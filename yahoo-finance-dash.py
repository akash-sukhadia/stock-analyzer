# -*- coding: utf-8 -*-
"""
Created on Mon Dec 20 11:57:49 2021

@author: HP
"""

import pandas as pd
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import talib
from stockstats import StockDataFrame as Sdf
import matplotlib.pyplot as plt
from mplfinance.original_flavor import candlestick_ohlc
from matplotlib.pylab import date2num
import yfinance as yf
import dash
# import dash_table
# import dash_html_components as html
import numpy as np
from multiprocessing import Lock
import threading
from dash import dash_table, html, Input, Output, dcc
import time
from tapy import Indicators
import sys


res = pd.DataFrame(columns=['Company Name', 'SYMBOL'])
res5m = pd.DataFrame(columns=['MACD', 'RSI', 'STOCH', 'ST', 'Ali', 'b/s'])
res15m = pd.DataFrame(columns=['MACD', 'RSI', 'STOCH', 'ST', 'Ali',  'b/s'])
res30m = pd.DataFrame(columns=['MACD', 'RSI', 'STOCH', 'ST', 'Ali',  'b/s'])
res1h = pd.DataFrame(columns=['MACD', 'RSI', 'STOCH', 'ST', 'Ali',  'b/s'])
res1d = pd.DataFrame(columns=['MACD', 'RSI', 'STOCH', 'ST', 'Ali',  'b/s'])
threads = list()


def isBuySellMACD(data):

    # Bullish SMA Crossover
    
    if (getLast(data, 'sma_test') == 1):
        # Bullish MACD
        if (getLast(data, 'macd_test') == 1):
            return "Buy"

    # Bearish SMA Crossover
    if (getLast(data, 'sma_test') == 0):
        # Bearish MACD
        if (getLast(data, 'macd_test') == 0):
            return "Sell"

    return "Nutral"


def isBuySellSTOCH(data):

    # # Bullish Stochastics
    if(getLast(data, 'stoch_over_sold') == 1):
        return "Buy"

    # # Bearish Stochastics
    if(getLast(data, 'stoch_over_bought') == 1):
        return "Sell"

    return "Nutral"


def isBuySellRSI(data):
    # # Bullish RSI
    if(getLast(data, 'rsi_over_sold') == 1):
        return "Buy"
    # # Bearish RSI
    if(getLast(data, 'rsi_over_bought') == 1):
        return "Sell"
    return "Nutral"

def isBuySellSuperTrend(data):

    if(getLast(data, 'stx') == 'up'):
        return "Buy"
    elif(getLast(data, 'stx') == 'down'):
        return "Sell"
    return "Nutral"

def isBuySellAlligator(data):
    lips = getLast(data, 'alligator_lips')
    teeth = getLast(data, 'alligator_teeth')
    jaw = getLast(data, 'alligator_jaw')
    sma = getLast(data, 'sma')
    Close = getLast(data, 'Close')
    
    if((Close > sma) and (lips > sma) and (lips > teeth) and (lips > jaw)):
        return "Buy"
    elif((Close < sma) and (lips < sma) and (lips < teeth) and (lips < jaw)):
        return "Sell"
    
    return "Nutral"

def getLast(data, column):
    return data[column].iat[-1]

