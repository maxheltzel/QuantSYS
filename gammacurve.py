import yfinance as yf
import pandas as pd
import mibian
import matplotlib.pyplot as plt
import numpy as np
import sys

# Constants
CONTRACT_SIZE = 100  # Each options contract is typically for 100 shares
RISK_FREE_RATE = 1  # Risk-free interest rate as a percentage


def volatility(ticker_symbol, period="5y"):
    stock = yf.Ticker(ticker_symbol)
    historical_data = stock.history(period=period)
    daily_returns = historical_data['Close'].pct_change().dropna()
    volatility = daily_returns.std() * np.sqrt(252) * 100  # Assuming 252 trading days in a year
    return volatility


# Function to fetch options data for the nearest expiration date
def fetch_options_first(ticker):
    stock = yf.Ticker(ticker)
    expiration_dates = stock.options
    nearest_expiration = expiration_dates[0]

    opt_chain = stock.option_chain(nearest_expiration)
    calls = opt_chain.calls.assign(Type='Call', Expiration=nearest_expiration)
    puts = opt_chain.puts.assign(Type='Put', Expiration=nearest_expiration)

    # Include open interest data
    calls['Open_Interest'] = calls['openInterest']
    puts['Open_Interest'] = puts['openInterest']

    options = pd.concat([calls, puts])

    return options


def fetch_options_second(ticker):
    stock = yf.Ticker(ticker)
    expiration_dates = stock.options
    second_nearest_expiration = expiration_dates[1]

    opt_chain = stock.option_chain(second_nearest_expiration)
    calls = opt_chain.calls.assign(Type='Call', Expiration=second_nearest_expiration)
    puts = opt_chain.puts.assign(Type='Put', Expiration=second_nearest_expiration)

    # Include open interest data
    calls['Open_Interest'] = calls['openInterest']
    puts['Open_Interest'] = puts['openInterest']

    options = pd.concat([calls, puts])

    return options


def fetch_options_third(ticker):
    stock = yf.Ticker(ticker)
    expiration_dates = stock.options
    third_nearest_expiration = expiration_dates[2]

    opt_chain = stock.option_chain(third_nearest_expiration)
    calls = opt_chain.calls.assign(Type='Call', Expiration=third_nearest_expiration)
    puts = opt_chain.puts.assign(Type='Put', Expiration=third_nearest_expiration)

    # Include open interest data
    calls['Open_Interest'] = calls['openInterest']
    puts['Open_Interest'] = puts['openInterest']

    options = pd.concat([calls, puts])

    return options


# Function to calculate Black-Scholes Gamma for calls and puts
def calculate_gamma(options_df, stock_price, days_to_expiry, volatility):
    interest_rate = RISK_FREE_RATE / 100  # Convert to decimal

    # Define a separate function for gamma calculation to include error handling
    def gamma_calc(row):
        try:
            # Your original calculation
            bs = mibian.BS([stock_price, row['strike'], interest_rate, days_to_expiry], volatility=volatility)
            return bs.gamma
        except ZeroDivisionError:
            # Return 0 (or any value you see fit) in case of division by zero
            return 0
        except Exception as e:
            # Optional: handle or log any other exceptions as needed
            print(f"Error calculating gamma for row {row}: {e}")
            return 0

    # Use the gamma_calc function instead of the lambda directly
    options_df['Gamma'] = options_df.apply(gamma_calc, axis=1)

    return options_df

def find_highest_open_interest(options_df):
    # For calls
    call_with_max_open_interest = options_df[options_df['Type'] == 'Call'].iloc[options_df[options_df['Type'] == 'Call']['Open_Interest'].idxmax()]
    # For puts
    put_with_max_open_interest = options_df[options_df['Type'] == 'Put'].iloc[options_df[options_df['Type'] == 'Put']['Open_Interest'].idxmax()]

    return call_with_max_open_interest, put_with_max_open_interest




def add_gradient_to_axvspan(start, end, color1, color2, num_bins=100, **kwargs):
    # Determine the alpha value step for each bin
    alpha_step = 1.0 / num_bins
    for i in range(num_bins):
        # Calculate the start and end positions for the current bin
        bin_start = start + (i * (end - start) / num_bins)
        bin_end = start + ((i + 1) * (end - start) / num_bins)
        # Calculate the alpha value for the current bin
        alpha = i * alpha_step
        # Interpolate between color1 and color2 for both RGB and alpha
        r = color1[0]
        g = color1[1]
        b = color1[2]
        a = alpha * color1[3] + (1.0 - alpha) * color2[3]
        # Set the color with the interpolated RGBA values
        rgba_color = (r, g, b, a)
        # Draw the axvspan with the current color
        plt.axvspan(bin_start, bin_end, color=rgba_color, **kwargs)

