from decimal import Decimal
from datetime import datetime
from document_parser import DocumentParser


class BinanceParser(DocumentParser):
    def __init__(self, *args, **kwargs):
        kwargs['exchange_name'] = 'binance'
        kwargs['header'] = {
            'created_at': 'created_at',
            'amount': 'amount',
            'fill_amount': 'fill_amount',
            'currency_pair': 'currency_pair',
            'type': 'type',
            'price': 'price',
        }
        kwargs['header_rows'] = 0
        super(BinanceParser, self).__init__(*args, **kwargs)

    def process_row(self, row):
        row['created_at'] = self.process_date(row)
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