def get_superTrend(data, period, multiplier):
    
    # Compute basic upper and Lower bands
    data['basic_ub'] = (data['High'] + data['Low']) / 2 + multiplier * data['atr']
    data['basic_lb'] = (data['High'] + data['Low']) / 2 - multiplier * data['atr']
    
    # Compute final upper and Lower bands
    data['final_ub'] = 0.00
    data['final_lb'] = 0.00
    for i in range(period, len(data)):
        data['final_ub'].iat[i] = data['basic_ub'].iat[i] if data['basic_ub'].iat[i] < data['final_ub'].iat[i - 1] or \
            data['Low'].iat[i - 1] > data['final_ub'].iat[i - 1] else \
        data['final_ub'].iat[i - 1]
        data['final_lb'].iat[i] = data['basic_lb'].iat[i] if data['basic_lb'].iat[i] > data['final_lb'].iat[i - 1] or \
            data['Low'].iat[i - 1] < data['final_lb'].iat[i - 1] else \
        data['final_lb'].iat[i - 1]
    
    # Set the Supertrend value
    data['supertrend'] = 0.00
    for i in range(period, len(data)):
        data['supertrend'].iat[i] = data['final_ub'].iat[i] if data['supertrend'].iat[i - 1] == data['final_ub'].iat[i - 1] \
        and data['Low'].iat[i] <= data['final_ub'].iat[i] else \
            data['final_lb'].iat[i] if data['supertrend'].iat[i - 1] == data['final_ub'].iat[i - 1] and data['Low'].iat[i] > \
                data['final_ub'].iat[i] else \
                    data['final_lb'].iat[i] if data['supertrend'].iat[i - 1] == data['final_lb'].iat[i - 1] and data['Low'].iat[i] >= \
                        data['final_lb'].iat[i] else \
                            data['final_ub'].iat[i] if data['supertrend'].iat[i - 1] == data['final_lb'].iat[i - 1] and data['Low'].iat[i] < \
                                data['final_lb'].iat[i] else 0.00
                                
    # Mark the trend direction up/down
    data['stx'] = np.where((data['supertrend'] > 0.00), np.where((data['Low'] < data['supertrend']), 'down', 'up'), np.NaN)
    return data                         
                                

def get_indicators(data):
    data1 = data.copy()
    stock_df = Sdf.retype(data1)
    data.columns = [x.title() for x in data.columns]
    print(data)
    # Get MACD
    data["macd_old"], data["macd_signal_old"], data["macd_hist_old"] = talib.MACD(data['Close'],
                                                                      fastperiod=12, slowperiod=26, signalperiod=9)
    data['macd'] = stock_df['macd']
    data["macd_signal"] = stock_df['macds']
    data["macd_hist"] = stock_df['macdh']

    # Get MA10 and MA30
    # data["ma5"] = talib.MA(data["Close"], timeperiod=5)
    # data["ma10"] = talib.MA(data["Close"], timeperiod=10)
    # data["ma50"] = talib.MA(data["Close"], timeperiod=50)
    # data["ma100"] = talib.MA(data["Close"], timeperiod=100)
    # data["ma200"] = talib.MA(data["Close"], timeperiod=200)
    
    data["ma5"] = stock_df['close_5_ema']
    data["ma10"] = stock_df['close_10_ema']
    data["ma50"] = stock_df['close_50_ema']
    data["ma100"] = stock_df['close_100_ema']
    data["ma200"] = stock_df['close_200_ema']

    # Get RSI
    data["rsi"] = stock_df['rsi']
    # if not(np.isnan(data["rsi"])):
    #     data['sma_r'] = talib.SMA(data["rsi"], 15)

    data['stoch_k_old'], data['stoch_d_old'] = talib.STOCH(
        data["High"], data["Low"],
        data["Close"], 14, 3)
    data['stoch_k'] = stock_df['stochrsi']
    data['stoch_d'] = stock_df['stochrsi_3']
    data['atr_old'] = talib.ATR(data["High"], data["Low"], data["Close"], 10)
    data['atr'] = stock_df['atr_10']
    

    # SMA FAST over SLow Crossover
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

    # # RSI OVER BOUGHT & Decreasing
    data['rsi_over_bought'] = np.where(
        (data.rsi > 80) & (
            data.rsi < data.rsi.shift(1)), 1, 0)

    # RSI OVER SOLD & Increasing
    data['rsi_over_sold'] = np.where(
        (data.rsi < 20) & (
            data.rsi > data.rsi.shift(1)), 1, 0)
    
    
    data['rsi_shift'] = data.rsi.shift(1)
    
    data['stoch_k_shift'] = data.stoch_k.shift(1)
    
    i = Indicators(data)
    
    i.alligator(period_jaws=21, period_teeth=13, period_lips=8, column_name_jaws='alligator_jaw', column_name_teeth='alligator_teeth', column_name_lips='alligator_lips')
        
    i.sma()
    data = i.df
    
    data = get_superTrend(data, 10, 3)
    # print("data size : ", len(data))
    return data


