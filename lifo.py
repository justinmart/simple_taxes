import pandas as pd
import numpy as np
from decimal import Decimal
from datetime import datetime, timedelta


class LIFO(object):
    """
      Calculates profit and loss for each currency traded based on Last-In-First-Out (LIFO).
      The run() function cycles through each currency and calculating LIFO for each trade.

      The aggregate_pnl() function takes a dataframe of individual
    """
    def __init__(self):
        pass

    def run(self, trades):
        print "Generating LIFO profit and loss"
        pnl = pd.DataFrame()
        remaining_funds = pd.DataFrame()
        for currency in trades.currency.unique():
            print "Calculating LIFO for {}".format(currency)
            curr_trades = self.generate_currency_trades(trades, currency)
            curr_pnl, curr_rf = self.calc_pnl(curr_trades)
            pnl = self.append_currency_pnl_to_total_pnl(pnl, curr_pnl, currency)
            remaining_funds = self.append_curr_rem_funds_to_rem_funds(remaining_funds, curr_rf, currency)
        pnl = self.clean_data(pnl)
        return pnl, remaining_funds

    def append_curr_rem_funds_to_rem_funds(self, remaining_funds, curr_rf, currency):
        if not curr_rf:
            return remaining_funds
        for _ in curr_rf:
            remaining_funds = remaining_funds.append(_, ignore_index=True)
        return remaining_funds

    def generate_currency_trades(self, df, currency):
        native = df[df['currency'] == currency][[
            'created_at', 'platform', 'currency', 'currency_pair', 'type', 'amount', 'basis']].copy()

        fills = df[df['fill_currency'] == currency][[
            'created_at', 'currency', 'currency_pair', 'fill_type', 'fill_amount', 'fill_basis']].copy()
        fills['currency'] = currency
        fills.rename(columns={'fill_amount': 'amount', 'fill_basis': 'basis', 'fill_type': 'type'}, inplace=True)

        trades = native.append(fills)
        trades.reset_index(inplace=True)
        del trades['index']
        trades.sort_values(by=['created_at'], ascending=True, inplace=True)
        return trades

    def append_currency_pnl_to_total_pnl(self, pnl, curr_pnl, currency):
        if curr_pnl.empty:
            return pnl
        curr_pnl['year'] = curr_pnl['date'].apply(lambda _: _.year)
        curr_pnl['currency'] = currency
        return pnl.append(curr_pnl)

    def aggregate_pnl(self, pnl):
        print "Calculating aggregate LIFO profit and loss"
        agg_pnl = {}
        for _ in pnl.year.unique():
            agg_pnl[_] = {}

        grouped_pnl = pnl.groupby(['year', 'long_term']).pnl.sum().transpose()
        for _ in grouped_pnl.iteritems():
            if _[0][1]:
                agg_pnl[_[0][0]]['long_term'] = round(_[1], 2)
            else:
                agg_pnl[_[0][0]]['short_term'] = round(_[1], 2)

        aggregate_pnl = pd.DataFrame.from_dict(agg_pnl).transpose()
        return aggregate_pnl

    def calc_pnl(self, df, log=False):
        """
          Takes a pandas dataframe of buys and sells and calculates the profit and loss
          from each trade based on LIFO.

          Methodology: Populate a queue with buys and sells as they happen.
          Buys are added to the queue, sells are deducted from the most recent buys
          until the sell is exhausted. Any leftover amount is re-added to the queue.
        """
        pnl = pd.DataFrame()
        queue = []
        for _ in df.iterrows():
            row = _[1]
            if row.type == 'buy':
                queue.append(row)
                pnl = self.add_buy_to_pnl(pnl, row)
                self.print_statement(log, queue, row, sell_amount=None, buy_amount=row['amount'])
            elif row.type == 'sell':
                sell_basis = row['basis']
                sell_amount = row['amount']
                self.print_statement(log, queue, row, sell_amount=sell_amount, buy_amount=None)
                self.validate_sell(sell_amount, queue, row, df, log)

                while True:
                    buy = queue.pop()
                    bd = self.buy_details(buy)

                    amount = sell_amount if ((bd['buy_amount'] - sell_amount) >= 0) else bd['buy_amount']
                    pnl = self.add_sell_to_pnl(pnl, row, bd, amount, sell_basis)

                    leftover = bd['buy_amount'] - sell_amount
                    if leftover > 0:
                        self.add_leftover_sell_to_queue(queue, bd, leftover)
                        break
                    elif leftover == 0:
                        break
                    elif leftover < 0:
                        sell_amount = abs(leftover)
                        pass

        remaining_funds = queue
        return pnl, remaining_funds

    def clean_data(self, pnl):
        pnl['long_term'] = pnl['long_term'].apply(lambda _: bool(_) if not np.isnan(_) else np.NaN)
        for _ in ['pnl', 'buy_basis', 'sell_basis']:
            pnl[_] = pnl[_].apply(lambda _: round(_, 2))
        return pnl

    def buy_details(self, buy):
        return {
            'buy_basis': buy['basis'],
            'buy_amount': buy['amount'],
            'buy_date': buy['created_at'],
            'buy_platform': buy['platform'],
            'buy_currency': buy['currency'],
            'buy_currency_pair': buy['currency_pair'],
        }

    def add_buy_to_pnl(self, df, row):
        return df.append(
            {
                'date': row['created_at'],
                'currency': row['currency'],
                'currency_pair': row['currency_pair'],
                'buy_date': row['created_at'],
                'sell_date': np.NaN,
                'time_diff': np.NaN,
                'long_term': np.NaN,
                'buy_platform': row['platform'],
                'sell_platform': np.NaN,
                'amount': row['amount'],
                'type': 'buy',
                'buy_basis': row['basis'],
                'sell_basis': np.NaN,
                'pnl': np.NaN,
            }, ignore_index=True
        )

    def add_sell_to_pnl(self, df, row, bd, amount, sell_basis):
        return df.append(
            {
                'date': row['created_at'],
                'currency': row['currency'],
                'currency_pair': row['currency_pair'],
                'buy_date': bd['buy_date'],
                'sell_date': row['created_at'],
                'time_diff': row['created_at'] - bd['buy_date'],
                'long_term': bool((row['created_at'] - bd['buy_date']) >= timedelta(365)),
                'buy_platform': bd['buy_platform'],
                'sell_platform': row['platform'],
                'amount': amount,
                'type': 'sell',
                'buy_basis': bd['buy_basis'],
                'sell_basis': sell_basis,
                'pnl': amount * (sell_basis - bd['buy_basis']),
            }, ignore_index=True
        )


    def add_leftover_sell_to_queue(self, queue, bd, leftover):
        queue.append(pd.Series(
            {
                'created_at': bd['buy_date'],
                'type': 'buy',
                'amount': leftover,
                'basis': bd['buy_basis'],
                'platform': bd['buy_platform'],
                'currency': bd['buy_currency'],
                'currency_pair': bd['buy_currency_pair'],
            }
        ))

    def validate_sell(self, sell_amount, queue, row, df, log):
        try:
            assert sell_amount <= sum([_.amount for _ in queue])
        except AssertionError as exc:
            self.assertion_error_print_statement(sell_amount, queue, row, df, log)

    def assertion_error_print_statement(self, sell_amount, queue, row, df, log):
        """
          If a list of trades ends up attempting to sell more than they have purchased (based on
          LIFO), this function is called to explicitly explain what happened.

          It is expected that people forget about some trades they have made, or some other ways they have
          obtained crypto. These errors can be hard to debug, so this function runs through the whole
          LIFO calculation, calling out the available balance after each trade. This will help the user
          understand what happened and remember which trades are missing.

          Params:
          log            : A flag toggling print statements. When true, the log of each trade will be printed.
                           This is only toggled after this function is called (and an AssertionError has been hit)
          sell_amount    : The specific amount being sold
          row            : specific trade data which caused the AssertionError
          df             : A pandas dataframe of all trades of a specific cryptocurrency
          queue          : The queue which is populated as part of the LIFO profit and loss calculation
        """
        if log:
            raise AssertionError("You are trying to sell more than you have purchased. See above for details")
        balance = sum([_.amount for _ in queue])
        print "You are trying to sell more %s than you have purchased" % row['currency']
        print "Error occured when trying to sell {s} {c}, when you have {a} available to sell".format(
          s=round(sell_amount, 2),
          c=row['currency'],
          a=round(balance, 2) if balance else 0,
        )
        print "You must be missing some trade or gift that resulted in more %s\n" % row['currency']
        print "This is the trade that caused the error: \n%s\n" % row
        print "Re-creating the history of buys and sells..."
        self.calc_pnl(df, log=True)

    def print_statement(self, log, queue, row, sell_amount, buy_amount):
        if not log:
            return
        balance = sum([_.amount for _ in queue])
        print "Date {d} selling: {s:<10} purchasing: {p:<10} balance: {b:<10} platform: {e}".format(
            d=row['created_at'],
            s=round(sell_amount, 2) if sell_amount else '',
            p=round(buy_amount, 2) if buy_amount else '',
            b=round(balance, 2) if balance else '',
            e=row['platform']
        )
