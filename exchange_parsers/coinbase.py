from decimal import Decimal
from datetime import datetime
from document_parser import DocumentParser
from errors import InvalidTradeException


class CoinbaseParser(DocumentParser):
    def __init__(self, *args, **kwargs):
        kwargs['exchange_name'] = 'coinbase'
        kwargs['header'] = {
            'created_at': 'Timestamp',
            'amount': 'Quantity Transacted',
            'fill_amount': 'USD Amount Transacted (Inclusive of Coinbase Fees)',
            'currency_pair': 'Asset',
            'type': 'Transaction Type',
            'price': 'USD Spot Price at Transaction'
        }
        kwargs['header_rows'] = 3
        super(CoinbaseParser, self).__init__(*args, **kwargs)

    def process_row(self, row):
        if row['type'].lower() not in ['buy', 'sell']:
            raise InvalidTradeException("Coinbase trade is not a buy or sell: %s" % row)

        row['created_at'] = datetime.strptime(row['created_at'], '%m/%d/%Y')
        row['type'] = row['type'].lower()
        row['currency_pair'] = row['currency_pair'] + '-USD'

        for key in ('amount', 'fill_amount', 'price'):
            row[key] = abs(Decimal(row[key]))
        return row
