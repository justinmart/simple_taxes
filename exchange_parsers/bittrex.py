from decimal import Decimal
from datetime import datetime
from document_parser import DocumentParser


class BittrexParser(DocumentParser):
    def __init__(self, *args, **kwargs):
        kwargs['exchange_name'] = 'bittrex'
        kwargs['header'] = {
            'created_at': 'Closed',
            'amount': 'Quantity',
            'fill_amount': None,
            'currency_pair': 'Exchange',
            'type': ['Type', 'OrderType'],
            'price': None,
        }
        kwargs['header_rows'] = 0
        super(BittrexParser, self).__init__(*args, **kwargs)

    def process_row(self, row):
        row['created_at'] = datetime.strptime(row['created_at'], '%m/%d/%Y %I:%M:%S %p')
        row['type'] = row['type'].split("_")[1].lower()
        row['currency_pair'] = self.process_currency_pair(row)
        row['amount'] = abs(Decimal(row['amount']))
        row['fill_amount'] = self.process_fill_amount(row)
        row['price'] = row['fill_amount'] / row['amount']
        return row

    def process_currency_pair(self, row):
        first = row['currency_pair'].split("-")[1]
        last = row['currency_pair'].split("-")[0]

        if first == 'BCC':
            first = 'BCH'
        return first + "-" + last

    def process_fill_amount(self, row):
        price = abs(Decimal(row['_extras']['Price']))
        try: 
            fees = abs(Decimal(row['_extras']['CommissionPaid']))
        except:
            fees = abs(Decimal(row['_extras']['Commission']))
        return price - fees
