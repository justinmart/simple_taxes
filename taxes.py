import pandas as pd
import os
from trades import Trades
from lifo import LIFO
from rates import ExchangeRates
from errors import NotATradeException, TradeTooSmallException


class Taxes():
    """
      Main class to initialize and run tax reporting.

      The run() function updates the exchange_rates.csv file with current values,
      obtains and formats all trades from each exchange, calculates LIFO, and finalizes
      a formal tax reporting database (intended to be sent to the IRS or a tax accountant).
      This function returns:
      trades              : Detailed information regarding every trade across all exchanges and currencies
      errors              : Information on any errors or any trades left out of the calculations
      pnl                 : Profit-and-loss calculations for each trade, including long-term vs short-term gains
      total_pnl           : Aggregate information on profit and loss for each year, by short term vs long term
      tax_reporting_data  : A spreadsheet intended to be sent to the IRS or a tax accountant which
                          : details every trade and the profit-and-loss associated with each.
    """
    def __init__(self, *args, **kwargs):
        pass

    def run(self, trades=None, errors=None):
        rates = ExchangeRates().update_exchange_rates()
        print "running Trades"
        trades, errors = self.run_trades()
        self.print_trade_info(trades)
        self.print_errors(errors)
        pnl, total_pnl = self.run_lifo(trades)
        tax_reporting_data = self.tax_reporting_data(pnl)
        self.write_files(trades, errors, pnl, total_pnl, tax_reporting_data)
        return trades, errors, pnl, total_pnl, tax_reporting_data

    def run_trades(self):
        return Trades().run()

    def run_lifo(self, trades):
        pnl = LIFO().run(trades)
        total_pnl = LIFO().aggregate_pnl(pnl)
        return pnl, total_pnl

    def tax_reporting_data(self, pnl):
        columns = ['currency', 'amount', 'buy_date', 'sell_date', 'buy_basis', 'sell_basis', 'pnl', 'long_term']
        df = pnl[pnl['type'] == 'sell'][columns].copy()
        df.sort_values(by=['sell_date'], ascending=True, inplace=True)
        df.reset_index(inplace=True)
        del df['index']
        return df

    def write_files(self, trades, errors, pnl, total_pnl, tax_reporting_data):
        print "Writing final data to files in output/ folder"
        for _ in ['trades', 'pnl', 'total_pnl', 'tax_reporting_data']:
            eval("{f}.to_csv(os.path.join('output', '{f}.csv'))".format(f=_))

        with open(os.path.join('output', 'errors.csv'), 'w') as f:
            for _ in errors:
                f.write("%s\n" % _)

    def update_file(self, filename, tax_reporting_data):
        tax_reporting_data.to_csv(os.path.join('data', 'tax_reporting_data.csv'))

    def print_errors(self, errors):
        print "\nTrades not included:"
        for exception in [TradeTooSmallException, NotATradeException]:
            count = len([_ for _ in errors if isinstance(_, exception)])
            print "{e:<25} {c}".format(e=exception.__name__, c=count)
        print "\n"

    def print_trade_info(self, trades):
        print "\nTrade counts"
        print "{p:<25} {c:<10}".format(p='Total Trades', c=len(trades))
        for _ in trades.platform.unique():
            print "{:<25}".format(_), "{:<10}".format(len(trades[trades['platform'] == _]))
