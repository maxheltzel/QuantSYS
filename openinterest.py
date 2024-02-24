import yfinance as yf
import pandas as pd
import mibian
import matplotlib.pyplot as plt
import subprocess
import sys


# Constants
CONTRACT_SIZE = 100  # Each options contract is typically for 100 shares
RISK_FREE_RATE = 1  # Risk-free interest rate as a percentage
VOLATILITY = 20  # Placeholder volatility as a percentage

# Function to fetch options data for the nearest expiration date
def fetch_options(ticker):
    stock = yf.Ticker(ticker)
    expiration_dates = stock.options
    if not expiration_dates:
        raise ValueError(f"No options data available for {ticker}")
    nearest_expiration = expiration_dates[0]

    opt_chain = stock.option_chain(nearest_expiration)
    calls = opt_chain.calls.assign(Type='Call', Expiration=nearest_expiration)
    puts = opt_chain.puts.assign(Type='Put', Expiration=nearest_expiration)
    options = pd.concat([calls, puts])

    return options, nearest_expiration
# Function to calculate Black-Scholes Delta
def calculate_deltas(options_df, stock_price, days_to_expiry):
    interest_rate = RISK_FREE_RATE / 100  # Convert to decimal

    # Calculate Delta for each option
    options_df['Delta'] = options_df.apply(
        lambda row: mibian.BS([stock_price, row['strike'], interest_rate, days_to_expiry], volatility=VOLATILITY).callDelta if row['Type'] == 'Call'
        else mibian.BS([stock_price, row['strike'], interest_rate, days_to_expiry], volatility=VOLATILITY).putDelta, axis=1)

    return options_df

# Function to calculate notional values
def calculate_notional_value(options_df):
    options_df['Notional Value'] = options_df['openInterest'] * options_df['Delta'] * options_df['strike'] * CONTRACT_SIZE
    return options_df



# Main execution
def main1(ticker_symbol):

    options_df, expiration = fetch_options(ticker_symbol)

    # Fetch the current price of the underlying stock
    stock_price = yf.Ticker(ticker_symbol).history(period="1d")['Close'].iloc[-1]

    # Calculate days to expiry
    today = pd.Timestamp.today()
    expiry = pd.Timestamp(expiration)
    days_to_expiry = (expiry - today).days

    # Calculate Deltas using Black-Scholes model
    options_df_with_deltas = calculate_deltas(options_df, stock_price, days_to_expiry)

    # Calculate notional value
    options_with_notional = calculate_notional_value(options_df_with_deltas)

    # Find strikes with the highest open interest for calls and puts
    highest_open_interest_call = options_with_notional[options_with_notional['Type'] == 'Call'].nlargest(1, 'openInterest')['strike'].iloc[0]
    highest_open_interest_put = options_with_notional[options_with_notional['Type'] == 'Put'].nlargest(1, 'openInterest')['strike'].iloc[0]

    # Format Delta with 4 decimal places
    options_with_notional['Delta'] = options_with_notional['Delta'].apply(lambda x: f'{x:.4f}')

    # Sort the DataFrame by strike price
    options_with_notional_sorted = options_with_notional.sort_values(by='strike')

    # Separate call and put options
    call_options = options_with_notional_sorted[options_with_notional_sorted['Type'] == 'Call']
    put_options = options_with_notional_sorted[options_with_notional_sorted['Type'] == 'Put']

    # Calculate total notional for call and put options
    total_call_notional = call_options.groupby('strike')['Notional Value'].sum()
    total_put_notional = put_options.groupby('strike')['Notional Value'].sum()

    # Subtract put notional from call notional
    net_notional = total_call_notional - total_put_notional

    # Get the closest 10 strikes below and above the current stock price
    closest_strikes_below = options_with_notional_sorted[options_with_notional_sorted['strike'] < stock_price].tail(40)
    closest_strikes_above = options_with_notional_sorted[options_with_notional_sorted['strike'] >= stock_price].head(40)

    # Concatenate the two subsets
    closest_strikes = pd.concat([closest_strikes_below, closest_strikes_above])

    # Plot
    plt.figure(figsize=(12, 6))
    plt.bar(closest_strikes['strike'], closest_strikes['Notional Value'],
            color=closest_strikes['Notional Value'].apply(lambda x: '#68838B' if x < 0 else '#00BFFF'))
    plt.xlabel('Strike Price')
    plt.ylabel('Notional Value')
    plt.title('Notional Value by Strike Price')
    plt.axhline(0, color='black', linewidth=0.8)  # Add a line at y=0 for reference

    # Annotate the points for highest open interest
    plt.annotate(f'Highest Open Interest (Call)\nStrike: {highest_open_interest_call}',
                 xy=(highest_open_interest_call, options_with_notional[options_with_notional['strike'] == highest_open_interest_call]['Notional Value'].values[0]),
                 xytext=(highest_open_interest_call, options_with_notional[options_with_notional['strike'] == highest_open_interest_call]['Notional Value'].values[0] + 500),
                 arrowprops=dict(facecolor='black', arrowstyle='->'),
                 horizontalalignment='center', fontsize=7, fontname='Consolas', color='#292421')

    plt.annotate(f'Highest Open Interest (Put)\nStrike: {highest_open_interest_put}',
                 xy=(highest_open_interest_put, options_with_notional[options_with_notional['strike'] == highest_open_interest_put]['Notional Value'].values[0]),
                 xytext=(highest_open_interest_put, options_with_notional[options_with_notional['strike'] == highest_open_interest_put]['Notional Value'].values[0] - 500),
                 arrowprops=dict(facecolor='black', arrowstyle='->'),
                 horizontalalignment='center', fontsize=7, fontname='Consolas', color='#292421')

    plt.grid(axis='y', linestyle='--')
    plt.show()


if __name__ == "__main1__":
    if len(sys.argv) != 2:
        print("Usage: python openinterest.py <ticker_symbol>")
        sys.exit(1)
    ticker_symbol = sys.argv[1].upper()
    main1(ticker_symbol)