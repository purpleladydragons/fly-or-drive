from math import radians, cos, sin, asin, sqrt

from dataclasses import dataclass

from ..gateways.google_distance_matrix_gateway import GoogleDistanceMatrixGateway
from ..gateways.eia_gateway import EIAGateway
from ..gateways.skyscanner_gateway import SkyScannerGateway

@dataclass
class DrivingInfo:
    distance_miles: float
    driving_duration_seconds: int
    hotel_total_price: float
    gas_total_price: float

@dataclass
class FlyingInfo:
    flight_duration_minutes: float
    estimated_price: float

class TripCalculatorService:
    def __init__(self):
        self.gdm = GoogleDistanceMatrixGateway()
        self.eia = EIAGateway()
        self.sky = SkyScannerGateway()

    # TODO handle latlng input as well
    def haversine(self, origin, destination):
        """
        Calculate the great circle distance in kilometers between two points
        on the earth (specified in decimal degrees)
        """

        lat1, lng1 = self.gdm.get_lat_lng(origin)
        lat2, lng2 = self.gdm.get_lat_lng(destination)

        # convert decimal degrees to radians
        lng1, lat1, lng2, lat2 = map(radians, [lng1, lat1, lng2, lat2])

        # haversine formula
        dlng = lng2 - lng1
        dlat = lat2 - lat1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlng / 2) ** 2
        c = 2 * asin(sqrt(a))
        r = 6371  # Radius of earth in kilometers. Use 3956 for miles. Determines return value units.
        return c * r

    def __calculate_drive(self, origin, destination, max_one_day_driving_minutes, car_mpg):
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

    # TODO add another method that does flying and then driving from airports

    def __calculate_flight(self, origin, destination):
        flight_distance_miles = self.haversine(origin, destination) * 0.60
        # +30 minutes for gate waiting
        flight_duration_minutes = (flight_distance_miles / 550) * 60 + 30

        flight_info = self.sky.get_flight_info(origin, destination)
        quotes = flight_info['Quotes']
        avg_price = sum([q['MinPrice'] for q in quotes]) / len(quotes)

        return FlyingInfo(flight_duration_minutes, avg_price)

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
        origin_airport = self.__find_nearest_airport(origin_latlng)

        destination_latlng = self.gdm.get_lat_lng(destination)
        destination_airport = self.__find_nearest_airport(destination_latlng)

        # TODO make sure types are all right
        drive_to_airport = self.__calculate_drive(origin, origin_airport)
        flight_info = self.__calculate_flight(origin_airport, destination_airport)
        drive_from_airport = self.__calculate_drive(destination_airport, destination)

        # TODO combine the info into some coherent package

    def __find_nearest_airport(self, coords):
        # TODO look up airports from db
        airports = []

        dists = [(airport, self.haversine(coords, airport)) for airport in airports]
        nearest_airport = sorted(dists, key=lambda d: d[1])[:3]
        return nearest_airport

    # TODO add a decorate to specify how it should be serialized to json compatible view
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
        flying_info = self.__calculate_flight(origin, destination)

        # TODO remember about return leg of driving too

        print("Finished calculations")

        return {
            'driving': {
                'length_miles': driving_info.distance_miles,
                'duration_minutes': driving_info.driving_duration_seconds / 60,
                'hotel_price_sum': driving_info.hotel_total_price,
                'gas_price_sum': driving_info.gas_total_price,
                'total_price': driving_info.hotel_total_price + driving_info.gas_total_price,
            },
            # TODO just nest a "driving" section under it
            'flying': {
                'duration_minutes': flying_info.flight_duration_minutes,
                'flight_price': flying_info.estimated_price,
            }
        }