def get_price_hist(ticker, period, interval):
    # Creare From and To date

    # Get today's date as UTC timestamp
    today = datetime.today().strftime("%d/%m/%Y")
    today = datetime.strptime(today + " +0000", "%d/%m/%Y %z")
    # today = datetime.today()
    to = int((today + relativedelta(days=1)).timestamp())
    # Get date ten years ago as UTC timestamp
    switcher = {
        "5d":
            today-relativedelta(days=5),
        "15d":
            today-relativedelta(days=15),
        "1mo":
            today-relativedelta(months=1),
        "2mo":
            today-relativedelta(months=2),
        "1y":
            today-relativedelta(years=1)
    }

    fro = int(switcher.get(period).timestamp())
    da = np.busday_count(datetime.fromtimestamp(
        fro).date(), datetime.fromtimestamp(to).date()) + 1
    froDate = (today-relativedelta(days=int(da))).timestamp()
    # res5m = pd.DataFrame(columns=['MACD', 'RSI', 'STOCH', 'ST', 'BuyOrSell'])
    # time.sleep(0.01)
    # query_string = f'https://query1.finance.yahoo.com/v7/finance/download/{ticker}?period1={froDate}&period2={to}&interval={interval}&events=history&includeAdjustedClose=true'
    data = yf.download(tickers=ticker, start=str(datetime.fromtimestamp(
        froDate).date()), end=str(datetime.fromtimestamp(to).date()), interval=interval)
    # data = pd.read_csv(query_string)
    data['DateTime'] = data.index
    data.index = range(len(data))
    print("data size for ", ticker," for timeDiff ", period," : ", len(data))
    return data

def do_processing(tickerName, ticker, period, interval, l):
    l.acquire()
    try:
        global res, res5m, res15m, res30m, res1h, res1d
        print("running job for ", ticker, " with timeDiff ",
              period, " and with interval ", interval)
        data = get_price_hist(ticker, period, interval)
        indicator = get_indicators(data)
        if(len(data) != len(indicator)):
            print("data size not matching for ", ticker, " for interval ", interval)
        name = "C:\\Users\\HP\\Desktop\\Data\\" + \
            ticker + "-" + interval + ".csv"
        indicator.to_csv(name)
        name = tickerName
        setIntveral = interval
        buyCount = 0
        sellCount = 0
        nutralCount = 0
        buyOrSell = ''
        macd = isBuySellMACD(indicator)
        rsi = isBuySellRSI(indicator)
        stoch = isBuySellSTOCH(indicator)
        superTrend = isBuySellSuperTrend(indicator)
        alligator = isBuySellAlligator(indicator)
        
        if(alligator == 'Buy'):
            buyCount = buyCount+1
        elif(alligator == 'Nutral'):
            nutralCount = nutralCount + 1
        elif(alligator == 'Sell'):
            sellCount = sellCount + 1
            
        if(superTrend == 'Buy'):
            buyCount = buyCount+1
        elif(superTrend == 'Nutral'):
            nutralCount = nutralCount + 1
        elif(superTrend == 'Sell'):
            sellCount = sellCount + 1
    
        if(macd == 'Buy'):
            buyCount = buyCount+1
        elif(macd == 'Nutral'):
            nutralCount = nutralCount + 1
        elif(macd == 'Sell'):
            sellCount = sellCount + 1

        if(rsi == 'Buy'):
            buyCount = buyCount+1
        elif(rsi == 'Nutral'):
            nutralCount = nutralCount + 1
        elif(rsi == 'Sell'):
            sellCount = sellCount + 1

        if(stoch == 'Buy'):
            buyCount = buyCount+1
        elif(stoch == 'Nutral'):
            nutralCount = nutralCount + 1
        elif(stoch == 'Sell'):
            sellCount = sellCount + 1

        if(buyCount > nutralCount and buyCount > sellCount):
            buyOrSell = 'Buy'
        elif(nutralCount > buyCount and nutralCount > sellCount):
            buyOrSell = 'Nutral'
        elif(sellCount > buyCount and sellCount > nutralCount):
            buyOrSell = 'Sell'
        elif(buyCount == nutralCount and buyCount > sellCount):
            buyOrSell = 'Buy'
        elif(sellCount == nutralCount and sellCount > buyCount):
            buyOrSell = 'Sell' 
        elif(sellCount == buyCount):
            buyOrSell = 'Nutral' 

        if(setIntveral == '5m'):
            res = res.append({'Company Name': name, 'SYMBOL': ticker}, ignore_index=True)
            # res5m = res5m.append(
                # {'MACD': macd, 'RSI': rsi, 'STOCH': stoch, 'ST': superTrend, 'Ali': alligator, 'b/s': buyOrSell}, ignore_index=True)
        elif(setIntveral == '15m'):
            res = res.append({'Company Name': name, 'SYMBOL': ticker}, ignore_index=True)
            res15m = res15m.append(
                {'MACD': macd, 'RSI': rsi, 'STOCH': stoch, 'ST': superTrend, 'Ali': alligator, 'b/s': buyOrSell}, ignore_index=True)
        elif(setIntveral == '30m'):
            res30m = res30m.append(
                {'MACD': macd, 'RSI': rsi, 'STOCH': stoch, 'ST': superTrend, 'Ali': alligator, 'b/s': buyOrSell}, ignore_index=True)
        elif(setIntveral == '1h'):
            res1h = res1h.append(
                {'MACD': macd, 'RSI': rsi, 'STOCH': stoch, 'ST': superTrend, 'Ali': alligator, 'b/s': buyOrSell}, ignore_index=True)
        elif(setIntveral == '1d'):
            res1d = res1d.append(
                {'MACD': macd, 'RSI': rsi, 'STOCH': stoch, 'ST': superTrend, 'Ali': alligator, 'b/s': buyOrSell}, ignore_index=True)
            
    finally:
        print("done")
        l.release()
        
