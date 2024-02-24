"""
TO DO LIST:

☐ Diversify functions into their own scripts to be called and debloat main.py
☐ FIX "DISPLAY CHART" BUTTON
☐ Bring over screeners
☐ Bring over Gamma curve chart and add volatility line
☐ Create refresh feature to re-derive data
☐


"""


####################################################################################################################
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
import yfinance as yf
import mibian
import pandas as pd
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QSizePolicy, QSpacerItem, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView, QLabel
from PyQt5.QtCore import Qt
import matplotlib.pyplot as plt
from PyQt5.QtGui import QPixmap
import pyrdp
import subprocess
import tkinter
from gammacurve import main
from openinterest import main1

''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
####################################################################################################################





# Function to get options data for a specific symbol
def get_options_data(symbol):
    stock = yf.Ticker(symbol)
    expirations = stock.options
    options_data = {}

    for expiry in expirations:
        options_chain = stock.option_chain(expiry)
        options_data[expiry] = {'calls': options_chain.calls, 'puts': options_chain.puts}  # Collect both calls and puts

    return options_data

# Function to calculate option Greeks
def calculate_option_greeks(options_data, stock_price, risk_free_rate):
    greeks_data = []
    for expiry, chains in options_data.items():
        for option_type, chain in chains.items():  # Iterate over both calls and puts
            for _, option in chain.iterrows():
                try:
                    underlying_price = stock_price
                    strike_price = option['strike']
                    time_to_expiry = max((pd.to_datetime(expiry) - pd.Timestamp.now()).days / 365.0, 0.001)
                    implied_volatility = option['impliedVolatility']

                    if implied_volatility is None or strike_price is None:
                        print(f"Skipping {option['contractSymbol']} due to None values")
                        continue

                    # Calculate Greeks using mibian.BS
                    option_obj = mibian.BS([underlying_price, strike_price, risk_free_rate, time_to_expiry * 365], volatility=implied_volatility * 100.0)

                    delta = option_obj.callDelta if option_type == 'calls' else option_obj.putDelta
                    theta = option_obj.callTheta if option_type == 'calls' else option_obj.putTheta
                    vega = option_obj.vega
                    gamma = option_obj.gamma
                    rho = option_obj.callRho if option_type == 'calls' else option_obj.putRho

                    # Adjust gamma based on the type of option

                    greeks_data.append([option['contractSymbol'], expiry, delta, theta, vega, gamma, rho,
                                        option['lastPrice'], option['openInterest'], option['volume'],
                                        option['bid'], option['ask'], option['change'], option['percentChange']])

                except Exception as e:
                    print(f"Error calculating Greeks for {option['contractSymbol']} - {str(e)}")

    return greeks_data



####################################################################################################################
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
# Calculates and plots the gamma exposure on a matplotlib chart. This is the functino that is called when the
# "Display Chart" button is. It then attempts to output a GEX bar chart.
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
####################################################################################################################


"""
def calculate_and_plot_gamma_exposure(df, fromStrike, toStrike, spotPrice):
    df_copy = df.copy()


    calls = df_copy[df_copy['Type'] == 'call'].copy()
    puts = df_copy[df_copy['Type'] == 'put'].copy()

    calls['GEX'] = calls['Gamma'] * calls['OpenInterest'] * 100 * spotPrice * spotPrice * 0.01
    puts['GEX'] = puts['Gamma'] * puts['OpenInterest'] * 100 * spotPrice * spotPrice * 0.01 * -1

    combined_df = pd.concat([calls, puts])

    combined_df['TotalGamma'] = combined_df['GEX']
    dfAgg = combined_df.groupby('StrikePrice')['TotalGamma'].sum()

    # Plotting
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.set_facecolor('#797979')
    fig.patch.set_facecolor('#3D3D3D')
    ax.grid(True, which='both', axis='y', linestyle='--', linewidth=0.5, color='gray')

    ax.bar(dfAgg.index, dfAgg / 10 ** 9, width=0.5, edgecolor='k', label="Gamma Exposure")

    ax.set_xlim([fromStrike, toStrike])

    chartTitle = "Total Gamma Exposure: $" + str("{:.2f}".format(dfAgg.sum() / 10 ** 9)) + " Bn per 1% SPY Move"
    ax.set_title(chartTitle, fontweight="bold", fontsize=20, color='white')
    ax.set_xlabel('Strike Price', fontweight="bold", color='white')
    ax.set_ylabel('Spot Gamma Exposure ($ billions/1% move)', fontweight="bold", color='white')

    ax.axvline(x=spotPrice, color='r', lw=2, label=f"Spot Price: ${spotPrice:,.0f}")

    ax.tick_params(axis='x', colors='white')
    ax.tick_params(axis='y', colors='white')

    legend = ax.legend()
    plt.setp(legend.get_texts(), color='white')

    plt.tight_layout()
    plt.show()

"""






