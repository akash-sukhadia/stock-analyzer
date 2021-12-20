# -*- coding: utf-8 -*-
"""
Created on Mon Dec 20 11:57:49 2021

@author: HP
"""

import pandas as pd
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import talib
import matplotlib.pyplot as plt
from mplfinance.original_flavor import candlestick_ohlc
from matplotlib.pylab import date2num
import yfinance as yf
import dash
import dash_table
import numpy as np


def isBuyMACD(data):
     # Bullish SMA Crossover
    if (getLast(data, 'sma_test') == 1):
        # Bullish MACD
        if (getLast(data, 'macd_test') == 1):
            return True
        
    return False   
        
def isBuySTOCH(data):

    # # Bullish Stochastics
    if(getLast(data, 'stoch_over_sold') == 1):
         return True
    return False  

def isBuyRSI(data):
    # # Bullish RSI
    if(getLast(data, 'rsi_over_sold') == 1):
         return True
    return False 

def isSellMACD(data):
    # Bearish SMA Crossover
    if (getLast(data, 'sma_test') == 0):
        # Bearish MACD
        if (getLast(data, 'macd_test') == 0):
            return True
    return False     

def isSellSTOCH(data):
    # # Bearish Stochastics
    if(getLast(data, 'stoch_over_bought') == 0):
         return True
    return False 

def isSellRSI(data):
    # # Bearish RSI
    if(getLast(data, 'rsi_over_bought') == 0):
         return True
    return False 

def getLast(data, column):
    return data.loc[data.index[-1], column]

def plot_chart(data, n, ticker):
    
    # Filter number of observations to plot
    data = data.iloc[-n:]
    
    # Create figure and set axes for subplots
    fig = plt.figure()
    fig.set_size_inches((20, 16))
    ax_candle = fig.add_axes((0, 0.72, 1, 0.32))
    ax_macd = fig.add_axes((0, 0.48, 1, 0.2), sharex=ax_candle)
    ax_rsi = fig.add_axes((0, 0.24, 1, 0.2), sharex=ax_candle)
    ax_vol = fig.add_axes((0, 0, 1, 0.2), sharex=ax_candle)
    
    # Format x-axis ticks as dates
    ax_candle.xaxis_date()
    
    # Get nested list of date, open, high, low and close prices
    ohlc = []
    for date, row in data.iterrows():
        openp, highp, lowp, closep = row[:4]
        ohlc.append([date2num(date), openp, highp, lowp, closep])
 
    # Plot candlestick chart
    ax_candle.plot(data.index, data["ma5"], label="MA5")
    ax_candle.plot(data.index, data["ma10"], label="MA10")
    ax_candle.plot(data.index, data["ma50"], label="MA50")
    ax_candle.plot(data.index, data["ma100"], label="MA100")
    ax_candle.plot(data.index, data["ma200"], label="MA200")
    
    candlestick_ohlc(ax_candle, ohlc, colorup="g", colordown="r", width=0.8)
    ax_candle.legend()
    
    # Plot MACD
    ax_macd.plot(data.index, data["macd"], label="macd")
    ax_macd.bar(data.index, data["macd_hist"] * 3, label="hist")
    ax_macd.plot(data.index, data["macd_signal"], label="signal")
    ax_macd.legend()
    
    # Plot RSI
    # Above 70% = overbought, below 30% = oversold
    ax_rsi.set_ylabel("(%)")
    ax_rsi.plot(data.index, [80] * len(data.index), label="overbought")
    ax_rsi.plot(data.index, [20] * len(data.index), label="oversold")
    ax_rsi.plot(data.index, data["rsi"], label="rsi")
    ax_rsi.legend()
    
    # Show volume in millions
    ax_vol.bar(data.index, data["Volume"] / 1000000)
    ax_vol.set_ylabel("(Million)")
   
    # Save the chart as PNG
    fig.savefig("C:\\Users\\HP\\Downloads\\Charts\\" + ticker + ".png", bbox_inches="tight")
    
    plt.show()


def get_indicators(data):
    
    # Get MACD
    data["macd"], data["macd_signal"], data["macd_hist"] = talib.MACD(data['Close'],
        fastperiod=12, slowperiod=26, signalperiod=9)
    
    # Get MA10 and MA30
    data["ma5"] = talib.MA(data["Close"], timeperiod=5)
    data["ma10"] = talib.MA(data["Close"], timeperiod=10)
    data["ma50"] = talib.MA(data["Close"], timeperiod=50)
    data["ma100"] = talib.MA(data["Close"], timeperiod=100)
    data["ma200"] = talib.MA(data["Close"], timeperiod=200)
    
    # Get RSI
    data["rsi"] = talib.RSI(data["Close"], 14)
