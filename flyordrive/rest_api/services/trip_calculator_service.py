import json
from math import radians, cos, sin, asin, sqrt
import os.path
import sqlite3

import dataclasses
from dataclasses import dataclass

from ..gateways.google_distance_matrix_gateway import GoogleDistanceMatrixGateway
from ..gateways.eia_gateway import EIAGateway
from ..gateways.skyscanner_gateway import SkyScannerGateway


@dataclass
class Airport:
    code: str
    lat: float
    lng: float

    def coords(self):
        return self.lat, self.lng


@dataclass
class DrivingInfo:
    distance_miles: float
    driving_duration_seconds: int  # TODO use minutes instead
    hotel_total_price: float
    gas_total_price: float

    def total_price(self):
        return self.hotel_total_price + self.gas_total_price

    def combine(self, other):
        return DrivingInfo(
            distance_miles=self.distance_miles + other.distance_miles,
            driving_duration_seconds=self.driving_duration_seconds + other.driving_duration_seconds,
            hotel_total_price=self.hotel_total_price + other.hotel_total_price,
            gas_total_price=self.gas_total_price + other.gas_total_price
        )

    def to_dict(self):
        return {**dataclasses.asdict(self), **{'total_price': self.total_price()}}

    def to_json(self):
        return json.dumps(self.to_dict())


@dataclass
class FlightInfo:
    flight_duration_minutes: float
    estimated_price: float

    def to_dict(self):
        return dataclasses.asdict(self)

    def to_json(self):
        return json.dumps(self.to_dict())


@dataclass
class FlyingTripInfo:
    flight_info: FlightInfo
    driving_info: DrivingInfo

    def compute_total(self):
        return {
            'total_price': self.flight_info.estimated_price + self.driving_info.total_price(),
            'total_duration_minutes': self.flight_info.flight_duration_minutes + self.driving_info.driving_duration_seconds / 60
        }

    def to_dict(self):
        return {
            'driving_info': self.driving_info.to_dict(),
            'flying_info': self.flight_info.to_dict(),
            'total_info': self.compute_total()
        }

    def to_json(self):
        return json.dumps(self.to_dict())