app = dash.Dash(__name__)

def draw_script_div():
    global res
    return html.Div(
        dash_table.DataTable(
            id='table-name',
            columns=[{"name": i, "id": i} for i in res.columns],
            data=res.to_dict('records'),
            style_cell={'textAlign': 'left'},
            style_header={
                'fontWeight': 'bold',
                'textAlign': 'left'
                }
            ), style={'width': '15%', 'display': 'inline-block'})

def draw_5m_div():
    return html.Div(
        dash_table.DataTable(
            id='table-5m',
            columns=[{"name": i, "id": i} for i in res5m.columns],
            data=res5m.to_dict('records'),
            style_cell={'textAlign': 'left', 'width': '5%'},
            style_header={
                'fontWeight': 'bold',
                'textAlign': 'left'
                },
            style_data_conditional=[
                {
                    'if': {
                        'filter_query': '{Ali} = Buy',
                        'column_id': 'Ali'
                        },
                    'backgroundColor': 'Green',
                    'fontWeight': 'bold',
                    'color': 'black'
                    },
                {
                    'if': {
                        'filter_query': '{Ali} = Sell',
                        'column_id': 'Ali'
                        },
                    'backgroundColor': 'Red',
                    'fontWeight': 'bold',
                    'color': 'black'
                    },
                {
                    'if': {
                        'filter_query': '{Ali} = Nutral',
                        'column_id': 'Ali'
                        },
                    'backgroundColor': 'Grey',
                    'fontWeight': 'bold',
                    'color': 'black'
                    },
                {
                    'if': {
                        'filter_query': '{ST} = Buy',
                        'column_id': 'ST'
                        },
                    'backgroundColor': 'Green',
                    'fontWeight': 'bold',
                    'color': 'black'
                    },
                {
                    'if': {
                        'filter_query': '{ST} = Sell',
                        'column_id': 'ST'
                        },
                    'backgroundColor': 'Red',
                    'fontWeight': 'bold',
                    'color': 'black'
                    },
                {
                    'if': {
                        'filter_query': '{ST} = Nutral',
                        'column_id': 'ST'
                        },
                    'backgroundColor': 'Grey',
                    'fontWeight': 'bold',
                    'color': 'black'
                    },
                {
                    'if': {
                        'filter_query': '{MACD} = Buy',
                        'column_id': 'MACD'
                        },
                    'backgroundColor': 'Green',
                    'fontWeight': 'bold',
                    'color': 'black'
                    },
                {
                    'if': {
                        'filter_query': '{MACD} = Sell',
                        'column_id': 'MACD'
                        },
                    'backgroundColor': 'Red',
                    'fontWeight': 'bold',
                    'color': 'black'
                    },
                {
                    'if': {
                        'filter_query': '{MACD} = Nutral',
                        'column_id': 'MACD'
                        },
                    'backgroundColor': 'Grey',
                    'fontWeight': 'bold',
                    'color': 'black'
                    },
                {
                    'if': {
                        'filter_query': '{RSI} = Buy',
                        'column_id': 'RSI'
                        },
                    'backgroundColor': 'Green',
                    'fontWeight': 'bold',
                    'color': 'black'
                    },
                {
                    'if': {
                        'filter_query': '{RSI} = Sell',
                        'column_id': 'RSI'
                        },
                    'backgroundColor': 'Red',
                    'fontWeight': 'bold',
                    'color': 'black'
                    },
                {
                    'if': {
                        'filter_query': '{RSI} = Nutral',
                        'column_id': 'RSI'
                        },
                    'backgroundColor': 'Grey',
                    'fontWeight': 'bold',
                    'color': 'black'
                    },
                {
                    'if': {
                        'filter_query': '{STOCH} = Buy',
                        'column_id': 'STOCH'
                        },
                    'backgroundColor': 'Green',
                    'fontWeight': 'bold',
                    'color': 'black'
                    },
                {
                    'if': {
                        'filter_query': '{STOCH} = Sell',
                        'column_id': 'STOCH'
                        },
                    'backgroundColor': 'Red',
                    'fontWeight': 'bold',
                    'color': 'black'
                    },
                {
                    'if': {
                        'filter_query': '{STOCH} = Nutral',
                        'column_id': 'STOCH'
                        },
                    'backgroundColor': 'Grey',
                    'fontWeight': 'bold',
                    'color': 'black'
                    },
                {
                    'if': {
                        'filter_query': '{b/s} = Buy',
                        'column_id': 'b/s'
                        },
                    'backgroundColor': 'Green',
                    'fontWeight': 'bold',
                    'color': 'black'
                    },
                {
                    'if': {
                        'filter_query': '{b/s} = Sell',
                        'column_id': 'b/s'
                        },
                    'backgroundColor': 'Red',
                    'fontWeight': 'bold',
                    'color': 'black'
                    },
                {
                    'if': {
                        'filter_query': '{b/s} = Nutral',
                        'column_id': 'b/s'
                        },
                    'backgroundColor': 'Grey',
                    'fontWeight': 'bold',
                    'color': 'black'
                    }
                ]
            ), style={'width': '16%', 'display': 'inline-block', 'margin': '10px'})

