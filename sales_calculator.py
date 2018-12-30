import pandas as pd
import current_exchange_rates
from decimal import Decimal


class SalesCalculator():
    # The Sales Calculator simulates selling yourcrypto assets, attempting to increase osses in order
    # to decrease the tax burden for a given year. This calculator assumes LIFO to calculate PNL
    # It provides a comprehensive report to maximize:
    #   (1) Total $ amount sold while not increasing the current PNL
    #   (2) Total $ amount sold that would minimize total PNL
    def __init__(self, year):
        self.year = year

    def sales_data(self, pnl, remaining_funds, pnl_threshold):
        # pnl_threshold:     With LIFO,  when simulating selling crypto assets the first few sales could
        #                    increase PNL before it finds some assets that would decrease PNL. This
        #                    threshold allows you increase PNL up to <X> before stopping the process.
        rates = self.current_exchange_rates()
        sales = pd.DataFrame()
        currencies = pnl.currency.unique()
        for _ in currencies:
            rf_copy = self.get_currency_rf_copy(remaining_funds, _)
            price = rates['{}_USD'.format(_)]

            rolling_pnl = 0
            rolling_sales = 0
            rolling_amount = 0
            while True:
                for row in rf_copy.iterrows():
                    basis = Decimal(row[1].basis)
                    amount = Decimal(row[1].amount)
                    _pnl = amount * (price - basis)
                    rolling_sales += (amount * price)
                    rolling_amount += amount

                    rolling_pnl += _pnl
                    if rolling_pnl >= pnl_threshold:
                        break

                    sales = sales.append({
                        'currency': _,
                        'amount': amount,
                        'rolling_amount': rolling_amount,
                        'sales': amount * price,
                        'rolling_sales': rolling_sales,
                        'pnl': _pnl,
                        'rolling_pnl': rolling_pnl,
                    }, ignore_index=True)
                break

        return sales

    def get_currency_rf_copy(self, remaining_funds, currency):
        return remaining_funds[(remaining_funds['currency'] == currency)].sort_values(
                by=['created_at'], ascending=False
            ).copy()

    def current_exchange_rates(self):
        return current_exchange_rates.ExchangeRates().run()

    def find_min_max_pnl(self, sales):
        print "Max sales while not impacting current capital gains (PNL):"
        summary = {}
        for _ in sales.currency.unique():
            copy = sales[sales['currency'] == _].copy()
            summary[_] = {
                'max_sales_usd': round(copy.sales.sum()),
                'max_sales_amt': round(copy.amount.sum(), 2),
                'max_sales_pnl': round(copy.pnl.sum()),
            }

            print "{:<6}".format(_), "Total Sales: ", "{:<10}".format(summary[_]['max_sales_usd']), "Amount to sell: ", \
                "{:<14}".format(summary[_]['max_sales_amt']), "Impact to PNL: ", "{:<10}".format(summary[_]['max_sales_pnl'])

        summary['total_max'] = {
            'max_sales_usd': round(sales.sales.sum()),
            'max_sales_pnl': round(sales.pnl.sum()),
        }
        print "Max Sales: ", "{:<10}".format(summary['total_max']['max_sales_usd']), \
            "Max PNL loss: ", "{:<10}".format(summary['total_max']['max_sales_pnl']), "\n"

        print "\nMax sales in order to minimize current capital gains (PNL)"
        r_s = 0
        r_p = 0
        for _ in sales.currency.unique():
            copy = sales[sales['currency'] == _].copy()
            min_pnl_index = copy.rolling_pnl.idxmin()
            rolling_sales = round(copy.loc[min_pnl_index].rolling_sales, 0)
            rolling_amount = round(copy.loc[min_pnl_index].rolling_amount, 2)
            rolling_pnl = round(copy.loc[min_pnl_index].rolling_pnl, 0)
            r_s += rolling_sales
            r_p += rolling_pnl

            summary[_]['min_sales_usd'] = rolling_sales
            summary[_]['min_sales_amt'] = rolling_amount
            summary[_]['min_sales_pnl'] = rolling_pnl

            print "{:<6}".format(_), "Total Sales: ", "{:<10}".format(rolling_sales), "Amount to sell: ", \
                "{:<14}".format(rolling_amount), "Impact to PNL: ", "{:<10}".format(rolling_pnl)

        summary['total_min'] = {
            'min_sales_usd': r_s,
            'min_sales_pnl': r_p,
        }
        print "Max Sales: ", "{:<10}".format(r_s), "Max PNL loss: ", "{:<10}".format(r_p)

        return summary

    def final_pnl_and_sales(self, summary, coins_to_sell, total_pnl):
        # Pull in a dict of coins that you want to sell, the total PNL calculations from taxes.py,
        # and the summary sales data from min_max_pnl
        sales = 0
        pnl = total_pnl[total_pnl['year'] == 2018].pnl.sum()
        print "Current capital gains (PNL): ", pnl, "\n"

        print "Selling assets in order to minimize current capital gains (PNL):"
        for _ in coins_to_sell:
            sales += summary[_]['min_sales_usd']
            pnl += summary[_]['min_sales_pnl']
            print "{:<10}".format(_), "${:<10} in sales".format(summary[_]['min_sales_usd'])

        print "Total sold (USD): {:<10} Final PNL: ".format(sales), "{:<}\n".format(pnl)

        print "Selling assets in order to maximize sales while not impacting current capital gains (PNL)"
        sales = 0
        pnl = total_pnl[total_pnl['year'] == 2018].pnl.sum()
        for _ in coins_to_sell:
            sales += summary[_]['max_sales_usd']
            pnl += summary[_]['max_sales_pnl']
            print "{:<10}".format(_), "${:<10} in sales".format(summary[_]['max_sales_usd'])

        print "Total sold (USD): {:<10} Final PNL: ".format(sales), "{:<}".format(pnl)
