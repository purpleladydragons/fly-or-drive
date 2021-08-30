import json
import os

import requests

class SkyScannerGateway:
    def __init__(self):
        self.apikey = os.environ['SKYSCANNER_API_KEY']
        self.headers = {
            'x-rapidapi-key': self.apikey,
            'x-rapidapi-host': "skyscanner-skyscanner-flight-search-v1.p.rapidapi.com"
        }

    def autosuggest_place(self, place):
        url = "https://skyscanner-skyscanner-flight-search-v1.p.rapidapi.com/apiservices/autosuggest/v1.0/US/USD/en-US/"
        querystring = {"query": place}
        response = requests.request("GET", url, headers=self.headers, params=querystring)

        data = json.loads(response.content)
        return data['Places'][0]['PlaceId']

    def get_flight_info(self, origin, destination):
        origin = self.autosuggest_place(origin)
        destination = self.autosuggest_place(destination)
        url = f"https://skyscanner-skyscanner-flight-search-v1.p.rapidapi.com/apiservices/browsequotes/v1.0/US/USD/en-us/{origin}/{destination}/2021-09/2021-09"
        response = requests.request("GET", url, headers=self.headers)
        return json.loads(response.content)