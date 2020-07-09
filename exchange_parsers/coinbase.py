from decimal import Decimal
from datetime import datetime
from document_parser import DocumentParser
from errors import InvalidTradeException


class CoinbaseParser(DocumentParser):
    # WARNING: Coinbase Parser only works for USD-denominated buys and sells. 
    def __init__(self, *args, **kwargs):
        kwargs['exchange_name'] = 'coinbase'
        kwargs['header'] = {
            'created_at': 'Timestamp',
            'amount': 'Quantity Transacted',
            'fill_amount': 'USD Total (inclusive of fees)',
            'currency_pair': 'Asset',
            'type': 'Transaction Type',
            'price': 'USD Spot Price at Transaction'
        }
        kwargs['header_rows'] = 7
        super(CoinbaseParser, self).__init__(*args, **kwargs)

    def process_row(self, row):
        if row['type'].lower() not in ['buy', 'sell', 'trade']:
            raise InvalidTradeException("Coinbase trade is not a buy or sell: %s" % row)

        if row['type'].lower() == 'trade':
            raise Error("Coinbase crypto<>crypto trades are not supported. Add them as manual trades \n"
                "and manually remove these trades from your coinbase.csv trades file. \n"
                "Trade: %s" % row['_extras']['Notes'])
        else:
            row['created_at'] = datetime.strptime(row['created_at'], '%Y-%m-%dT%H:%M:%SZ')
            row['type'] = row['type'].lower()
            row['currency_pair'] = row['currency_pair'] + '-USD'

            for key in ('amount', 'fill_amount', 'price'):
                row[key] = abs(Decimal(row[key]))
        return row
