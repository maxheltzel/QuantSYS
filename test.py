import yfinance as yf


def get_options_data(symbol):
    stock = yf.Ticker(symbol)
    expirations = stock.options
    options_data = {}

    for expiry in expirations:
        options_chain = stock.option_chain(expiry)
        options_data[expiry] = {'calls': options_chain.calls, 'puts': options_chain.puts}  # Collect both calls and puts

    return options_data



symbol = input("Enter stock symbol: ")