def draw_15m_div():
    return html.Div(dash_table.DataTable(
        id='table-15m',
        columns=[{"name": i, "id": i} for i in res15m.columns],
        data=res15m.to_dict('records'),
        style_cell={'textAlign': 'left', 'width': '10%'},
        style_header={
            'fontWeight': 'bold',
            'textAlign': 'left'
            },
        style_data_conditional=[
            {
                'if': {
                    'filter_query': '{Ali} = Buy',
                    'column_id': 'Ali'
                    },
                'backgroundColor': 'Green',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{Ali} = Sell',
                    'column_id': 'Ali'
                    },
                'backgroundColor': 'Red',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{Ali} = Nutral',
                    'column_id': 'Ali'
                    },
                'backgroundColor': 'Grey',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{ST} = Buy',
                    'column_id': 'ST'
                    },
                'backgroundColor': 'Green',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{ST} = Sell',
                    'column_id': 'ST'
            },
                'backgroundColor': 'Red',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{ST} = Nutral',
                    'column_id': 'ST'
                    },
                'backgroundColor': 'Grey',
                'fontWeight': 'bold',
                'color': 'black'
                },  
            {
                'if': {
                    'filter_query': '{MACD} = Buy',
                    'column_id': 'MACD'
                    },
                'backgroundColor': 'Green',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{MACD} = Sell',
                    'column_id': 'MACD'
                    },
                'backgroundColor': 'Red',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{MACD} = Nutral',
                    'column_id': 'MACD'
                    },
                'backgroundColor': 'Grey',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{RSI} = Buy',
                    'column_id': 'RSI'
                    },
                'backgroundColor': 'Green',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{RSI} = Sell',
                    'column_id': 'RSI'
                    },
                'backgroundColor': 'Red',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{RSI} = Nutral',
                    'column_id': 'RSI'
                    },
                'backgroundColor': 'Grey',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{STOCH} = Buy',
                    'column_id': 'STOCH'
                    },
                'backgroundColor': 'Green',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{STOCH} = Sell',
                    'column_id': 'STOCH'
                    },
                'backgroundColor': 'Red',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{STOCH} = Nutral',
                    'column_id': 'STOCH'
                    },
                'backgroundColor': 'Grey',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{b/s} = Buy',
                    'column_id': 'b/s'
                    },
                'backgroundColor': 'Green',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{b/s} = Sell',
                    'column_id': 'b/s'
                    },
                'backgroundColor': 'Red',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{b/s} = Nutral',
                    'column_id': 'b/s'
                    },
                'backgroundColor': 'Grey',
                'fontWeight': 'bold',
                'color': 'black'
            }
        ]            
    ), style={'width': '16%', 'display': 'inline-block', 'margin': '40px'})

