class ParserError(Exception):
    pass

class MissingHeaderElementError(ParserError):
    pass

class InvalidTradeException(Exception):
    pass

class NotATradeException(InvalidTradeException):
    pass

class TradeTooSmallException(InvalidTradeException):
    pass

class ApiError(Exception):
    pass

class UpdateExchangeRateException(Exception):
    pass

class NoNewExchangeRatesException(UpdateExchangeRateException):
    pass

class ExchangeRatesAlreadyUpToDateException(UpdateExchangeRateException):
    pass
