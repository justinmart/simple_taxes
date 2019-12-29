from decimal import Decimal
from datetime import datetime
from document_parser import DocumentParser


class PoloniexParser(DocumentParser):
    def __init__(self, *args, **kwargs):
        kwargs['exchange_name'] = 'poloniex'
        kwargs['header'] = {
            'created_at': 'Date',
            'amount': 'Amount',
            'fill_amount': 'Total',
            'currency_pair': 'Market',
            'type': 'Type',
            'price': 'Price',
        }
        kwargs['header_rows'] = 0
        super(PoloniexParser, self).__init__(*args, **kwargs)

    def process_row(self, row):
        row['created_at'] = self.process_date(row)
        row['type'] = row['type'].lower()
        row['currency_pair'] = self.process_currency_pair(row)

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
        pair = row['currency_pair']
        first = pair.split("/")[0]
        last = pair.split("/")[1]

        if first == 'BCHSV':
            first = 'BSV'
        elif first == 'BCHABC':
            first = 'BCH'

        return first + "-" + last
