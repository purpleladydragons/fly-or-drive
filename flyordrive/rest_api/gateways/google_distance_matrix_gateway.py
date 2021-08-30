from datetime import datetime
import os

import googlemaps


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

    def find_airport(self, airport_code):
        return self.gmaps.places(airport_code, type='airport')