####################################################################################################################
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
# User input for their desired symbol. Also pulls the greek calculation function and runs it with the provided data.
''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
####################################################################################################################



def submit():
    print("Submit function called")
    symbol = line_edit.text().upper()
    text_edit.append(f'Stock ticker: {symbol}\n')
    print(f"Symbol: {symbol}")

    stock = yf.Ticker(symbol)
    stock_info = stock.history(period="1d")

    if not stock_info.empty:
        stock_price = stock_info['Close'].iloc[-1]
        text_edit.append(f"Current stock price: {stock_price}\n")

        options_data = get_options_data(symbol)
        if options_data:
            risk_free_rate = 0.02
            greeks_data = calculate_option_greeks(options_data, stock_price, risk_free_rate)

            table.setRowCount(0)
            for row_data in greeks_data:
                row_number = table.rowCount()
                table.insertRow(row_number)
                for column_number, data in enumerate(row_data):
                    if column_number == 5:  # Adjust index based Gamma column
                        table.setItem(row_number, column_number, QTableWidgetItem(f"{data:.10f}"))
                    else:
                        table.setItem(row_number, column_number, QTableWidgetItem(str(data)))
            text_edit.append("Data fetched and displayed.\n")
            display_chart_button.show()
            text_edit.append("Data fetched and displayed.\n")
            display_chart_button2.show()
        else:
            text_edit.append(f"No valid option data for {symbol}\n")
            display_chart_button.hide(),
            text_edit.append("Data fetched and displayed.\n")
            display_chart_button2.hide()
    else:
        text_edit.append(f"No current stock price data available for {symbol}\n")

####################################
''''''''''''''''''''''''''''''''''''
# to create app
''''''''''''''''''''''''''''''''''''
####################################

import sys
import os

def resource_path(relative_path):
    """ Get the absolute path to the resource, works for development and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


    gammacurve.some_function()
    vwapscreener.some_variable = None


####################################
''''''''''''''''''''''''''''''''''''
# Plots the gamma curve
''''''''''''''''''''''''''''''''''''
####################################



def displayGammaCurve():
    ticker_symbol = line_edit.text().strip()
    if ticker_symbol:
        try:
            main(ticker_symbol)
        except Exception as e:
            print(f"Unexpected error: {e}")
    else:
        print("Please enter a ticker symbol.")


####################################
''''''''''''''''''''''''''''''''''''
# Plots the Open interest in a negative and positive histogram format
''''''''''''''''''''''''''''''''''''
####################################



def displayOI():
    ticker_symbol = line_edit.text().strip()
    if ticker_symbol:
        try:
            main1(ticker_symbol)
        except Exception as e:
            print(f"Unexpected error: {e}")
    else:
        print("Please enter a ticker symbol.")




####################################
''''''''''''''''''''''''''''''''''''
# Displays Screeners
''''''''''''''''''''''''''''''''''''
####################################




import subprocess

def run_screener(self):
    try:
        subprocess.run([sys.executable, "vwapscreener.py"], check=True)
        print("VWAP screener script completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error running VWAP screener script: {e}")





####################################
''''''''''''''''''''''''''''''''''''
# QT UI Styling
''''''''''''''''''''''''''''''''''''
####################################

app = QApplication([])
stylesheet ="""QToolTip
{
     border: 2px solid #121212;
     background-color: #ffb13f;
     padding: 2px;
     border-radius: 4px;
     opacity: 100;
}

QWidget
{
    color: #c1c1c1;
    background-color: #333333;
}

QTreeView, QListView
{
    background-color: #b0b0b0;
    margin-left: 6px;
}