def filter_options_advanced(options_df, stock_price, n=30):
    # Calculate distance to the money
    options_df['DistanceToMoney'] = abs(options_df['strike'] - stock_price)
    # Sort options by distance to money and then by open interest to prioritize liquidity
    options_sorted = options_df.sort_values(by=['DistanceToMoney', 'Open_Interest'], ascending=[True, False])
    # Return the top n rows based on this sorting
    return options_sorted.head(n)

def find_least_gamma_strike(options_df_with_gamma):
    # Identify the strike price with the minimum gamma value
    least_gamma_strike_row = options_df_with_gamma.loc[options_df_with_gamma['Gamma'] == options_df_with_gamma['Gamma'].min()]
    least_gamma_strike = least_gamma_strike_row['strike'].iloc[0]  # Select the first strike in case of ties
    least_gamma_value = least_gamma_strike_row['Gamma'].iloc[0]

    return least_gamma_strike, least_gamma_value

def find_highest_strike_least_gamma(options_df_with_gamma):
    # Filter or sort to find the highest strike with the least gamma
    # First, sort by gamma ascending to find the least gamma values, then by strike descending to prioritize higher strikes, and finally take the first row
    least_gamma_high_strike_row = options_df_with_gamma.sort_values(by=['Gamma', 'strike'], ascending=[True, False]).iloc[0]
    least_gamma_strike = least_gamma_high_strike_row['strike']
    least_gamma_value = least_gamma_high_strike_row['Gamma']

    return least_gamma_strike, least_gamma_value