def draw_30m_div():
    return html.Div(dash_table.DataTable(
        id='table-30m',
        columns=[{"name": i, "id": i} for i in res30m.columns],
        data=res30m.to_dict('records'),
        style_cell={'textAlign': 'left', 'width': '10%'},
        style_header={
            'fontWeight': 'bold',
            'textAlign': 'left'
            },
        style_data_conditional=[
            {
                'if': {
                    'filter_query': '{Ali} = Buy',
                    'column_id': 'Ali'
                    },
                'backgroundColor': 'Green',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{Ali} = Sell',
                    'column_id': 'Ali'
                    },
                'backgroundColor': 'Red',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{Ali} = Nutral',
                    'column_id': 'Ali'
                    },
                'backgroundColor': 'Grey',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{ST} = Buy',
                    'column_id': 'ST'
                    },
                'backgroundColor': 'Green',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{ST} = Sell',
                    'column_id': 'ST'
                    },
                'backgroundColor': 'Red',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{ST} = Nutral',
                    'column_id': 'ST'
                    },
                'backgroundColor': 'Grey',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{MACD} = Buy',
                    'column_id': 'MACD'
                    },
                'backgroundColor': 'Green',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{MACD} = Sell',
                    'column_id': 'MACD'
                    },
                'backgroundColor': 'Red',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{MACD} = Nutral',
                    'column_id': 'MACD'
                    },
                'backgroundColor': 'Grey',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{RSI} = Buy',
                    'column_id': 'RSI'
                    },
                'backgroundColor': 'Green',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{RSI} = Sell',
                    'column_id': 'RSI'
                    },
                'backgroundColor': 'Red',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{RSI} = Nutral',
                    'column_id': 'RSI'
                    },
                'backgroundColor': 'Grey',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{STOCH} = Buy',
                    'column_id': 'STOCH'
                    },
                'backgroundColor': 'Green',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{STOCH} = Sell',
                    'column_id': 'STOCH'
                    },
                'backgroundColor': 'Red',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{STOCH} = Nutral',
                    'column_id': 'STOCH'
                    },
                'backgroundColor': 'Grey',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{b/s} = Buy',
                    'column_id': 'b/s'
                    },
                'backgroundColor': 'Green',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{b/s} = Sell',
                    'column_id': 'b/s'
                    },
                'backgroundColor': 'Red',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{b/s} = Nutral',
                    'column_id': 'b/s'
                    },
                'backgroundColor': 'Grey',
                'fontWeight': 'bold',
                'color': 'black'
                }
            ]
        ), style={'width': '15%', 'display': 'inline-block', 'margin': '12px'})

