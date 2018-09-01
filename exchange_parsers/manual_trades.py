from decimal import Decimal
from datetime import datetime
from document_parser import DocumentParser


class ManualTradesParser(DocumentParser):
    def __init__(self, *args, **kwargs):
        kwargs['exchange_name'] = 'manual'
        kwargs['header'] = {
            'created_at': 'created_at',
            'amount': 'amount',
            'fill_amount': 'fill_amount',
            'currency_pair': 'currency_pair',
            'type': 'type',
            'price': 'price',
        }
        kwargs['header_rows'] = 0
        super(ManualTradesParser, self).__init__(*args, **kwargs)

    def process_row(self, row):
        row['created_at'] = self.process_date(row)
        row['type'] = row['type'].lower()

        for key in ('amount', 'fill_amount'):
            row[key] = abs(Decimal(row[key]))
        row['price'] = self.process_price(row)
        return row

    def process_date(self, row):
        _date = row['created_at']
        if isinstance(_date, str):
            try:
                return datetime.strptime(_date, '%m/%d/%Y %H:%M:%S')
            except:
                return datetime.strptime(_date, '%m/%d/%Y')
        if isinstance(_date, date):
            return datetime(_date.year, _date.month, _date.day)
        else:
            return _date

    def process_price(self, row):
        try:
            return abs(Decimal(row['price']))
        except:
            return row['fill_amount'] / row['amount']

    def generate_platform_field(self, trade):
        return trade['_extras']['platform']
