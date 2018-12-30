import csv
import os
import time
import requests
import numpy as np
from decimal import Decimal
from datetime import datetime, timedelta
from errors import ApiError, UpdateExchangeRateException, \
    NoNewExchangeRatesException, ExchangeRatesAlreadyUpToDateException

class ExchangeRates(object):
    """
      This class ingests exchange_rates.csv -- a bare history of [BTC, ETH, USD] exchange rates from 2013 to today.
      The parse_file() function return a parsed dictionary of exchange-rate data.

      The update_exchange_rates() function identifies the most recent date in exchange_rates.csv, and appends recent
      exchange rate data. This process uses the Coinbase Pro free API, which is rate-limited to 3 calls per second.
    """
    def __init__(self):
        self.path = os.path.join('data', 'exchange_rates.csv')
        self.api = 'https://api.gdax.com/products/'
        self.base_currencies = ['BTC', 'ETH']

    def parse_file(self, filename):
        with open(filename, 'r') as f:
            return self.parse(f)

    def parse(self, f_obj):
        reader = csv.DictReader(f_obj)
        rates = {}
        for row in reader:
            date = self.get_date(row)
            if date not in rates:
                rates[date] = {}
            rates[date][row['currency']] = Decimal(row['rate'])
            # TODO: Hacky addition of stablecoins. Pegged to $1 for now.
            if row['currency'] == 'BTC':
                for _ in ['USDT', 'USDC', 'DAI', 'TUSD', 'GUSD', 'PAX']:
                    rates[date][_] = Decimal(1)
        return rates

    def update_file(self, filename, rates):
        with open(filename, 'a') as f:
            f.write('\n')
            for key in rates:
                for currency in rates[key]:
                    f.write("{},{},{}\n".format(
                        key,
                        currency,
                        rates[key][currency],
                    ))

    def get_date(self, row):
        return datetime.strptime(row['date'], '%Y-%m-%d').date()

    def update_exchange_rates(self):
        rates = self.parse_file(self.path)
        try:
            max_date = self.get_max_date(rates)
            print "Updating exchange rates from %s" % max_date
            new_rates = self.get_exchange_rates(max_date)
        except UpdateExchangeRateException as exc:
            print exc
            return
        self.update_file(self.path, new_rates)

    def get_max_date(self, rates):
        max_date = max(rates.keys())
        if max_date + timedelta(1) >= datetime.today().date():
            raise UpdateExchangeRateException("Exchange Rates up to date")
        return max_date

    def get_exchange_rates(self, start_date):
        today = datetime.today().date()
        daterange = self.date_range(start_date, today)
        rates = {}
        for date in daterange:
            if date.weekday() == 0:
                print "Updating exchange rate data for week of %s..." % date
            rates[date] = {}
            for currency in self.base_currencies:
                url = self.get_url(currency, date)
                response = self.get_response(url)
                rate = response.json()
                rates[date][currency] = self.calculate_exchange_rate(rate)

        if not rates:
            raise NoNewExchangeRatesException("New Exchange Rates did not return any values")
        return rates

    def date_range(self, start, end):
        return [end - timedelta(_) for _ in range(1, (end-start).days)]

    def get_url(self, currency, date):
        endpoint = '{}-USD/'.format(currency)
        params = 'candles?start={start}&end={end}&granularity=3600'.format(
            start=date - timedelta(days=1),
            end=date,
        )
        return self.api + endpoint + params

    def calculate_exchange_rate(self, rate):
        candle_rates = []
        for candle in rate:
            candle_rates.append((candle[3] + candle[4]) / 2.0)
        return round((1 / np.average(candle_rates)), 15)

    def get_response(self, url):
        count = 0
        while True:
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    break
                else:
                    raise
            except:
                if count > 5:
                    raise ApiError("Too many API failures %s" % url)
                time.sleep(10 * count)
                count += 1
                continue
        return response
