from decimal import Decimal
from datetime import datetime
from document_parser import DocumentParser
from errors import BinanceTradeException


class BinanceXlsxOldParser(DocumentParser):
    def __init__(self, *args, **kwargs):
        kwargs['exchange_name'] = 'binance'
        kwargs['header'] = {
            'created_at': 'Date(UTC)',
            'amount': 'Amount',
            'fill_amount': 'Total',
            'currency_pair': 'Market',
            'type': 'Type',
            'price': 'Price',
        }
        kwargs['header_rows'] = 0
        super(BinanceXlsxOldParser, self).__init__(*args, **kwargs)

    def process_row(self, row):
        row['created_at'] = self.process_date(row)
        row['currency_pair'] = self.process_currency_pair(row)
        row['type'] = row['type'].lower()

        for key in ('amount', 'fill_amount', 'price'):
            row[key] = abs(Decimal(row[key]))
        return row

    def process_date(self, row):
        _date = row['created_at']
        if isinstance(_date, str):
            return datetime.strptime(_date, '%Y-%m-%d %H:%M:%S')
        if isinstance(_date, date):
            return datetime(_date.year, _date.month, _date.day)
        else:
            return _date

    def process_currency_pair(self, row):
        quote_pairs = ['BTC', 'ETH', 'USDT']
        pair = row['currency_pair']

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
