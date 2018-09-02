from errors import NotATradeException
from decimal import Decimal
from datetime import datetime, timedelta
from document_parser import DocumentParser


class GeminiParser(DocumentParser):
    def __init__(self, *args, **kwargs):
        kwargs['exchange_name'] = 'gemini'
        kwargs['header'] = {
            'created_at': None,
            'amount': None,
            'fill_amount': None,
            'currency_pair': None,
            'type': 'Type',
            'price': None,
        }
        kwargs['header_rows'] = 0
        super(GeminiParser, self).__init__(*args, **kwargs)

    def process_row(self, row):
        if row['type'].lower() not in ['buy', 'sell']:
            raise NotATradeException("Gemini trade is not a buy or sell: %s" % row)

        row['type'] = row['type'].lower()
        row['created_at'] = self.process_date(row)
        row['amount'] = self.process_amount(row)
        row['fill_amount'] = self.process_fill_amount(row)
        row['currency_pair'] = self.process_currency_pair(row)
        row['price'] = self.process_price(row)
        return row

    def process_date(self, row):
        date = float(row['_extras']['Date'])
        temp = datetime(1900, 1, 1)
        delta = timedelta(days=date - 2)
        utc_delta = timedelta(hours=-7)
        return temp + delta + utc_delta

    def process_amount(self, row):
        currency = row['_extras']['Symbol'][:3]
        amt = str(row['_extras'][currency + ' Amount'])
        chars = ['.', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', 'e', '-']
        return abs(Decimal(''.join(_ if _ in chars else '' for _ in amt)))

    def process_fill_amount(self, row):
        currency = row['_extras']['Symbol'][3:]
        amt = str(row['_extras'][currency + ' Amount'])
        chars = ['.', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', 'e', '-']
        return abs(Decimal(''.join(_ if _ in chars else '' for _ in amt)))

    def process_currency_pair(self, row):
        return row['_extras']['Symbol'][:3] + '-' + row['_extras']['Symbol'][3:]

    def process_price(self, row):
        return row['fill_amount'] / row['amount']
