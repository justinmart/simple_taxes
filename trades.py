import pandas as pd
import glob
import os
from exchange_parsers.coinbase import CoinbaseParser
from exchange_parsers.coinbase_pro import CoinbaseProParser
from exchange_parsers.binance_csv import BinanceCsvParser
from exchange_parsers.binance_xlsx import BinanceXlsxParser
from exchange_parsers.bitfinex import BitfinexParser
from exchange_parsers.bittrex import BittrexParser
from exchange_parsers.poloniex import PoloniexParser
from exchange_parsers.kraken import KrakenParser
from exchange_parsers.gemini import GeminiParser
from exchange_parsers.circle import CircleParser
from exchange_parsers.manual_trades import ManualTradesParser

parsers = {
    'binance_csv': BinanceCsvParser,
    'binance_xlsx': BinanceXlsxParser,
    'bitfinex': BitfinexParser,
    'bittrex': BittrexParser,
    'circle': CircleParser,
    'coinbase': CoinbaseParser,
    'coinbase_pro': CoinbaseProParser,
    'gemini': GeminiParser,
    'kraken': KrakenParser,
    'poloniex': PoloniexParser,
    'manual_trades': ManualTradesParser,
}


class Trades():
    """
      This class obtains all trades from each exchange.

      The run() function obtains all files in each data/<exchange>/ folder, and parses data in
      each one according to that exchange's unique parser (Based on the "parsers" dictionary).
      Each exchange's data is coalesced into a single dataframe, along with any errors captured
      in the process.
    """
    def __init__(self, *args, **kwargs):
        pass

    def run(self):
        trades = []
        errors = []
        for exchange in parsers.keys():
            print "Processing trades from {}".format(exchange)
            for _file in glob.glob('./data/{}/*'.format(exchange)):
                filename = self.process_filename(_file)
                if filename[0] == '.':
                    print "Skipping folder in {}".format(exchange)
                    continue
                else:
                    trade, error = parsers[exchange]().run(os.path.join('data', exchange, filename))
                trades.extend(trade)
                errors.extend(error)

        df = self.dict_to_df(trades)
        df = self.process_df(df)
        return df, errors

    def process_filename(self, _file):
        body = _file.split(".")[-2].split("/")[-1]
        filetype = _file.split(".")[-1]
        return body + '.' + filetype

    def dict_to_df(self, _dict):
        print "Finalizing trades"
        df = pd.DataFrame()
        for trade in _dict:
            df = df.append(trade, ignore_index=True)
        return df

    def process_df(self, df):
        df.sort_values(by=['created_at'], ascending=True, inplace=True)
        df.reset_index(inplace=True)
        del df['index']
        del df['_extras']
        return df
