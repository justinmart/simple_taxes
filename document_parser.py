import csv
import xlrd
import os
from cached_property import cached_property
from rates import ExchangeRates
from decimal import Decimal
from datetime import datetime
from errors import MissingHeaderElementError, InvalidTradeException, \
    NotATradeException, TradeTooSmallException


class DocumentParser(object):
    """
    DocumentParser takes a document and parses it's data into a standard format. It accepts either CSV or XLSX files and will
    automatically parse either one, as long as each file contains a proper "required_fields" mapping.

    Overview:
    Each exchange provides CSVs or XLSX files of a user's complete trading activity. We ingest these files, and as long as we can
    tease out the "required fields" we will be able to construct every other metric we need to perform a tax analysis.

    Each exchange has a sub-class which uniquely parses their files and returns the required fields. This class then uses the
    required fields to construct every other metric.

    params
    required fields.     : Mapping of name of required fields for each trade and data type. See README.md for more.
    include_small_trades : We remove small trades based on a threshold. A trade is "small" if either side of the trade
                           is less than the threshold. Some trades are technically small but very meaningful, namely
                           ICOs, Fork, Airdrops, and Gifts. For these trades, the "fill amount" (e.g., the amount you paid)
                           is effectively zero (they are free transactions), so they qualify as small.
                           Include all small trades that are included in the "include_small_trades" list.

    errors
    MissingHeaderElementError  : If an exchange parser does not supply the required fields, this exception is thrown
    NotATradeException         : If an exchange returns extraneous non-trade data (deposits, withdrawals, etc)
    TradeTooSmallException     : If the amount (on either side of a trade) is below a theshold, it is omitted
    """
    required_fields = {
        'created_at': datetime,
        'amount': Decimal,
        'fill_amount': Decimal,
        'price': Decimal,
        'currency_pair': str,
        'type': str,
    }
    include_small_trades = ['fork', 'ico', 'airdrop', 'gift']
    small_trade_threshold = Decimal(1E-7)

    def __init__(self, exchange_name=None, header=None, header_rows=None):
        self.exchange_name = exchange_name
        self.header = header
        self.header_rows = header_rows
        self._validate_header()

    @cached_property
    def rates(self):
        return ExchangeRates().parse_file(os.path.join('data', 'exchange_rates.csv'))

    def _validate_header(self):
        for field in self.required_fields.keys():
            if field not in self.header.keys():
                raise errors.MissingHeaderElementError("Missing field: {}".format(field))

    def run(self, filename):
        filetype = filename.split('.')[-1]
        if filetype == 'csv':
            return self.open_csv(filename)
        elif filetype == 'xlsx':
            return self.open_xlsx(filename)
        else:
            raise ValueError("Filetype is neither csv or xlsx: %s" % filetype)

    def open_xlsx(self, filename):
        workbook = xlrd.open_workbook(filename)
        sheet_index = 0
        sheet = workbook.sheet_by_index(sheet_index)
        headers = dict((_, sheet.cell_value(0, _)) for _ in range(sheet.ncols) )
        reader = (dict((headers[j], sheet.cell_value(i, j)) for j in headers) for i in range(1, sheet.nrows))
        return self.xlsx_parser(reader)

    def xlsx_parser(self, reader):
        trades = []
        errors = []
        for row in reader:
            dict_row = {self.decode(k): self.decode(v) for k,v in row.items()}
            try:
                trade = self.parse_trade(dict_row)
            except InvalidTradeException as exc:
                errors.append(exc)
            else:
                trades.append(trade)
        return trades, errors

    def decode(self, arg):
        if isinstance(arg, unicode):
            return arg.encode()
        return arg

    def open_csv(self, filename):
        with open(filename, 'r') as f:
            return self.csv_parser(self.skip_headers(f))

    def skip_headers(self, f_obj):
        for i in range(self.header_rows):
            f_obj.next()
        return f_obj

    def csv_parser(self, f_obj):
        reader = csv.DictReader(_.replace('\0', '') for _ in f_obj)
        trades = []
        errors = []
        for row in reader:
            try:
                trade = self.parse_trade(row)
            except InvalidTradeException as exc:
                errors.append(exc)
            else:
                trades.append(trade)
        return trades, errors

    def parse_trade(self, row):
        trade = {}
        for native_name, vendor_name in self.header.items():
            if not vendor_name:
                continue
            trade[native_name] = row.pop(vendor_name)
        trade['_extras'] = row
        processed_trade = self.process_row(trade)
        self.validate_trade_type(processed_trade)
        processed_trade.update(self.generate_implied_fields(processed_trade))
        self.validate_trade(processed_trade)
        return processed_trade

    def validate_trade_type(self, trade):
        if trade['type'] not in ['buy', 'sell']:
            raise NotATradeException("Trade is not a buy or sell", trade)

    def validate_trade(self, trade):
        self.validate_row(trade)
        if (trade['amount'] < self.small_trade_threshold or \
            trade['fill_amount'] < self.small_trade_threshold) and \
            (trade['platform'] not in self.include_small_trades):
            raise TradeTooSmallException("Trade amount is too low", trade)

    def generate_implied_fields(self, trade):
        fields = [
            'platform', 'currency', 'fill_currency', 'fill_type',
            'native_value', 'native_currency', 'basis', 'fill_basis'
        ]
        implied_fields = {}
        for _ in fields:
            implied_fields[_] = eval('self.generate_{}_field(trade)'.format(_))
            trade.update({_: implied_fields[_]})
        return implied_fields

    def generate_platform_field(self, trade):
        return self.exchange_name

    def generate_currency_field(self, trade):
        return trade['currency_pair'].split('-')[0]

    def generate_fill_currency_field(self, trade):
        return trade['currency_pair'].split('-')[1]

    def generate_fill_type_field(self, trade):
        if trade['type'] == 'buy':
            return 'sell'
        elif trade['type'] == 'sell':
            return 'buy'
        else:
            raise NotATradeException("Trade is not a buy or sell", trade)

    def generate_native_value_field(self, trade):
        fill_amount = trade['fill_amount']
        fill_currency = trade['fill_currency']
        created_at = trade['created_at'].date()

        if fill_currency == 'USD':
            return fill_amount
        else:
            try:
                rate = self.rates[created_at][fill_currency]
            except:
                raise ValueError('Native Value could not find exchange rate {}'.format(trade))
        return fill_amount / rate

    def generate_native_currency_field(self, trade):
        return 'USD'

    def generate_basis_field(self, trade):
        return trade['native_value'] / trade['amount']

    def generate_fill_basis_field(self, trade):
        # Some trades have no value for the fill amount (ICOs, Forks, etc)
        try:
            return trade['native_value'] / trade['fill_amount']
        except:
            return Decimal('0')

    def process_row(self, row):
        raise NotImplemented()

    def validate_row(self, row):
        for key, _type in self.required_fields.items():
            if not isinstance(row[key], _type):
                raise TypeError("%s should be %s, got %s" % (key, _type, type(row[key])))
