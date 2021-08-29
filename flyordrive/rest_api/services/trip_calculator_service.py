import os
import requests
import json
import googlemaps
from datetime import datetime
from math import radians, cos, sin, asin, sqrt


# TODO import gateway

class TripCalculatorService:
    def __init__(self):
        self.gdm = GoogleDistanceMatrixGateway()
        self.gh = GoogleHotelsGateway()
        self.eia = EIAGateway()
        self.sky = SkyScannerGateway()

    # TODO also note that this fails badly if flight requires layover
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

    # TODO add a decorate to specify how it should be serialized to json compatible view
    def calculate_trip(self, origin, destination, max_one_day_driving_minutes=8 * 60, car_mpg=20):
        """
        Given origin and destination, determine relevant trip information,
        e.g time to drive, cost of driving + hotels, flight length and price

        :param origin: name of origin city
        :param destination: name of destination city
        :return: TripInfoView
        """

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

        flight_distance_miles = self.haversine(origin, destination) * 0.60
        # +30 minutes for gate waiting
        flight_duration_minutes = (flight_distance_miles / 550) * 60 + 30

        # TODO use flight info
        flight_info = self.sky.get_flight_info(origin, destination)

        # TODO remember about return leg of driving too

        return {
            'driving': {
                'length_miles': distance_miles,
                'duration_minutes': driving_duration_seconds / 60,
                'hotel_price_sum': hotel_total_price,
                'gas_price_sum': gas_total_price,
                'total_price': hotel_total_price + gas_total_price,
            },
            'flying': {
                'duration_minutes': flight_duration_minutes,
                'flight_price': 0
            }
        }


class GoogleDistanceMatrixGateway:
    def __init__(self):
        googlemaps_api_key = os.environ['GOOGLE_API_KEY']
        self.gmaps = googlemaps.Client(key=googlemaps_api_key)

    def get_lat_lng(self, place):
        latlng = self.gmaps.geocode(place)[0]['geometry']['location']
        lat = latlng['lat']
        lng = latlng['lng']
        return lat, lng

    def get_driving_route(self, origin, destination):
        now = datetime.now()
        route_info = self.gmaps.distance_matrix([origin], [destination],
                                                mode='driving', departure_time=now,
                                                language='en-US',
                                                traffic_model='optimistic')
        relevant_part = route_info['rows'][0]['elements'][0]
        distance_meters = relevant_part['distance']['value']
        duration_seconds = relevant_part['duration']['value']

        return (distance_meters, duration_seconds)


class GoogleHotelsGateway:
    def get_hotel_prices_around_location(self, coords):
        return [1]


class EIAGateway:
    eia_api_key = os.environ['EIA_API_KEY']
    url = f"http://api.eia.gov/category/?api_key={eia_api_key}&category_id=711295"

    ca_thing = f"http://api.eia.gov/series/?api_key={eia_api_key}&series_id=PET.EMM_EPM0R_PTE_SCA_DPG.W"
    us_thing = f"http://api.eia.gov/series/?api_key={eia_api_key}&series_id=PET.EMM_EPM0_PTE_NUS_DPG.W"

    def get_gas_prices_around_location(self, coords):
        lat, lng = coords
        # hack. assume california bounded simply by flat rect top, angled side, and rect bottom
        if ((lng < -119.9 and lat < 42) or
                (35 < lat < 39 and lng < -1.5 * lat - 123 / 2) or
                (lat < 35 and lng < -114.5)):
            to_check = EIAGateway.ca_thing
        else:
            to_check = EIAGateway.us_thing

        resp = requests.get(to_check)
        gas_price = json.loads(resp.content)['series'][0]['data'][0][1]
        return [gas_price]


class SkyScannerGateway:
    def __init__(self):
        self.headers = {
            'x-rapidapi-key': os.environ['SKYSCANNER_API_KEY'],
            'x-rapidapi-host': "skyscanner-skyscanner-flight-search-v1.p.rapidapi.com"
        }

    def get_flight_info(self, origin, destination):
        url = "https://skyscanner-skyscanner-flight-search-v1.p.rapidapi.com/apiservices/browseroutes/v1.0/US/USD/en-us/Los%20Angeles,%20CA/San%20Francisco,%20CA/2021-09/2021-09-10"
        response = requests.request("GET", url, headers=self.headers)
        return response.content
