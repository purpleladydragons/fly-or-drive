import os
import requests
import json
import googlemaps
from datetime import datetime
# TODO import gateway

class TripCalculatorService:
    # TODO add a decorate to specify how it should be serialized to json compatible view
    @staticmethod
    def calculate_trip(origin, destination):
        """
        Given origin and destination, determine relevant trip information,
        e.g time to drive, cost of driving + hotels, flight length and price

        :param origin: name of origin city
        :param destination: name of destination city
        :return: TripInfoView
        """

        # TODO probably accept more optional? params, like max driving in a day etc

        gdm = GoogleDistanceMatrixGateway()
        gh = GoogleHotelsGateway()
        eia = EIAGateway()
        sky = SkyScannerGateway()

        driving_route = gdm.get_driving_route(origin, destination)

        # TODO sample points along driving route to use for hotels and gas
        route_sample_points = [(34, -122), (45, -105)]

        hotel_total_price = 0
        gas_total_price = 0

        # TODO it's not this simple for calculating price of trip: you stop at hotel once a day, gas could be 0-2 times a day etc
        for pt in route_sample_points:
            local_hotel_prices = gh.get_hotel_prices_around_location(pt)
            hotel_total_price += sum(local_hotel_prices) / len(local_hotel_prices)

            local_gas_prices = eia.get_gas_prices_around_location(pt)
            gas_total_price += sum(local_gas_prices) / len(local_gas_prices)

        # TODO use flight info
        flight_info = sky.get_flight_info(origin, destination)

        distance_miles = (driving_route[0] / 1000) * 0.62
        return {
            'driving': {
                'length_miles': distance_miles,
                'duration_minutes': driving_route[1],
                'hotel_price_sum': hotel_total_price,
                'gas_price_sum': gas_total_price,
                'total_price': hotel_total_price + gas_total_price,
            },
            'flying': {
                'duration_minutes': 0,
                'flight_price': 0
            }
        }


class GoogleDistanceMatrixGateway:
    def __init__(self):
        googlemaps_api_key = os.environ['GOOGLE_DISTANCE_MATRIX_API_KEY']
        self.gmaps = googlemaps.Client(key=googlemaps_api_key)

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
        lat,lng = coords
        # hack. assume california bounded simply by flat rect top, angled side, and rect bottom
        if ((lng < -119.9 and lat < 42) or
            (35 < lat < 39 and lng < -1.5 * lat - 123/2) or
            (lat < 35 and lng < -114.5)):
            to_check = EIAGateway.ca_thing
        else:
            to_check = EIAGateway.us_thing

        resp = requests.get(to_check)
        gas_price = json.loads(resp.content)['series'][0]['data'][0][1]
        return [gas_price]


class SkyScannerGateway:
    def get_flight_info(self, origin, destination):
        pass