def draw_1h_div():
    return html.Div(dash_table.DataTable(
        id='table-1h',
        columns=[{"name": i, "id": i} for i in res1h.columns],
        data=res1h.to_dict('records'),
        style_cell={'textAlign': 'left', 'width': '10%'},
        style_header={
            'fontWeight': 'bold',
            'textAlign': 'left'
            },
        style_data_conditional=[
            {
                'if': {
                    'filter_query': '{Ali} = Buy',
                    'column_id': 'Ali'
                    },
                'backgroundColor': 'Green',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{Ali} = Sell',
                    'column_id': 'Ali'
                    },
                'backgroundColor': 'Red',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{Ali} = Nutral',
                    'column_id': 'Ali'
                    },
                'backgroundColor': 'Grey',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{ST} = Buy',
                    'column_id': 'ST'
                    },
                'backgroundColor': 'Green',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{ST} = Sell',
                    'column_id': 'ST'
                    },
                'backgroundColor': 'Red',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{ST} = Nutral',
                    'column_id': 'ST'
                    },
                'backgroundColor': 'Grey',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{MACD} = Buy',
                    'column_id': 'MACD'
                    },
                'backgroundColor': 'Green',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{MACD} = Sell',
                    'column_id': 'MACD'
                    },
                'backgroundColor': 'Red',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{MACD} = Nutral',
                    'column_id': 'MACD'
                    },
                'backgroundColor': 'Grey',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{RSI} = Buy',
                    'column_id': 'RSI'
                    },
                'backgroundColor': 'Green',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{RSI} = Sell',
                    'column_id': 'RSI'
                    },
                'backgroundColor': 'Red',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{RSI} = Nutral',
                    'column_id': 'RSI'
                    },
                'backgroundColor': 'Grey',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{STOCH} = Buy',
                    'column_id': 'STOCH'
                    },
                'backgroundColor': 'Green',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{STOCH} = Sell',
                    'column_id': 'STOCH'
                    },
                'backgroundColor': 'Red',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{STOCH} = Nutral',
                    'column_id': 'STOCH'
                    },
                'backgroundColor': 'Grey',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{b/s} = Buy',
                    'column_id': 'b/s'
                    },
                'backgroundColor': 'Green',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{b/s} = Sell',
                    'column_id': 'b/s'
                    },
                'backgroundColor': 'Red',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{b/s} = Nutral',
                    'column_id': 'b/s'
                    },
                'backgroundColor': 'Grey',
                'fontWeight': 'bold',
                'color': 'black'
                }
            ]
        ), style={'width': '15%', 'display': 'inline-block', 'margin': '55px'})

def draw_1d_div():
    return html.Div(dash_table.DataTable(
        id='table-1d',
        columns=[{"name": i, "id": i} for i in res1d.columns],
        data=res1d.to_dict('records'),
        style_cell={'textAlign': 'left', 'width': '10%'},
        style_header={
            'fontWeight': 'bold',
            'textAlign': 'left'
            },
        style_data_conditional=[
            {
                'if': {
                    'filter_query': '{Ali} = Buy',
                    'column_id': 'Ali'
                    },
                'backgroundColor': 'Green',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{Ali} = Sell',
                    'column_id': 'Ali'
                    },
                'backgroundColor': 'Red',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{Ali} = Nutral',
                    'column_id': 'Ali'
                    },
                'backgroundColor': 'Grey',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{ST} = Buy',
                    'column_id': 'ST'
                    },
                'backgroundColor': 'Green',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{ST} = Sell',
                    'column_id': 'ST'
                    },
                'backgroundColor': 'Red',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{ST} = Nutral',
                    'column_id': 'ST'
                    },
                'backgroundColor': 'Grey',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{MACD} = Buy',
                    'column_id': 'MACD'
                    },
                'backgroundColor': 'Green',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{MACD} = Sell',
                    'column_id': 'MACD'
                    },
                'backgroundColor': 'Red',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{MACD} = Nutral',
                    'column_id': 'MACD'
                    },
                'backgroundColor': 'Grey',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{RSI} = Buy',
                    'column_id': 'RSI'
                    },
                'backgroundColor': 'Green',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{RSI} = Sell',
                    'column_id': 'RSI'
                    },
                'backgroundColor': 'Red',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{RSI} = Nutral',
                    'column_id': 'RSI'
                    },
                'backgroundColor': 'Grey',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{STOCH} = Buy',
                    'column_id': 'STOCH'
                    },
                'backgroundColor': 'Green',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{STOCH} = Sell',
                    'column_id': 'STOCH'
                    },
                'backgroundColor': 'Red',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{STOCH} = Nutral',
                    'column_id': 'STOCH'
                    },
                'backgroundColor': 'Grey',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{b/s} = Buy',
                    'column_id': 'b/s'
                    },
                'backgroundColor': 'Green',
                'fontWeight': 'bold',
            'color': 'black'
            },
            {
                'if': {
                    'filter_query': '{b/s} = Sell',
                    'column_id': 'b/s'
                    },
                'backgroundColor': 'Red',
                'fontWeight': 'bold',
                'color': 'black'
                },
            {
                'if': {
                    'filter_query': '{b/s} = Nutral',
                    'column_id': 'b/s'
                    },
                'backgroundColor': 'Grey',
                'fontWeight': 'bold',
                'color': 'black'
                }
            ]
        ), style={'width': '12%', 'display': 'inline-block', 'margin': '12px'})

