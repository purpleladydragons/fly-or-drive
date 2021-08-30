import os
import requests
import json
import googlemaps
from datetime import datetime
from math import radians, cos, sin, asin, sqrt

from ..gateways.google_distance_matrix_gateway import GoogleDistanceMatrixGateway
from ..gateways.eia_gateway import EIAGateway
from ..gateways.skyscanner_gateway import SkyScannerGateway

class TripCalculatorService:
    def __init__(self):
        self.gdm = GoogleDistanceMatrixGateway()
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
    # TODO break up into calculate driving and calculate flying
    # TODO flying needs to incorporate 1) rental cars 2) price/time to get from airport to wherever (uber or rental)
    def calculate_trip(self, origin, destination, max_one_day_driving_minutes=8 * 60, car_mpg=20):
        """
        Given origin and destination, determine relevant trip information,
        e.g time to drive, cost of driving + hotels, flight length and price

        :param origin: name of origin city
        :param destination: name of destination city
        :return: TripInfoView
        """

        print(f"calculating trip for {origin} to {destination}")

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

        # TODO do some smart processing: store skyscanner's list of airports with their coords
        # TODO then geocode the destination and use haversine to find closest 5? airports
        # b/c if you do closest you might get some random bs one or something idk
        # and then calc for each of them? (but this kils the API lol)
        # anyway, do that and you can add the time to drive from airport to place too!

        flight_distance_miles = self.haversine(origin, destination) * 0.60
        # +30 minutes for gate waiting
        flight_duration_minutes = (flight_distance_miles / 550) * 60 + 30

        # TODO figure out how to get duration of flight... (i guess just assume no layovers...)
        # TODO process flight info somehwere else
        flight_info = self.sky.get_flight_info(origin, destination)
        quotes = flight_info['Quotes']
        avg_price = sum([q['MinPrice'] for q in quotes]) / len(quotes)

        # TODO remember about return leg of driving too

        print("Finished calculations")

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
                'flight_price': avg_price
            }
        }