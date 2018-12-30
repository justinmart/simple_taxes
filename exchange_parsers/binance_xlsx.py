from decimal import Decimal
from datetime import datetime
from document_parser import DocumentParser
from errors import NotATradeException


class BinanceXlsxParser(DocumentParser):
    #  Binance's new trading history reports are in XLSX format and are really f***ed up.
    #  They report an aggregate row summing up a total order, but the individual trades
    #  are in rows underneath this aggregate row and only report partial info.
    #  This parser deals with all the funny business properly as of Dec 2018, but if Binance
    #  changes their structure again, this will have to change.
    def __init__(self, *args, **kwargs):
        self.current_trade_pair = None
        self.current_trade_type = None
        kwargs['exchange_name'] = 'binance'
        kwargs['header'] = {
            'created_at': None,
            'amount': None,
            'fill_amount': None,
            'currency_pair': None,
            'type': None,
            'price': None,
        }
        kwargs['header_rows'] = 0
        super(BinanceXlsxParser, self).__init__(*args, **kwargs)

    def process_row(self, row):
        #  Binance XLSX file contains "overview" rows that aggregate trade activity, and
        #  header rows under each aggregate row.
        is_trade = self.is_row_a_trade(row)
        if not is_trade:
            if row['_extras']['Pair'] == 'Date(UTC)':
                raise NotATradeException("Binance trade is an Intermediate Overview Row and not a specific trade", row)
            else:
                self.set_current_trade_pair_and_type(row)
                raise NotATradeException("Binance trade is an Overview Row and not a specific trade", row)

        self.check_current_trade_pair_and_type()
        row['created_at'] = self.process_date(row)
        row['currency_pair'] = self.process_currency_pair()
        row['type'] = self.current_trade_type.lower()
        row['price'] = self.process_price(row)
        row['amount'] = self.process_amount(row)
        row['fill_amount'] = self.process_fill_amount(row)
        return row

    def is_row_a_trade(self, row):
        # For rows that are actual trades, the date field will be under the 'Pair' key.
        # If we can actually process the 'Pair' field into a date, then it's a trade row
        try:
            date = self.process_date(row)
            return True
        except:
            return False

    def set_current_trade_pair_and_type(self, row):
        self.current_trade_pair = row['_extras']['Pair']
        self.current_trade_type = row['_extras']['Type']

    def check_current_trade_pair_and_type(self):
        if not self.current_trade_pair or not self.current_trade_type:
            raise Exception("Binance trade has no current trade pair -- check for changes to Binance's report")

    def process_currency_pair(self):
        quote_pairs = ['BTC', 'ETH', 'USDT']
        pair = self.current_trade_pair

        if pair[-3:] in quote_pairs:
            first = pair[:-3]
            last =  pair[-3:]
        elif pair[-4:] in quote_pairs:
            first = pair[:-4]
            last = pair[-4:]
        else:
            raise Exception('Binance quote pair is not one of {}'.format(quote_pairs))

        if first == 'BCC':
            first = 'BCH'
        return first + "-" + last

    def process_date(self, row):
        # Due to Binance's bullshit XLSX format, the date is under the 'Pair' key
        _date = row['_extras']['Pair']
        if isinstance(_date, str):
            return datetime.strptime(_date, '%Y-%m-%d %H:%M:%S')
        if isinstance(_date, date):
            return datetime(_date.year, _date.month, _date.day)
        else:
            raise Exception("Not a Date")

    def process_price(self, row):
        # Due to Binance's bullshit XLSX format, the price is under the 'Type' key
        return abs(Decimal(row['_extras']['Type']))

    def process_amount(self, row):
        # Due to Binance's bullshit XLSX format, the price is under the 'Order Price' key
        return abs(Decimal(row['_extras']['Order Price']))

    def process_fill_amount(self, row):
        # Due to Binance's bullshit XLSX format, the price is under the 'Order Amount' key
        return abs(Decimal(row['_extras']['Order Amount']))