def main(ticker_symbol):
    ticker = yf.Ticker(ticker_symbol)
    options_df_first = fetch_options_first(ticker_symbol)
    options_df_second = fetch_options_second(ticker_symbol)
    options_df_third = fetch_options_third(ticker_symbol)

    call_max_open_interest_first, put_max_open_interest_first = find_highest_open_interest(options_df_first)
    call_max_open_interest_second, put_max_open_interest_second = find_highest_open_interest(options_df_second)
    call_max_open_interest_third, put_max_open_interest_third = find_highest_open_interest(options_df_third)

    # Fetch the current price of the underlying stock
    stock_price = yf.Ticker(ticker_symbol).history(period="1d")['Close'].iloc[-1]

    # Calculate days to expiry for each expiration date
    today = pd.Timestamp.today()
    expiry_first = pd.Timestamp(options_df_first['Expiration'].iloc[0])
    expiry_second = pd.Timestamp(options_df_second['Expiration'].iloc[0])
    expiry_third = pd.Timestamp(options_df_third['Expiration'].iloc[0])
    days_to_expiry_first = (expiry_first - today).days
    days_to_expiry_second = (expiry_second - today).days
    days_to_expiry_third = (expiry_third - today).days

    # Calculate historical volatility
    vol = volatility(ticker_symbol)
    print("Historical Volatility:", vol)

    # Sort options by their proximity to the current stock price for the first expiration date
    options_df_first['DistanceToMoney'] = abs(options_df_first['strike'] - stock_price)
    options_sorted_first = options_df_first.sort_values(by='DistanceToMoney')

    # Select 80 options closest to the money for the first expiration date
    options_closest_first = options_sorted_first.head(90)

    # Ensure options are sorted by strike price for smooth plotting for the first expiration date
    options_closest_sorted_by_strike_first = options_closest_first.sort_values(by='strike')

    # Calculate Gamma using Black-Scholes model for the selected options of the first expiration date
    options_df_with_gamma_first = calculate_gamma(options_closest_sorted_by_strike_first, stock_price,
                                                   days_to_expiry_first, vol)

    # Sort options by their proximity to the current stock price for the second expiration date
    options_df_second['DistanceToMoney'] = abs(options_df_second['strike'] - stock_price)
    options_sorted_second = options_df_second.sort_values(by='DistanceToMoney')

    # Select 80 options closest to the money for the second expiration date
    options_closest_second = options_sorted_second.head(90)

    # Ensure options are sorted by strike price for smooth plotting for the second expiration date
    options_closest_sorted_by_strike_second = options_closest_second.sort_values(by='strike')

    # Calculate Gamma using Black-Scholes model for the selected options of the second expiration date
    options_df_with_gamma_second = calculate_gamma(options_closest_sorted_by_strike_second, stock_price,
                                                    days_to_expiry_second, vol)

    # Sort options by their proximity to the current stock price for the third expiration date
    options_df_third['DistanceToMoney'] = abs(options_df_third['strike'] - stock_price)
    options_sorted_third = options_df_third.sort_values(by='DistanceToMoney')

    # Select 80 options closest to the money for the third expiration date
    options_closest_third = options_sorted_third.head(90)

    # Ensure options are sorted by strike price for smooth plotting for the third expiration date
    options_closest_sorted_by_strike_third = options_closest_third.sort_values(by='strike')

    # Calculate Gamma using Black-Scholes model for the selected options of the third expiration date
    options_df_with_gamma_third = calculate_gamma(options_closest_sorted_by_strike_third, stock_price,
                                                   days_to_expiry_third, vol)

    options_df_first_ctm = filter_options_advanced(options_df_first, stock_price)
    options_df_second_ctm = filter_options_advanced(options_df_second, stock_price)
    options_df_third_ctm = filter_options_advanced(options_df_third, stock_price)

    # Plot Gamma for all expiration dates on the same plot
    plt.figure(figsize=(18, 9), facecolor='#747474')  # Set the popup window background color to black
    ax = plt.gca()
    ax.set_facecolor('#747474')
    ax.set_title('Gamma Curve', color='lightgrey')
    ax.set_xlabel('Strike Price', color='lightgrey')
    ax.set_ylabel('Gamma', color='lightgrey')
    ax.tick_params(axis='both', colors='lightgrey')


    # Plot Gamma for the first expiration date
    plt.plot(options_df_with_gamma_first['strike'], options_df_with_gamma_first['Gamma'], '#9C9C9C', marker='o',
             markersize=4,
             linestyle='-', linewidth=2, label=f'{expiry_first.date()}, Gamma')

    # Plot Gamma for the second expiration date
    plt.plot(options_df_with_gamma_second['strike'], options_df_with_gamma_second['Gamma'], '#626262', marker='o',
             markersize=4,
             linestyle='-', linewidth=2, label=f'{expiry_second.date()}, Gamma')

    # Plot Gamma for the third expiration date
    plt.plot(options_df_with_gamma_third['strike'], options_df_with_gamma_third['Gamma'], '#2F2F2F', marker='o',
             markersize=4,
             linestyle='-', linewidth=2, label=f'{expiry_third.date()}, Gamma')

    # Apply the gradient


    # Add vertical lines at the strikes with the highest open interest for the first expiration date
    plt.axvline(x=call_max_open_interest_first['strike'], color='#9C9C9C', linestyle='--',
                label=f'Peak Open Interest {expiry_first.date()}')
    plt.axvline(x=put_max_open_interest_first['strike'], color='#9C9C9C', linestyle='--',
                label='')

    # Add vertical lines at the strikes with the highest open interest for the second expiration date
    plt.axvline(x=call_max_open_interest_second['strike'], color='#626262', linestyle='--',
                label=f'Peak Open Interest {expiry_second.date()}')
    plt.axvline(x=put_max_open_interest_second['strike'], color='#626262', linestyle='--',
                label='')

    # Add vertical lines at the strikes with the highest open interest for the third expiration date
    plt.axvline(x=call_max_open_interest_third['strike'], color='#2F2F2F', linestyle='--',
                label=f'Peak Open Interest {expiry_third.date()}')
    plt.axvline(x=put_max_open_interest_third['strike'], color='#2F2F2F', linestyle='--',
                label='')

    # Label the vertical lines with the strike value
    label_offset = 0.005  # Adjust this value to control the distance of the text from the lines
    label_properties = {'family': 'Consolas', 'color': 'black', 'weight': 'bold', 'fontsize': 8}
    for strike in [call_max_open_interest_first['strike'], put_max_open_interest_first['strike'],
                   call_max_open_interest_second['strike'], put_max_open_interest_second['strike'],
                   call_max_open_interest_third['strike'], put_max_open_interest_third['strike']]:
        plt.text(strike, label_offset, f'{strike}', verticalalignment='bottom', horizontalalignment='right',
                 **label_properties)

    # Identify the strike price with the maximum gamma value for the first expiration date
    max_gamma_strikes_first = options_df_with_gamma_first.loc[options_df_with_gamma_first['Gamma'] == options_df_with_gamma_first['Gamma'].max(), 'strike']
    max_gamma_strike_first = max_gamma_strikes_first.iloc[0]  # Select the first strike in case of ties
    max_gamma_value_first = options_df_with_gamma_first['Gamma'].max()

    # Draw a vertical line at the strike price with the maximum gamma value for the first expiration date
    plt.axvline(x=max_gamma_strike_first, color='black', linestyle='-')

    # Draw a horizontal line at the maximum gamma value for the first expiration date
    plt.axhline(y=max_gamma_value_first, color='black', linestyle='-')

    # Label the peak gamma point and its value for the first expiration date
    label_text_first = f'Peak Gamma\n@ {max_gamma_strike_first} strike\nGamma: {max_gamma_value_first:.4f}'
    font_properties = {'family': 'Consolas', 'fontsize': 8, 'color': 'black', 'weight' : 'bold'}
    plt.text(max_gamma_strike_first, max_gamma_value_first, label_text_first, verticalalignment='bottom', horizontalalignment='right',
             fontdict=font_properties)

    # Identify the strike price with the maximum gamma value for the second expiration date
    max_gamma_strikes_second = options_df_with_gamma_second.loc[options_df_with_gamma_second['Gamma'] == options_df_with_gamma_second['Gamma'].max(), 'strike']
    max_gamma_strike_second = max_gamma_strikes_second.iloc[0]  # Select the first strike in case of ties
    max_gamma_value_second = options_df_with_gamma_second['Gamma'].max()

    # Draw a vertical line at the strike price with the maximum gamma value for the second expiration date
    plt.axvline(x=max_gamma_strike_second, color='black', linestyle='-')

    # Draw a horizontal line at the maximum gamma value for the second expiration date
    plt.axhline(y=max_gamma_value_second, color='black', linestyle='-')

    # Label the peak gamma point and its value for the second expiration date
    label_text_second = f'Peak Gamma\n@ {max_gamma_strike_second} strike\nGamma: {max_gamma_value_second:.4f}'
    plt.text(max_gamma_strike_second, max_gamma_value_second, label_text_second, verticalalignment='bottom', horizontalalignment='right',
             fontdict=font_properties, font=('bold'))

    # Identify the strike price with the maximum gamma value for the third expiration date
    max_gamma_strikes_third = options_df_with_gamma_third.loc[options_df_with_gamma_third['Gamma'] == options_df_with_gamma_third['Gamma'].max(), 'strike']
    max_gamma_strike_third = max_gamma_strikes_third.iloc[0]  # Select the first strike in case of ties
    max_gamma_value_third = options_df_with_gamma_third['Gamma'].max()

    # Draw a vertical line at the strike price with the maximum gamma value for the third expiration date
    plt.axvline(x=max_gamma_strike_third, color='black', linestyle='-')

    # Draw a horizontal line at the maximum gamma value for the third expiration date
    plt.axhline(y=max_gamma_value_third, color='black', linestyle='-')

    # Label the peak gamma point and its value for the third expiration date
    label_text_third = f'Peak Gamma\n@ {max_gamma_strike_third} strike\nGamma: {max_gamma_value_third:.4f}'
    plt.text(max_gamma_strike_third, max_gamma_value_third, label_text_third, verticalalignment='bottom', horizontalalignment='right',
             fontdict=font_properties, font=('bold'))

    options_df_with_gamma_first = calculate_gamma(options_closest_sorted_by_strike_first, stock_price, days_to_expiry_first, vol)
    least_gamma_strike_first, least_gamma_value_first = find_least_gamma_strike(options_df_with_gamma_first)

    x_min, x_max = ax.get_xlim()

    add_gradient_to_axvspan(start=x_min, end=max_gamma_strike_first, color1=(1, 0, 0, 0),
                            color2=(175 / 255, 104 / 255, 104 / 255, 0.5), num_bins=100)

    add_gradient_to_axvspan(start=max_gamma_strike_first, end=x_max, color1=(135 / 255, 167 / 255, 130 / 255, 1),
                            color2=(0, 1, 0, 0), num_bins=100)

    legend = ax.legend(facecolor='darkgrey', edgecolor='lightgrey', fontsize='medium')
    plt.setp(legend.get_texts(), color='lightgrey')
    plt.grid(True, which='both', linestyle='--', linewidth=0.5, color='darkgrey')  # Adjust grid color to fit the theme




    plt.grid(True, which='both', linestyle='--', linewidth=0.5, color='darkgrey')  # Adjust grid color to fit the theme
    plt.legend()
    plt.show()



if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python gammacurve.py <ticker_symbol>")
        sys.exit(1)
    ticker_symbol = sys.argv[1].upper()
    main(ticker_symbol)