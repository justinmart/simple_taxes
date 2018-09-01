from decimal import Decimal
from datetime import datetime
from document_parser import DocumentParser


class CoinbaseProParser(DocumentParser):
    def __init__(self, *args, **kwargs):
        kwargs['exchange_name'] = 'coinbase_pro'
        kwargs['header'] = {
            'created_at': 'created at',
            'amount': 'size',
            'fill_amount': 'total',
            'currency_pair': 'product',
            'type': 'side',
            'price': 'price',
        }
        kwargs['header_rows'] = 0
        super(CoinbaseProParser, self).__init__(*args, **kwargs)

    def process_row(self, row):
        row['created_at'] = datetime.strptime(row['created_at'], '%Y-%m-%dT%H:%M:%S.%fZ')
        row['type'] = row['type'].lower()

        for key in ('amount', 'fill_amount', 'price'):
            row[key] = abs(Decimal(row[key]))
        return row
