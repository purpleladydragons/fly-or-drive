import requests
import json

class CliClient:
    def prompt_user(self):
        origin = input("Input origin: ")
        destination = input("Input destination: ")
        resp = self.make_request(origin, destination)
        data = json.loads(resp.content)
        self.pretty_print_data(data)

    def pretty_print_data(self, data):
        print("###### Driving ######")
        driving_data = data['driving']
        driving_time = driving_data['duration_minutes']
        driving_hours = driving_time // 60
        driving_minutes = driving_time % 60
        driving_price = driving_data['total_price']
        print(f'{int(driving_hours)} hr {int(driving_minutes)} min')
        print(f'${round(driving_price, 2)}')
        print("###### Flying ######")
        flying_data = data['flying']
        flying_time = flying_data['duration_minutes']
        flying_hours = flying_time // 60
        flying_minutes = flying_time % 60
        print(f'{int(flying_hours)} hr {int(flying_minutes)} min')

    def make_request(self, origin, destination):
        base_url = 'http://localhost:8000'
        full_url = f'{base_url}/api/calculate'
        data = {'origin': origin, 'destination': destination}
        return requests.post(full_url, data=json.dumps(data), headers={'Content-type': 'application/json'})


if __name__ == "__main__":
    client = CliClient()
    client.prompt_user()