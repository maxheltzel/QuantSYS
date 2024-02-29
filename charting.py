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

"""
def get_ticker_symbol():
    root = tk.Tk()
    root.geometry("1000x500")  # Set initial window size
    root.title("Enter Ticker Symbol")

    label = tk.Label(root, text="Enter the ticker symbol:")
    label.pack()

    entry = tk.Entry(root)
    entry.pack()

    def on_submit():
        ticker_symbol = entry.get().upper()
        if ticker_symbol:
            root.destroy()  # Close the input window
            main(ticker_symbol)  # Call main function after successful submission
        else:
            messagebox.showwarning("Warning", "Please enter a valid ticker symbol.")

    button = tk.Button(root, text="Submit", command=on_submit)
    button.pack()

    root.mainloop()
"""

def main3(ticker_symbol):
    period = '10d'
    interval = '1d'  # Use daily data to calculate levels

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
    percentiles = [30, 50, 75, 90]

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

    # Prepare data for candlestick plot
    ohlc = df_intraday[['Datetime', 'Open', 'High', 'Low', 'Close']].copy()
    ohlc['Datetime'] = ohlc['Datetime'].map(mdates.date2num)

    # Plotting setup
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_title(f"1m Chart for {ticker_symbol} with Levels")

    # Calculate, plot high and low levels, and annotate their values with the offset
    for i, p in enumerate(percentiles, start=1):
        linestyle = '-' if p == 30 else ':'

        # High levels
        high_level = open_price + np.percentile(session_stats['high_diff'], p)
        ax.axhline(y=high_level, color='green', linestyle=linestyle, linewidth=1)
        ax.text(df_intraday['Datetime'].max(), high_level, f'{high_level:.2f}', verticalalignment='center',
                horizontalalignment='right', color='green', fontsize=8)

        # Low levels
        low_level = open_price - np.percentile(session_stats['low_diff'], p)
        ax.axhline(y=low_level, color='red', linestyle=linestyle, linewidth=1)
        ax.text(df_intraday['Datetime'].max(), low_level, f'{low_level:.2f}', verticalalignment='center',
                horizontalalignment='right', color='red', fontsize=8)

    # Plot the candlestick chart
    candlestick_ohlc(ax, ohlc.values, width=0.0005, colorup='g', colordown='r', alpha=0.75)


    # Continue with your plotting logic...
    length = 20

    # Calculate the Upper Band, Lower Band, and LB Line
    UpperBand = df_intraday['Close'].rolling(window=length).max()
    LowerBand = df_intraday['Low'].rolling(window=length).min()
    LB = LowerBand.rolling(window=length).max()

    # Plot the Vector (LB Line)
    ax.plot(df_intraday['Datetime'], LB, label='LB Line (Vector)', color='purple', linewidth=1, linestyle='-')

    # Continue with the rest of your plotting logic including the logo
    # Load your logo image and plot as before

    LB_filled = LB.fillna(method='bfill')

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
