import os
import requests
import json
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
        route_sample_points = ['x']

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

        return {
            'driving': {
                'length_miles': 0,
                'duration_minutes': 0,
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
    def get_driving_route(self, origin, destination):
        pass


class GoogleHotelsGateway:
    def get_hotel_prices_around_location(self, coords):
        return [1]


class EIAGateway:
    eia_api_key = os.environ['EIA_API_KEY']
    url = f"http://api.eia.gov/category/?api_key={eia_api_key}&category_id=711295"

    ca_thing = f"http://api.eia.gov/series/?api_key={eia_api_key}&series_id=PET.EMM_EPM0R_PTE_SCA_DPG.W"
    east_coast_thing = "http://api.eia.gov/series/?api_key=YOUR_API_KEY_HERE&series_id=PET.EMM_EPM0_PTE_R10_DPG.W"

    # TODO should introduce another layer to convert coords to region i think
    def get_gas_prices_around_location(self, coords):
        resp = requests.get(EIAGateway.ca_thing)
        gas_price = json.loads(resp.content)['series'][0]['data'][0][1]
        return [gas_price]


class SkyScannerGateway:
    def get_flight_info(self, origin, destination):
        pass