#    if not(np.isnan(data["rsi"])):
#        data['sma_r'] = talib.SMA(data["rsi"], 15)
    
    data['stoch_k'], data['stoch_d'] = talib.STOCH(
        data["High"], data["Low"],
        data["Close"], 14, 3)
    
    
    # SMA FAST over SLOW Crossover
    if(hasattr(data, 'ma100')):
        data['sma_test'] = np.where(data.ma100 > data.ma50, 1, 0)
    else:
        data['sma_test'] = np.where(data.ma50 > data.ma10, 1, 0)
    

    # MACD over Signal Crossover
    data['macd_test'] = np.where((data.macd > data.macd_signal), 1, 0)
    
    # Stochastics OVER BOUGHT & Decreasing
    data['stoch_over_bought'] = np.where(
        (data.stoch_k > 80) & (
            data.stoch_k > data.stoch_k.shift(1)), 1, 0)

    # Stochastics OVER SOLD & Increasing
    data['stoch_over_sold'] = np.where(
        (data.stoch_k < 20) & (
            data.stoch_k > data.stoch_k.shift(1)), 1, 0)

    # RSI OVER BOUGHT & Decreasing
    data['rsi_over_bought'] = np.where(
        (data.rsi > 80) & (
            data.rsi < data.rsi.shift(1)), 1, 0)

    # RSI OVER SOLD & Increasing
    data['rsi_over_sold'] = np.where(
        (data.rsi < 20) & (
            data.rsi > data.rsi.shift(1)), 1, 0)
    
    return data

def get_price_hist(ticker, period, interval):
    #Creare From and To date
    data = yf.download(tickers=ticker, period=period, interval=interval)
#    print("data :", data)
    return data

dataset = pd.read_csv("C:\\Users\\HP\\Desktop\\Data.csv", usecols= ['Company Name','Symbol'])

#
#    data = 


#indicator.to_csv("C:\\Users\\HP\\Desktop\\output.csv")
app = dash.Dash(__name__)
res=pd.DataFrame(columns=['Company Name', 'Time Interval', 'MACD', 'RSI', 'STOCH', 'BuyOrSell'])

#interval = np.array(["5m", "15m", "30m", "1h", "1d", "1wk", "1mo"])
#timeDiff = np.array(["5d", "15d", "1mo", "2mo", "1y", "5y", "10y"])

#interval = np.array(["15m", "30m", "1h", "1d", "1wk", "1mo"])
#timeDiff = np.array(["15d", "1mo", "2mo", "1y", "5y", "10y"])

interval = np.array(["5m", "15m", "30m", "1h", "1d"])
timeDiff = np.array(["5d", "15d", "1mo", "2mo", "1y"])

for row in dataset.itertuples():
    for i in range(len(interval)):
        for j in range(len(timeDiff)):
            if(i==j):
                print("running job for ", row[2], " with timeDiff ",timeDiff[j], " and with interval ",interval[i])
                data = get_price_hist(row[2], timeDiff[j], interval[i])
                indicator = get_indicators(data)
                name = row[1]
                setIntveral = interval[i]
                buyCount = 0
                sellCount = 0
                if(isBuyMACD(indicator)):
                    macd = 'Buy'
                    buyCount = buyCount+1
                elif(isSellMACD(indicator)):
                    macd = 'Sell'
                    sellCount = sellCount+1
                if(isBuyRSI(indicator)):
                    rsi = 'Buy'
                    buyCount = buyCount+1
                elif(isSellRSI(indicator)):
                    rsi = 'Sell'
                    sellCount = sellCount+1
                if(isBuySTOCH(indicator)):
                    stoch = 'Buy'
                    buyCount = buyCount+1
                elif(isSellSTOCH(indicator)):
                    stoch = 'Sell'
                    sellCount = sellCount+1
                if(buyCount > sellCount):
                    buyOrSell = 'Buy'
                else:
                    buyOrSell = 'Sell'
                res = res.append({'Company Name': name, 'Time Interval': setIntveral,
                            'MACD': macd, 'RSI': rsi, 'STOCH': stoch, 'BuyOrSell': buyOrSell}, ignore_index=True)
print("res : ", res)            
app.layout = dash_table.DataTable(
    id='table',
    columns=[{"name": i, "id": i} for i in res.columns],
    data=res.to_dict('records'),
    style_cell={'textAlign': 'left', 'width': '20%'},
    style_header={
        'fontWeight': 'bold',
        'textAlign': 'left'
    },
    style_data_conditional=[
        {
            'if': {
                'filter_query': '{BuyOrSell} = Buy',
                'column_id': 'BuyOrSell'
            },
            'backgroundColor': 'Green',
            'fontWeight': 'bold',
            'color': 'black'
        },
        {
            'if': {
                'filter_query': '{BuyOrSell} = Sell',
                'column_id': 'BuyOrSell'
            },
            'backgroundColor': 'Red',
            'fontWeight': 'bold',
            'color': 'black'
        }
    ]
)

if __name__ == '__main__':
    app.run_server(debug=True, use_reloader=False)
#plot_chart(indicator, 180, 'SBIN.NS')

#
    
        