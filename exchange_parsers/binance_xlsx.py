from decimal import Decimal
from datetime import datetime
from document_parser import DocumentParser


class BinanceXlsxParser(DocumentParser):
    # WARNING: You must download your "Trade History" from Binance, **NOT** "Order History"  
    # Order History has a completely different formatting which will not work. 
    def __init__(self, *args, **kwargs):
        kwargs['exchange_name'] = 'binance'
        kwargs['header'] = {
            'created_at': 'Date(UTC)',
            'amount': 'Amount',
            'fill_amount': 'Total',
            'currency_pair': 'Market',
            'type': 'Type',
            'price': 'Price',
        }
        kwargs['header_rows'] = 0
        super(BinanceXlsxParser, self).__init__(*args, **kwargs)

    def process_row(self, row):
        row['created_at'] = self.process_date(row)
        row['currency_pair'] = self.process_currency_pair(row)
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

    def process_currency_pair(self, row):
        # WARNING: If USD is added to the quote pair, we'll need to change how we parse pairs below
        # because pair[-3:] will match USD even if it's TUSD, etc. 
        quote_pairs = ['USDC', 'USDT', 'TUSD', 'BUSD', 'DAI', 'BTC', 'ETH']
        pair = row['currency_pair']

        if pair[-3:] in quote_pairs:
            first = pair[:-3] 
            last =  pair[-3:]
        elif pair[-4:] in quote_pairs:
            first = pair[:-4] 
            last = pair[-4:]
        else:
            raise Exception('Binance quote pair is not one of {}'.format(quote_pairs))

        if first == 'BCC':
            first = 'BCH'
        return first + "-" + last
