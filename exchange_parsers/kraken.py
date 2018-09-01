from decimal import Decimal
from datetime import datetime
from document_parser import DocumentParser


class KrakenParser(DocumentParser):
    def __init__(self, *args, **kwargs):
        kwargs['exchange_name'] = 'kraken'
        kwargs['header'] = {
            'created_at': 'time',
            'amount': 'vol',
            'fill_amount': 'cost',
            'currency_pair': 'pair',
            'type': 'type',
            'price': 'price',
        }
        kwargs['header_rows'] = 0
        super(KrakenParser, self).__init__(*args, **kwargs)

    def process_row(self, row):
        row['created_at'] = datetime.strptime(row['created_at'], '%Y-%m-%d %H:%M:%S.%f')
        row['type'] = row['type'].lower()
        row['currency_pair'] = self.process_currency_pair(row)

        for key in ('amount', 'fill_amount', 'price'):
            row[key] = abs(Decimal(row[key]))
        return row

    def process_currency_pair(self, row):
        first = row['currency_pair'].split("X")[1].replace('BT', 'BTC')
        second = row['currency_pair'].split("X")[-1].replace('BT', 'BTC')
        return first + '-' + second