QWidget:item:hover
{
    background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #7D7D7D, stop: 1 #787878);
    color: #ABABAB;
}

QWidget:item:selected
{
    background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #C8C8C8, stop: 1 #C8C8C8);
}

QMenuBar::item
{
    background: transparent;
}

QMenuBar::item:selected
{
    background: transparent;
    border: 2px solid #5BBA46;
}

QMenuBar::item:pressed
{
    background: #555;
    border: 2px solid #111;
    background-color: QLinearGradient(
        x1:0, y1:0,
        x2:0, y2:1,
        stop:1 #313131,
        stop:0.5 #444444
    );
    margin-bottom:-2px;
    padding-bottom:2px;
}

QMenu
{
    border: 2px solid #111;
}

QMenu::item
{
    padding: 3px 21px 3px 21px;
}

QMenu::item:selected
{
    color: #010101;
}

QWidget:disabled
{
    color: #909090;
    background-color: #333333;
}

QAbstractItemView
{
    background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #5e5e5e, stop: 0.1 #757575, stop: 1 #6e6e6e);
}

QWidget:focus
{
    /*border: 2px solid gray;*/
}

QLineEdit
{
    background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #5e5e5e, stop: 0 #757575, stop: 1 #6e6e6e);
    padding: 2px;
    border-style: solid;
    border: 2px solid #2f2f2f;
    border-radius: 6;
}

QPushButton
{
    color: #c1c1c1;
    background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #676767, stop: 0.1 #636363, stop: 0.5 #5f5f5f, stop: 0.9 #5b5b5b, stop: 1 #575757);
    border-width: 2px;
    border-color: #2f2f2f;
    border-style: solid;
    border-radius: 7;
    padding: 4px;
    font-size: 13px;
    padding-left: 6px;
    padding-right: 6px;
    min-width: 41px;
}

QPushButton:pressed
{
    background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #3e3e3e, stop: 0.1 #3c3c3c, stop: 0.5 #393939, stop: 0.9 #383838, stop: 1 #363636);
}

QComboBox
{
    selection-background-color: #A2A2A2;
    background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #519449, stop: 0.1 #579E4E, stop: 0.5 #5FA556, stop: 0.9 #68AE5F, stop: 1 #6EB365);
    border-style: solid;
    border: 2px solid #2f2f2f;
    border-radius: 6;
}

QComboBox:hover,QPushButton:hover
{
    border: 1px solid QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #A2A2A2, stop: 1 #A2A2A2);
}

QComboBox:on
{
    padding-top: 4px;
    padding-left: 5px;
    background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #3e3e3e, stop: 0.1 #3c3c3c, stop: 0.5 #393939, stop: 0.9 #383838, stop: 1 #363636);
    selection-background-color: #A2A2A2;
}

QComboBox QAbstractItemView
{
    border: 3px solid gray;
    selection-background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #ffb13f, stop: 1 #d88a1b);
}

QComboBox::drop-down
{
     subcontrol-origin: padding;
     subcontrol-position: top right;
     width: 16px;

     border-left-width: 0px;
     border-left-color: gray;
     border-left-style: solid; /* just a single line */
     border-top-right-radius: 4px; /* same radius as the QComboBox */
     border-bottom-right-radius: 4px;
 }

QComboBox::down-arrow
{
     image: url(:/dark_orange/img/down_arrow.png);
}

QGroupBox
{
    border: 2px solid gray;
    margin-top: 11px;
}

QGroupBox:focus
{
    border: 2px solid gray;
}

QTextEdit:focus
{
    border: 2px solid gray;
}

QScrollBar:horizontal {
     border: 2px solid #333333;
     background: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0.0 #232323, stop: 0.2 #393939, stop: 1 #595959);
     height: 8px;
     margin: 0px 17px 0 17px;
}

