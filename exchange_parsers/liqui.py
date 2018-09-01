from decimal import Decimal
from datetime import datetime
from document_parser import DocumentParser


class LiquiParser(DocumentParser):
    def __init__(self, *args, **kwargs):
        kwargs['exchange_name'] = 'liqui'
        kwargs['header'] = {
            'created_at': 'Date',
            'amount': 'Amount',
            'fill_amount': 'Total',
            'currency_pair': 'Market',
            'type': 'Type',
            'price': 'Price',
        }
        kwargs['header_rows'] = 0
        super(LiquiParser, self).__init__(*args, **kwargs)

    def process_row(self, row):
        row['created_at'] = datetime.strptime(row['created_at'], '%d.%m.%Y %H:%M:%S')
        row['type'] = row['type'].lower()
        row['currency_pair'] = row['currency_pair'].replace('/', '-')

        for key in ('amount', 'fill_amount', 'price'):
            row[key] = abs(Decimal(row[key]))
        return row
