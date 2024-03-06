import tkinter as tk
from tkinter import simpledialog, messagebox
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
import yfinance as yf
from PIL import Image
from mplfinance.original_flavor import candlestick_ohlc
import sys
from matplotlib.patches import FancyArrowPatch
import matplotlib.font_manager
print(matplotlib.font_manager.findSystemFonts(fontpaths=None, fontext='ttf'))



def main3(ticker_symbol):
    period = '10d'
    interval = '1d'  # Use daily data to calculate levels
    transparent = (0.0, 0.0, 0.0, 0.0)
    ticker = yf.Ticker(ticker_symbol)
    options = ticker.option_chain()
    calls = options.calls
    puts = options.puts





    # Fetch the data
    ticker = yf.Ticker(ticker_symbol)
    df = ticker.history(period=period, interval=interval)
    df.reset_index(inplace=True)

    # Calculate session statistics (high, low, and open for each session)
    session_stats = df[['Date', 'Open', 'High', 'Low']].copy()

    # Calculate high and low differentials relative to the session open
    session_stats['high_diff'] = session_stats['High'] - session_stats['Open']
    session_stats['low_diff'] = session_stats['Open'] - session_stats['Low']

    # Define percentiles
    percentiles = [30, 50, 75, 90, 95, 99]

    # Fetch intraday data for the most recent day
    interval = '1m'  # Change to '1m' for intraday 1-minute data
    today = pd.Timestamp.now().strftime('%Y-%m-%d')  # Use today's date for fetching data
    df_intraday = ticker.history(start=today, interval=interval)
    df_intraday.reset_index(inplace=True)

    if not df_intraday.empty:
        # Use the open price of the most recent intraday session for calculations
        open_price = df_intraday['Open'].iloc[0]
    else:
        # Fallback to the open price of the most recent daily session if no intraday data is available
        open_price = df['Open'].iloc[-1]


    highest_calls = calls.sort_values(by='openInterest', ascending=False).head(2)
    highest_puts = puts.sort_values(by='openInterest', ascending=False).head(2)

    filtered_calls = calls[(calls['strike'] >= open_price - 5) & (calls['strike'] <= open_price + 5)]
    filtered_puts = puts[(puts['strike'] >= open_price - 5) & (puts['strike'] <= open_price + 5)]

    highest_call_oi = filtered_calls.loc[filtered_calls['openInterest'].idxmax()]
    highest_put_oi = filtered_puts.loc[filtered_puts['openInterest'].idxmax()]

    # Prepare data for candlestick plot
    ohlc = df_intraday[['Datetime', 'Open', 'High', 'Low', 'Close']].copy()
    ohlc['Datetime'] = ohlc['Datetime'].map(mdates.date2num)

    # Plotting setup
    plt.figure(figsize=(18, 9), facecolor='#747474')
    ax = plt.gca()
    ax.set_facecolor('#747474')
    ax.set_title(f"1m Chart for {ticker_symbol} with Levels", color='lightgrey')
    ax.set_xlabel('Time', color='lightgrey')
    ax.set_ylabel('Price', color='lightgrey')
    ax.tick_params(axis='both', colors='lightgrey')

    # Calculate, plot high and low levels, and annotate their values with the offset
    for i, p in enumerate(percentiles, start=1):
        linestyle = '-' if p == 30 else ':'

        # High levels
        high_level = open_price + np.percentile(session_stats['high_diff'], p)
        ax.axhline(y=high_level, color='black', linestyle=linestyle, linewidth=1)
        ax.text(df_intraday['Datetime'].max(), high_level, f'{high_level:.2f}', verticalalignment='center',
                horizontalalignment='center', color='darkgrey', fontsize=8)

        # Low levels
        low_level = open_price - np.percentile(session_stats['low_diff'], p)
        ax.axhline(y=low_level, color='black', linestyle=linestyle, linewidth=1)
        ax.text(df_intraday['Datetime'].max(), low_level, f'{low_level:.2f}', verticalalignment='center',
                horizontalalignment='center', color='darkgrey', fontsize=8)






    # Calculate the first two high and low 30 percent deviation levels
    high_level_30_1 = open_price + np.percentile(session_stats['high_diff'], 30)
    low_level_30_1 = open_price - np.percentile(session_stats['low_diff'], 30)

    # Coordinates for the arrow
    arrow_start = (mdates.date2num(df_intraday['Datetime'].max()), high_level_30_1)
    arrow_end = (mdates.date2num(df_intraday['Datetime'].max()), low_level_30_1)

    # Create and add the arrow to the plot
    arrow = FancyArrowPatch(arrow_start, arrow_end, connectionstyle="arc3,rad=-.02", color="black", lw=1,
                            arrowstyle="<|-|>", mutation_scale=8)
    ax.add_patch(arrow)
    label_text = "Minimum Expected\nVolatility"

    # Add a label to the arrow
    label_x = (arrow_start[0] + arrow_end[0]) / 2
    label_y = (arrow_start[1] + arrow_end[1]) / 2
    ax.text(label_x, label_y, label_text, horizontalalignment='left', verticalalignment='bottom', color='black',
            fontsize=8, fontname='Courier New')




    high_level_50 = open_price + np.percentile(session_stats['high_diff'], 50)
    high_level_75 = open_price + np.percentile(session_stats['high_diff'], 75)
    low_level_50 = open_price - np.percentile(session_stats['low_diff'], 50)
    low_level_75 = open_price - np.percentile(session_stats['low_diff'], 75)
    high_level_95 = open_price + np.percentile(session_stats['high_diff'], 95)
    low_level_95 = open_price - np.percentile(session_stats['low_diff'], 95)
    high_level_90 = open_price + np.percentile(session_stats['high_diff'], 90)
    low_level_90 = open_price - np.percentile(session_stats['low_diff'], 90)
    high_level_99 = open_price + np.percentile(session_stats['high_diff'], 99)
    low_level_99 = open_price - np.percentile(session_stats['low_diff'], 99)



    ax.axhline(y=high_level_95, color='black', linestyle='--', linewidth=1)
    ax.axhline(y=low_level_95, color='black', linestyle='--', linewidth=1)

    # Fill between the second and third levels on the upside
    ax.fill_between(df_intraday['Datetime'], high_level_50, high_level_75, color='blue', alpha=0.3)

    # Fill between the second and third levels on the downside
    ax.fill_between(df_intraday['Datetime'], low_level_50, low_level_75, color='purple', alpha=0.3)
    ax.fill_between(df_intraday['Datetime'], high_level_90, high_level_95, color='darkgrey', alpha=0.3)
    ax.fill_between(df_intraday['Datetime'], low_level_90, low_level_95, color='darkgrey', alpha=0.3)

    # Calculate the midpoints for the labels
    label_x = df_intraday['Datetime'].median()
    label_y_high = (high_level_50 + high_level_75) / 2
    label_y_low = (low_level_50 + low_level_75) / 2







    # Coordinates for the arrow
    arrow_start2 = (mdates.date2num(df_intraday['Datetime'].min()), high_level_99)
    arrow_end2 = (mdates.date2num(df_intraday['Datetime'].min()), low_level_99)

    # Create and add the arrow to the plot
    arrow2 = FancyArrowPatch(arrow_start2, arrow_end2, connectionstyle="arc3,rad=0", color="black", lw=1,
                             arrowstyle="<|-|>", mutation_scale=15)
    ax.add_patch(arrow2)
    label_text2 = "Maximum Volatility"

    # Add a label to the arrow
    label_x2 = (arrow_start2[0] + arrow_end2[0]) / 2
    label_y2 = (arrow_start2[1] + arrow_end2[1]) / 2
    ax.text(label_x2, label_y2, label_text2, horizontalalignment='left', verticalalignment='bottom', color='black',
            fontsize=8, fontname='Courier New')














    # Add labels to the boxes
    ax.text(label_x, label_y_high, 'Expected Unfolding Volatility', horizontalalignment='center',
            verticalalignment='center', color='white', fontsize=8, fontname='Courier New',
            bbox=dict(facecolor='green', alpha=0.4))
    ax.text(label_x, label_y_low, 'Expected Unfolding Volatility', horizontalalignment='center',
            verticalalignment='center', color='white', fontsize=8, fontname='Courier New',
            bbox=dict(facecolor='red', alpha=0.4))




    label_y_high_95 = high_level_95 + (high_level_95 - high_level_90) * 1.2
    label_y_low_95 = low_level_95 - (low_level_90 - low_level_95) * 0.5
    ax.text(label_x, label_y_high_95, 'Expected Volatility Ceiling', horizontalalignment='center',
            verticalalignment='center', color='white', fontsize=6, fontname='Courier New',
            bbox=dict(facecolor='#747474', alpha=0.5))
    ax.text(label_x, label_y_low_95, 'Expected Volatility Floor', horizontalalignment='center',
            verticalalignment='center', color='white', fontsize=6, fontname='Courier New',
            bbox=dict(facecolor='#747474', alpha=0.5))









    top_2_calls_within_5 = filtered_calls.nlargest(2, 'openInterest')
    top_2_puts_within_5 = filtered_puts.nlargest(2, 'openInterest')

    highest_call_oi_within_5 = filtered_calls.loc[filtered_calls['openInterest'].idxmax()]
    highest_put_oi_within_5 = filtered_puts.loc[filtered_puts['openInterest'].idxmax()]

    for idx, row in top_2_calls_within_5.iterrows():
        ax.axhline(y=row['strike'], color='orange', linestyle=':', linewidth=1,
                   label=f'Call Interest Target: {row["strike"]}')

    for idx, row in top_2_puts_within_5.iterrows():
        ax.axhline(y=row['strike'], color='orange', linestyle=':', linewidth=1,
                   label=f'Put Interest Target: {row["strike"]}')







    # Plot the candlestick chart
    current_price = df_intraday['Close'].iloc[-1]
    ax.axhline(y=current_price, color='#029100', linestyle='-', linewidth=1, label='Current Price')
    yesterday_close = df['Close'].iloc[-2]
    ax.axhline(y=yesterday_close, color='#300056', linestyle='-.', linewidth=1, label=f"Yesterday's Close {yesterday_close}", alpha=0.5)
    ax.axhline(y=open_price, color='#273575', linestyle='--', linewidth=1, label=f'Open Price {open_price}', alpha=0.5)
    candlestick_ohlc(ax, ohlc.values, width=0.00000000005, colorup='#747474', colordown='#747474', alpha=0.005)

    # Continue with your plotting logic...
    length = 20

    # Calculate the Upper Band, Lower Band, and LB Line
    UpperBand = df_intraday['Close'].rolling(window=length).max()
    LowerBand = df_intraday['Low'].rolling(window=length).min()
    LB = LowerBand.rolling(window=length).max()

    # Plot the Vector (LB Line)
    #ax.plot(df_intraday['Datetime'], LB, label='LB Line (Vector)', color='purple', linewidth=1, linestyle='-')

    # Continue with the rest of your plotting logic including the logo
    # Load your logo image and plot as before

    #LB_filled = LB.fillna(method='bfill')




    # Load your logo image
    logo_path = "C:\\Users\\maxhe\\Downloads\\nuclei.png"
    logo = Image.open(logo_path)
    zoom = 0.25  # Adjust zoom level to scale your logo's size on the plot

    # Define the bounding box for the inset axes [x, y, width, height]
    # Adjust these values to place and scale the logo as needed
    bbox_props = dict(boxstyle="square,pad=0.3", fc="white", ec="b", lw=2)
    logo_box = OffsetImage(logo, zoom=zoom)
    logo_box.image.axes = ax
    ab = AnnotationBbox(logo_box, (0.06, 0.932), xycoords='axes fraction', frameon=False)

    ax.add_artist(ab)

    ax.set_ylabel('Price')
    ax.legend()

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python gammacurve.py <ticker_symbol>")
        sys.exit(1)
    ticker_symbol = sys.argv[1].upper()
    main3(ticker_symbol)