def update_table():
    return [draw_script_div(),
    # draw_5m_div(),
    draw_15m_div(),
    draw_30m_div(),
    draw_1h_div(),
    draw_1d_div()]

def plot_dataTable():                    
    app.layout = html.Div([
        html.Button('Fetch Data', id='submit-val', n_clicks=0),
        dcc.Loading(
            id="loading-1",
            type="default",
            children=html.Div(id="parent", children = [
            draw_script_div(),
            # draw_5m_div(),
            draw_15m_div(),
            draw_30m_div(),
            draw_1h_div(),
            draw_1d_div()])
        )
        ])
    
def get_all_data():
    global threads
    try:
        print("before thread size : ", len(threads))
        dataset = pd.read_csv("C:\\Users\\HP\\Desktop\\Data.csv",
                                  usecols=['Company Name', 'Symbol'])
        # interval = np.array(["5m", "15m", "30m", "1h", "1d"])
        # timeDiff = np.array(["5d", "15d", "1mo", "2mo", "1y"])
        interval = np.array(["15m", "30m", "1h", "1d"])
        timeDiff = np.array(["15d", "1mo", "2mo", "1y"])
        lock = Lock()
        
        for row in dataset.itertuples():
            for i in range(len(interval)):
                for j in range(len(timeDiff)):
                    if(i == j and __name__ == '__main__' and row[2] == 'SBIN.NS'):
                    # if(i == j and __name__ == '__main__'):
                    # if(i == j):
                        name = "thread-"+row[2]+"-"+interval[i]
                        # do_processing(row[1], row[2], timeDiff[j], interval[i], lock)
                        # do_processing(row[1], row[2], timeDiff[j], interval[i], lock)
                        t = threading.Thread(name = name, target=do_processing, args=(row[1], row[2], timeDiff[j], interval[i], lock))
                        # proc = multiprocessing.Process(target=do_processing, args=(row[1], row[2], timeDiff[j], interval[i], lock))
                        threads.append(t)
                        # t.start()


        for index, thread in enumerate(threads):
            print("started")
            thread.start()
            
                        
        for index, thread in enumerate(threads):
            print("joined")
            thread.join()
            
        for t in threads:
            if not t.is_alive():
                # get results from thread
                t.handled = True
    finally:
        threads = [t for t in threads if not t.handled] 
        print("after thread size : ", len(threads))

def load_data():
    get_all_data()
    plot_dataTable()

# load_data()
plot_dataTable()
# print(sys.version)


# @app.callback(Output("loading-output-1", "children"), Input("submit-val", "n_clicks"))
# def query_loader(n_clicks):
#     return ""

@app.callback(Output("parent", "children"), Input("submit-val", "n_clicks"))
def query_df(n_clicks):
    print("n_clicks :", n_clicks)
    if(n_clicks > 0):
        global res, res5m, res15m, res30m, res1h, res1d
        res = res.iloc[0:0]
        res5m = res5m.iloc[0:0]
        res15m = res15m.iloc[0:0]
        res30m = res30m.iloc[0:0]
        res1h = res1h.iloc[0:0]
        res1d = res1d.iloc[0:0]
        get_all_data()
        return update_table()

if __name__ == '__main__':
    app.run_server(debug=True, port=8080)
#plot_chart(indicator, 180, 'SBIN.NS')

#
