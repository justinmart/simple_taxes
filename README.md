# Simple Crypto Taxes

This project simplifies the process of determining profit-and-loss for cryptocurrency trades.
It will provide:
* A detailed report containing information about every trade
* A detailed profit-and-loss calculation on every trade
* A simplified report containing basic profit-and-loss data on each trade (useful for Tax Accountants or for tax filings)
* A report on aggreagate profit-and-loss from all trades by year, and by short-term vs long-term gains
* A report on all errors encountered in the process

It supports trades from all the major US Exchanges and some international exchanges via `csv` and `xlsx` trading history files.
* Coinbase
* Coinbase Pro
* Binance
* Gemini
* Kraken
* Poloniex
* Bitfinex
* Bittrex
* Circle
* It also supports manual trades via entering them into a spreadsheet and saving a copy as a `.csv`

## Getting Started

These instructions will get you a copy of the project up and running on your local machine, and guidance on how to obtain your own tax reports.

If you do not have Python version 2.7 installed on your machine, download and install Anaconda Python version 2.7 (here: https://www.anaconda.com/download/). This will install python and Jupyter Notebook, and easy interface to run python scripts.

Once python is installed, from any terminal run: `pip install ...` for each library in `requirements.txt`. Currently there are only two requirements:
  * `pip install cached-property`
  * `pip install xlrd`

Once Python 2.7 with Jupyter Notebook and all relevant requirements are installed on your machine, follow these steps:
1. Download this repo to your local machine
2. Go to each supported exchange for which you have trades and download a `csv` or `xlsx` of your trade history
3. Put these `csv` or `xlsx` files into the appropriate folder inside the `data/` directory (the program will automatically parse *all* files in the correct folders)
  * For Binance, please note they have recently changed their trade history reports. **Important** You must pull your "TRADE HISTORY" from Binance (not "Order History"). Put all newly downloaded reports in the `binance_xlsx` folder.
  * NOTE: In generaly, this tool only works for **USD fiat trades**, if you are buying / selling into another fiat currency (EUR, GBP, etc), then this tool will not work. 
4. For any trades that are from unsupported exchanges, or any other manual trades (ICOs, forks, in-person or on-chain trades, etc) populate a spreadsheet with a specific format (see below)
5. Run the script (see below), which populates 5 files in the `output` folder:
  * `trades.csv`          : Detailed information regarding every trade across all exchanges and currencies
  * `errors`              : Information on any errors or any trades left out of the calculations
  * `pnl.cvs`             : Profit-and-loss calculations for each trade, including long-term vs short-term gains
  * `total_pnl`           : Aggregate information on profit and loss for each year, by short term vs long term
  * `tax_reporting_data`  : A spreadsheet intended to be sent to the IRS or a tax accountant which details every trade and the profit-and-loss associated with each

## Run the program

If you have Jupyter Notebook installed, from any terminal type `jupyter notebook` and navigate to where this repo was downloaded. Run the provided `Jupyter Notebook Taxes Script` and follow the directions in that script.

Alternatively, you can. run the following commands from a python session:

`$ from taxes import Taxes`

`$ trades, errors, pnl, total_pnl, tax_reporting_data, remaining_funds = Taxes().run()`

This will populate 5 files in the `output/` folder with detailed information on your trades and your profit-and-loss (see above).


## Populating a Manual Trades spreadsheet

For any trades that are from unsupported exchanges, or any other trades, populate a spreadsheet with a specific format. Save this spreadsheet as a `.csv` and place it in the `data/manual_trades/` folder.

The specific formula for all trades must follow:
```
created_at    : The date of the trade (in 01/30/2018 24:01:01 or 01/30/2018 format)
amount        : The amount of the asset that was bought or sold
fill_amount   : The amount received for buying or selling (this is the "base pair")
currency_pair : The trade pair, with the base-pair last. E.g., BTC-USD (USD is always the base pair), 'BAT-ETH' (ETH is the base pair), 'LTC-BTC' (BTC is the base pair)
type          : Either buy or sell (based on the trade-pair)
price         : The price of the trade
platform      : The exchange or mechanism of trade (e.g., `fork`, `ico`, `airdrop`, `gift`, `btc blockchain`, `bitmex`, `in-person`, etc)
```

*Examples:*
- 10 ETH sold for 1 BTC:
```
created_at: 01/01/2018
amount: 10
fill_amount: 1
currency_pair: ETH-BTC
type: sell
price: 0.1
platform: in-person
```
- 0.5 BTC purchased for $2500 USD
```
created_at: 01/01/2018
amount: 0.5
fill_amount: 2500
currency_pair: BTC-USD
type: buy
price: 5000
platform: bitmex
```
- 500 BAT purchased for 0.25 ETH
```
created_at: 01/01/2018
amount: 500
fill_amount: 0.25
currency_pair: BAT-ETH
type: buy
price: 0.0005
platform: shapeshift
```
**Forks, Airdrops, and Gifts** must have `ico`, `airdrop`, or `gift` as the platform and with USD as the base pair. In this calculator, we treat these events as purchases where the purchase price is $0.
- For example, the BCH fork granting 2 BCH
```
created_at: 01/01/2017
amount: 2
fill_amount: 0
currency_pair: BCH-USD
type: buy
price: 0
platform: ico
```
**ICOs** must include a platform field, and the platform must be `ico`.
- For example, receiving 10000 BAT in the Basic Attention Token crowdsale
```
created_at: 08/16/2017
amount: 10000
fill_amount: 1.56
currency_pair: BAT-ETH
type: buy
price: 0.000156
platform: ico
```

## Error Catching

Cryptocurrency taxes are complex. It's easy to forget about some trades or other sources of crypto. If the program discovers you are trying to sell more than you have purchased, it will halt and provide detailed information related to exactly where this error occurred, for which currency, and a history of all buys & sells and the resulting available balance up to that point.

It's expected that this detailed output will help you remember which purchases you may have forgotten.

## Authors

* **Justin Mart** - *Developer* - [justinmart](https://github.com/justinmart)
* **Omar Bohsali** - *Architectural Consulting* - [omarish](https://github.com/omarish)

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details
