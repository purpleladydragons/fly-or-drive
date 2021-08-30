import json
import os

import requests


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