class TripCalculatorService:
    def __init__(self):
        self.gdm = GoogleDistanceMatrixGateway()
        self.eia = EIAGateway()
        self.sky = SkyScannerGateway()

    def haversine_coords(self, origin, destination):
        lat1, lng1 = origin
        lat2, lng2 = destination
        # convert decimal degrees to radians
        lng1, lat1, lng2, lat2 = map(radians, [lng1, lat1, lng2, lat2])

        # haversine formula
        dlng = lng2 - lng1
        dlat = lat2 - lat1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlng / 2) ** 2
        c = 2 * asin(sqrt(a))
        r = 6371  # Radius of earth in kilometers. Use 3956 for miles. Determines return value units.
        return c * r

    def haversine_places(self, origin, destination):
        """
        Calculate the great circle distance in kilometers between two points
        on the earth (specified in decimal degrees)
        """

        lat1, lng1 = self.gdm.get_lat_lng(origin)
        lat2, lng2 = self.gdm.get_lat_lng(destination)

        return self.haversine_coords((lat1, lng1), (lat2, lng2))

    def __calculate_drive(self, origin, destination, max_one_day_driving_minutes, car_mpg):
        print("Calculating drive", origin, destination)
        driving_route = self.gdm.get_driving_route(origin, destination)
        distance_miles = (driving_route[0] / 1000) * 0.62
        driving_duration_seconds = driving_route[1]

        # assume that you don't need a hotel on last day of trip, since you'll be at destination
        num_stops = max(0, driving_duration_seconds / (max_one_day_driving_minutes * 60) - 1)
        hotel_total_price = 150 * num_stops

        # assume you run car dry each time, then you're refilling gas_price * tank_size
        # and you do that when you run out, which is mpg * tank_size miles
        # but tank_size cancels out, so you don't need it
        num_gas_stops = distance_miles / car_mpg
        gas_total_price = num_gas_stops * 3.3

        return DrivingInfo(distance_miles, driving_duration_seconds, hotel_total_price, gas_total_price)

    def __calculate_flight(self, origin, destination):
        """

        :param origin: Airport
        :param destination: Airport
        :return:
        """
        flight_distance_miles = self.haversine_coords(origin.coords(), destination.coords()) * 0.60
        # +30 minutes for gate waiting
        flight_duration_minutes = (flight_distance_miles / 550) * 60 + 30

        flight_info = self.sky.get_flight_info(origin.code, destination.code)
        quotes = flight_info['Quotes']
        if len(quotes) == 0:
            avg_price = float('inf')
        else:
            avg_price = sum([q['MinPrice'] for q in quotes]) / len(quotes)

        return FlightInfo(flight_duration_minutes, avg_price)

    def __attempt_to_find_airports(self, place, airports, to_or_from):
        """
        Given a place near a list of candidate airports,
        try to find a route from the place to/from any of the airports

        :param place:
        :param airports:
        :param to_or_from: 'to' or 'from'
        :return:
        """
        airport_drive = None
        airport = None
        for port in airports:
            # TODO unfortunate workaround for now
            # we only have the AITA codes for airports which aren't reliable for geocoding
            # the website I used to get the AITA codes no longer works :) so it'll be manual to get the names
            # honestly, could just run this once for each airport and save it to db :shrug:
            port_place = self.gdm.reverse_geocode(port.coords())
            if to_or_from == 'to':
                origin = place
                destination = port_place
            else:
                origin = port_place
                destination = place
            try:
                airport_drive = self.__calculate_drive(origin,
                                                       destination,
                                                       max_one_day_driving_minutes=480,
                                                       car_mpg=20)
                airport = port
                break
            except:
                pass

        return airport, airport_drive

    def __calculate_flying_trip(self, origin, destination):
        """
        For cases when the origin or destination are a non-trivial distance from nearest airport

        Geocode the places and determine nearest airports. Calculate flight between them and then
        calculate driving routes to origin airport and from destination airport

        :param origin:
        :param destination:
        :return:
        """

        origin_latlng = self.gdm.get_lat_lng(origin)
        origin_airports = self.__find_nearest_airport(origin_latlng)

        destination_latlng = self.gdm.get_lat_lng(destination)
        destination_airports = self.__find_nearest_airport(destination_latlng)

        origin_airport, drive_to_airport = self.__attempt_to_find_airports(origin, origin_airports, 'to')
        destination_airport, drive_from_airport = self.__attempt_to_find_airports(destination, destination_airports, 'from')

        # TODO fail gracefully
        if drive_to_airport is None or drive_from_airport is None:
            return None

        flight_info = self.__calculate_flight(origin_airport, destination_airport)

        flying_trip_info = FlyingTripInfo(flight_info, drive_to_airport.combine(drive_from_airport))

        return flying_trip_info

    def __find_nearest_airport(self, coords):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(base_dir, '../../db.sqlite3')
        con = sqlite3.connect(db_path)
        cur = con.cursor()
        cur.execute('SELECT * FROM airport;')
        airport_rows = cur.fetchall()
        # the below is a bad hack to sort by airport popularity
        # the list we got the airports from was sorted by descending popularity
        # so we can first trim the list down to nearby airports
        # and then sort those remainders on the primary key as a proxy for most popular
        # (because the data was inserted in desc popular order)
        airports = [
            (row[0], Airport(row[1], float(row[2]), float(row[3])))
            for row in airport_rows
        ]

        dists = [(airport, self.haversine_coords(coords, airport[1].coords())) for airport in airports]
        nearest_airport = sorted(sorted(dists, key=lambda d: d[1])[:3], key=lambda d: d[0][0])
        return [port[0][1] for port in nearest_airport]

    def calculate_trip(self, origin, destination, max_one_day_driving_minutes=8 * 60, car_mpg=20):
        """
        Given origin and destination, determine relevant trip information,
        e.g time to drive, cost of driving + hotels, flight length and price

        :param origin: name of origin city
        :param destination: name of destination city
        :return: TripInfoView
        """

        print(f"calculating trip for {origin} to {destination}")

        driving_info = self.__calculate_drive(origin, destination, max_one_day_driving_minutes, car_mpg)
        flying_info = self.__calculate_flying_trip(origin, destination)

        # TODO remember about return leg of driving too

        print("Finished calculations")

        return {
            'driving': driving_info.to_dict(),
            'flying': flying_info.to_dict()
        }
