import requests
import time
from decimal import Decimal


CMC_API_KEY = None

class ExchangeRates():
    def __init__(self):
        self.limit = 200
        self.cmc_url = 'https://pro-api.coinmarketcap.com/'
        self.cmc_endpoint = 'v1/cryptocurrency/listings/latest?sort=market_cap&start=1&limit={}'.format(self.limit)
        self.cmc_header = {'X-CMC_PRO_API_KEY': CMC_API_KEY}

    def run(self):
        rates = self.get_cmc_rates()
        rates = self.add_manual_rates(rates)
        return rates

    def decode(self, arg):
        if isinstance(arg, unicode):
            return arg.encode()
        return arg

    def get_cmc_rates(self):
        url = self.cmc_url + self.cmc_endpoint
        response = requests.get(url, headers=self.cmc_header)
        r = response.json()
        self.check_api_status(r)

        rates = {}
        for _ in r['data']:
            rates['{}_USD'.format(_['symbol'])] = Decimal(_['quote']['USD']['price'])
        rates = {self.decode(k): v for k,v in rates.items()}
        return rates

    def add_manual_rates(self, rates):
        rates['USD_USD'] = Decimal(1.0)
        rates['IOTA_USD'] = rates['MIOTA_USD']
        rates['XRB_USD'] = rates['NANO_USD']
        return rates

    def check_api_status(self, response):
        if str(response['status']['error_message']) == "API key missing.":
                raise Exception("API Key Missing. Get free API key from https://coinmarketcap.com/api/ and enter on current_exchange_rates.py")
