from decimal import Decimal
from datetime import datetime
from document_parser import DocumentParser


class BitfinexParser(DocumentParser):
    def __init__(self, *args, **kwargs):
        kwargs['exchange_name'] = 'bitfinex'
        kwargs['header'] = {
            'created_at': 'Date',
            'amount': 'Amount',
            'fill_amount': None,
            'currency_pair': 'Pair',
            'type': None,
            'price': 'Price',
        }
        kwargs['header_rows'] = 0
        super(BitfinexParser, self).__init__(*args, **kwargs)

    def process_row(self, row):
        row['created_at'] = datetime.strptime(row['created_at'], '%Y-%m-%d %H:%M:%S')
        row['type'] = self.process_type(row)
        row['currency_pair'] = self.process_currency_pair(row)

        for key in ('amount', 'price'):
            row[key] = abs(Decimal(row[key]))
        row['fill_amount'] = row['amount'] * row['price']
        return row

    def process_type(self, row):
        amount = row['amount']
        if amount > 0:
            return 'buy'
        elif amount < 0:
            return 'sell'
        else:
            raise ValueError("Bitfinex trade is niether buy nor sell: {}".foramt(row))

    def process_currency_pair(self, row):
        pair = row['currency_pair']
        return pair.split("/")[0] + "-" + pair.split("/")[1]