QScrollBar::handle:horizontal
{
      background: QLinearGradient( x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #ffb13f, stop: 0.5 #d88a1b, stop: 1 #ffb13f);
      min-height: 21px;
      border-radius: 3px;
}

QScrollBar::add-line:horizontal {
      border: 2px solid #2b2b2b;
      border-radius: 3px;
      background: QLinearGradient( x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #ffb13f, stop: 1 #d88a1b);
      width: 15px;
      subcontrol-position: right;
      subcontrol-origin: margin;
}

QScrollBar::sub-line:horizontal {
      border: 2px solid #2b2b2b;
      border-radius: 3px;
      background: QLinearGradient( x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #ffb13f, stop: 1 #d88a1b);
      width: 15px;
     subcontrol-position: left;
     subcontrol-origin: margin;
}

QScrollBar::right-arrow:horizontal, QScrollBar::left-arrow:horizontal
{
      border: 2px solid black;
      width: 2px;
      height: 2px;
      background: #f0f0f0;
}

QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal
{
      background: none;
}

QScrollBar:vertical
{
      background: QLinearGradient( x1: 0, y1: 0, x2: 1, y2: 0, stop: 0.0 #5D5D5D, stop: 0.2 #717171, stop: 1 #7F7F7F);
      width: 8px;
      margin: 17px 0 17px 0;
      border: 2px solid #333333;
}

QScrollBar::handle:vertical
{
      background: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #EAEAEA, stop: 0.5 #EAEAEA, stop: 1 #EAEAEA);
      min-height: 21px;
      border-radius: 3px;
}

QScrollBar::add-line:vertical
{
      border: 2px solid #2b2b2b;
      border-radius: 3px;
      background: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #CACACA, stop: 1 #ACACAC);
      height: 15px;
      subcontrol-position: bottom;
      subcontrol-origin: margin;
}

QScrollBar::sub-line:vertical
{
      border: 2px solid #2b2b2b;
      border-radius: 3px;
      background: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #CACACA, stop: 1 #ACACAC);
      height: 15px;
      subcontrol-position: top;
      subcontrol-origin: margin;
}

QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical
{
      border: 2px solid black;
      width: 2px;
      height: 2px;
      background: #f0f0f0;
}


QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical
{
      background: none;
}

QTextEdit
{
    background-color: #353535;
}

QPlainTextEdit
{
    background-color: #353535;
}

QHeaderView::section
{
    background-color: QLinearGradient(x1:0, y1:0, x2:0, y2:1, stop:0 #5EAB54, stop: 0.5 #559E4B, stop: 0.6 #509546, stop:0.7 #4D9044, stop:1 #45823C);
    color: #ACAAAA;
    padding-left: 5px;
    border: 2px solid #7c7c7c;
}

QCheckBox:disabled
{
color: #515151;
}

QDockWidget::title
{
    text-align: center;
    spacing: 4px; /* spacing between items in the tool bar */
    background-color: QLinearGradient(x1:0, y1:0, x2:0, y2:1, stop:0 #434343, stop: 0.5 #343434, stop:1 #434343);
}

QDockWidget::close-button, QDockWidget::float-button
{
    text-align: center;
    spacing: 2px; /* spacing between items in the tool bar */
    background-color: QLinearGradient(x1:0, y1:0, x2:0, y2:1, stop:0 #434343, stop: 0.5 #343434, stop:1 #434343);
}

QDockWidget::close-button:hover, QDockWidget::float-button:hover
{
    background: #5DB64F;
}

QDockWidget::close-button:pressed, QDockWidget::float-button:pressed
{
    padding: 2px -2px -2px 2px;
}

QMainWindow::separator
{
    background-color: QLinearGradient(x1:0, y1:0, x2:0, y2:1, stop:0 #262626, stop: 0.5 #252525, stop: 0.6 #313131, stop:1 #444444);
    color: #f0f0f0;
    padding-left: 5px;
    border: 2px solid #5c5c5c;
    spacing: 4px; /* spacing between items in the tool bar */
}

QMainWindow::separator:hover
{

    background-color: QLinearGradient(x1:0, y1:0, x2:0, y2:1, stop:0 #d88a1b, stop:0.5 #c46d17 stop:1 #ffb13f);
    color: #f0f0f0;
    padding-left: 5px;
    border: 2px solid #7c7c7c;
    spacing: 4px; /* spacing between items in the tool bar */
}

QToolBar::handle
{
     spacing: 4px; /* spacing between items in the tool bar */
     background: url(:/dark_orange/img/handle.png);
}

QMenu::separator
{
    height: 3px;
    background-color: QLinearGradient(x1:0, y1:0, x2:0, y2:1, stop:0 #262626, stop: 0.5 #252525, stop: 0.6 #313131, stop:1 #444444);
    color: #f0f0f0;
    padding-left: 5px;
    margin-left: 11px;
    margin-right: 6px;
}

QProgressBar
{
    border: 3px solid #808080;
    border-radius: 6px;
    text-align: center;
}

QProgressBar::chunk
{
    background-color: #d88a1b;
    width: 2.35px;
    margin: 0.55px;
}

QTabBar::tab {
    color: #c2c2c2;
    border: 2px solid #555;
    border-bottom-style: none;
    background-color: #434343;
    padding-left: 11px;
    padding-right: 11px;
    padding-top: 4px;
    padding-bottom: 3px;
    margin-right: -2px;
}

QTabWidget::pane {
    border: 2px solid #555;
    top: 2px;
}

QTabBar::tab:last
{
    margin-right: 0; /* the last selected tab has nothing to overlap with on the right */
    border-top-right-radius: 4px;
}

QTabBar::tab:first:!selected
{
 margin-left: 0px; /* the last selected tab has nothing to overlap with on the right */


    border-top-left-radius: 4px;
}

QTabBar::tab:!selected
{
    color: #c2c2c2;
    border-bottom-style: solid;
    margin-top: 4px;
    background-color: QLinearGradient(x1:0, y1:0, x2:0, y2:1, stop:1 #313131, stop:.4 #444444);
}

QTabBar::tab:selected
{
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    margin-bottom: 0px;
}

QTabBar::tab:!selected:hover
{
    /*border-top: 2px solid #ffaa00;
    padding-bottom: 3px;*/
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    background-color: QLinearGradient(x1:0, y1:0, x2:0, y2:1, stop:1 #313131, stop:0.4 #444444, stop:0.2 #444444, stop:0.1 #D93636);
}

QRadioButton::indicator:checked, QRadioButton::indicator:unchecked{
    color: #c2c2c2;
    background-color: #434343;
    border: 2px solid #c2c2c2;
    border-radius: 7px;
}

QRadioButton::indicator:checked
{
    background-color: qradialgradient(
        cx: 0.5, cy: 0.5,
        fx: 0.5, fy: 0.5,
        radius: 1.0,
        stop: 0.25 #D93636,
        stop: 0.3 #434343
    );
}

QCheckBox::indicator{
    color: #c2c2c2;
    background-color: #434343;
    border: 2px solid #c2c2c2;
    width: 10px;
    height: 10px;
}

QRadioButton::indicator
{
    border-radius: 7px;
}

QRadioButton::indicator:hover, QCheckBox::indicator:hover
{
    border: 2px solid #D94C42;
}

QCheckBox::indicator:checked
{
    image:url(:/dark_orange/img/checkbox.png);
}

QCheckBox::indicator:disabled, QRadioButton::indicator:disabled
{
    border: 2px solid #7E7E7E;
}


QSlider::groove:horizontal {
    border: 2px solid #4A4949;
    height: 9px;
    background: #302F2F;
    margin: 3px 0;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1,
      stop: 0.0 #b0b0b0, stop: 0.2 #b8b8b8, stop: 1 #888888);
    border: 2px solid #4A4949;
    width: 15px;
    height: 15px;
    margin: -5px 0;
    border-radius: 3px;
}

QSlider::groove:vertical {
    border: 2px solid #4A4949;
    width: 9px;
    background: #302F2F;
    margin: 0 3px;
    border-radius: 3px;
}

QSlider::handle:vertical {
    background: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0.0 #b0b0b0,
      stop: 0.2 #b8b8b8, stop: 1 #888888);
    border: 2px solid #4A4949;
    width: 15px;
    height: 15px;
    margin: 0 -5px;
    border-radius: 3px;
}

QAbstractSpinBox {
    padding-top: 3px;
    padding-bottom: 3px;
    border: 2px solid #808080;

    border-radius: 3px;
    min-width: 55px;
}"""



####################################
''''''''''''''''''''''''''''''''''''
# Section to Run and format the UI
''''''''''''''''''''''''''''''''''''
####################################


app.setStyleSheet(stylesheet)



####################################
''''''''''''''''''''''''''''''''''''
# Used for debugging
''''''''''''''''''''''''''''''''''''
####################################

def plot_simple_chart():
    plt.ion()  # Interactive mode on
    plt.figure(figsize=(10, 6))
    plt.plot([1, 2, 3, 4], [1, 4, 9, 16])  # Simple plot
    plt.title('Simple Chart')
    plt.xlabel('X-axis')
    plt.ylabel('Y-axis')
    plt.draw()  # Use draw for non-blocking plot
    plt.pause(0.001)  # Pause to ensure the plot is drawn
    plt.ioff()  # Optional: Turn interactive mode off if you don't need it elsewhere



####################################
''''''''''''''''''''''''''''''''''''
# Global
''''''''''''''''''''''''''''''''''''
####################################




window = QWidget()
window.setWindowTitle("Nuclei Analysis System - Copyright © Max Heltzel 2024, All Rights Reserved. Build 2.19.24")
main_layout = QVBoxLayout()
#main_layout.setSizeConstraint(QVBoxLayout.SetMaximumSize)
window.setLayout(main_layout)
window.showMaximized()




spacer1 = QHBoxLayout()
spacer1.addItem(QSpacerItem(20, 10, QSizePolicy.Expanding, QSizePolicy.Minimum))
main_layout.addLayout(spacer1)


image_path = resource_path('assets/connect.png')
pixmap = QPixmap(image_path)





pixmap = pixmap.scaled(230, 34)
image_label = QLabel()
image_label.setPixmap(pixmap)
image_label.setAlignment(Qt.AlignCenter)



button_layout_screener = QHBoxLayout()
button_layout_screener.addItem(QSpacerItem(20, 10, QSizePolicy.Expanding, QSizePolicy.Minimum))
button = QPushButton("Run Screeners")
button.clicked.connect(run_screener)  # Note: 'self' is removed since it's not needed here
button.setDefault(True)
button_layout_screener.addWidget(button)
button_layout_screener.addItem(QSpacerItem(20, 10, QSizePolicy.Expanding, QSizePolicy.Minimum))
main_layout.addLayout(button_layout_screener)


main_layout.addWidget(image_label)


line_edit_layout = QHBoxLayout()
line_edit_layout.addItem(QSpacerItem(20, 10, QSizePolicy.Expanding, QSizePolicy.Minimum))
line_edit = QLineEdit()
line_edit.textChanged.connect(lambda: line_edit.setText(line_edit.text().upper()))  # Convert input to uppercase as it's typed
line_edit.setFixedWidth(150)
line_edit.setFixedWidth(250)
line_edit.setFixedHeight(35)
line_edit_layout.addWidget(line_edit)
line_edit_layout.addItem(QSpacerItem(20, 10, QSizePolicy.Expanding, QSizePolicy.Minimum))
main_layout.addLayout(line_edit_layout)

font = line_edit.font()
font.setPointSize(14)
line_edit.setFont(font)

button_layout = QHBoxLayout()
button_layout.addItem(QSpacerItem(20, 10, QSizePolicy.Expanding, QSizePolicy.Minimum))
button = QPushButton("Fetch Options Data")
button.clicked.connect(submit)
button.setDefault(True)
button_layout.addWidget(button)
button_layout.addItem(QSpacerItem(20, 10, QSizePolicy.Expanding, QSizePolicy.Minimum))
main_layout.addLayout(button_layout)


text_edit = QTextEdit()
text_edit.setReadOnly(True)
text_edit.setMaximumHeight(100)
main_layout.addWidget(text_edit)


table = QTableWidget(0, 14)
table.setHorizontalHeaderLabels(['Contract Symbol', 'Expiry', 'Delta', 'Theta', 'Vega', 'Gamma', 'Rho', 'Last Price', 'Open Interest', 'Volume', 'Bid', 'Ask', 'Change', 'Percent Change'])
table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
main_layout.addWidget(table)


display_chart_button = QPushButton("Display Gamma Curve")
display_chart_button.clicked.connect(displayGammaCurve)
display_chart_button.hide()
main_layout.addWidget(display_chart_button)

display_chart_button2 = QPushButton("Open Interest by Strike")
display_chart_button2.clicked.connect(displayOI)
display_chart_button2.hide()
main_layout.addWidget(display_chart_button2)





window.setLayout(main_layout)
sys.exit(app.exec_())

