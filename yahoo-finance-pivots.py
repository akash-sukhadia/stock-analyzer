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
# import dash_table
# import dash_html_components as html
import numpy as np
from multiprocessing import Lock
import threading
from dash import dash_table, html, Input, Output, dcc
import time
from tapy import Indicators
import sys
import requests as _requests


res = pd.DataFrame(columns=['Company Name', 'SYMBOL', 'CLOSE'])
res5m = pd.DataFrame(columns=['S3', 'S2', 'S1', 'PIVOT', 'R1', 'R2', 'R3'])
res15m = pd.DataFrame(columns=['S3', 'S2', 'S1', 'PIVOT', 'R1', 'R2', 'R3'])
res30m = pd.DataFrame(columns=['S3', 'S2', 'S1', 'PIVOT', 'R1', 'R2', 'R3'])
res1h = pd.DataFrame(columns=['S3', 'S2', 'S1', 'PIVOT', 'R1', 'R2', 'R3'])
res1d = pd.DataFrame(columns=['S3', 'S2', 'S1', 'PIVOT', 'R1', 'R2', 'R3'])
threads = list()


def getLast(data, column):
    return data[column].iat[-1]


def get_pivots(data):
    
    pivot = (data.High.shift(1) + data.Low.shift(1) + data.Close.shift(1))/3
    r1 = (2*pivot) - data.Low.shift(1)
    s1 = (2*pivot) - data.High.shift(1)
    r2 = (pivot) + (data.High.shift(1) - data.Low.shift(1))
    s2 = (pivot) - (data.High.shift(1) - data.Low.shift(1))
    r3 = (r1) + (data.High.shift(1) - data.Low.shift(1))
    s3 = (s1) - (data.High.shift(1) - data.Low.shift(1))

    
    data['S3'] = s3
    data['S2'] = s2
    data['S1'] = s1
    data['PIVOT'] = pivot
    data['R1'] = r1
    data['R2'] = r2
    data['R3'] = r3
    

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
    froDate = int((today-relativedelta(days=int(da))).timestamp())
    # res5m = pd.DataFrame(columns=['MACD', 'RSI', 'STOCH', 'ST', 'BuyOrSell'])
    # session = _requests
    # query_string = f'https://query2.finance.yahoo.com/v7/finance/download/{ticker}?period1={froDate}&period2={to}&interval={interval}&events=history&includeAdjustedClose=true'
    # data = session.get(
    #             url=url,
    #             params=params,
    #             proxies=proxy,
    #             headers=utils.user_agent_headers,
    #             timeout=timeout
    #         )
    
    # print("queryString : ", query_string)
    data = yf.download(tickers=ticker, start=str(datetime.fromtimestamp(
        froDate).date()), end=str(datetime.fromtimestamp(to).date()), interval=interval)
    # data = pd.read_csv(query_string)
    data['DateTime'] = data.index
    data.index = range(len(data))
    print("data size for ", ticker," for timeDiff ", period," : ", len(data))
    # print("data :", data)
    return data

def calculate_piviots(tickerName, ticker, period, interval, l):
    l.acquire()
    try:
        global res, res5m, res15m, res30m, res1h, res1d
        print("running job for ", ticker, " with timeDiff ",
              period, " and with interval ", interval)
        data = get_price_hist(ticker, period, interval)
        indicator = get_pivots(data)
        name = "C:\\Users\\HP\\Desktop\\Data\\" + \
            ticker + "-" + interval + "-pivots.csv"
        indicator.to_csv(name)
        name = tickerName
        setIntveral = interval
        
        if(setIntveral == '5m'):
            res = res.append({'Company Name': name, 'SYMBOL': ticker, 'CLOSE': round(getLast(data, 'Close'), 2)}, ignsore_index=True)
            # res5m = res5m.append(
            #     {'S3': round(getLast(data, 'S3'), 2), 'S2': round(getLast(data, 'S2'), 2), 'S1': round(getLast(data, 'S1'), 2), 
            #      'PIVOT': round(getLast(data, 'PIVOT'), 2), 'R1': round(getLast(data, 'R1'), 2), 'R2': round(getLast(data, 'R2'), 2), 'R3': round(getLast(data, 'R3'), 2)}, ignore_index=True)
        elif(setIntveral == '15m'):
            res = res.append({'Company Name': name, 'SYMBOL': ticker, 'CLOSE': round(getLast(data, 'Close'), 2)}, ignore_index=True)
            res15m = res15m.append(
                {'S3': round(getLast(data, 'S3'), 2), 'S2': round(getLast(data, 'S2'), 2), 'S1': round(getLast(data, 'S1'), 2), 
                 'PIVOT': round(getLast(data, 'PIVOT'), 2), 'R1': round(getLast(data, 'R1'), 2), 'R2': round(getLast(data, 'R2'), 2), 'R3': round(getLast(data, 'R3'), 2)}, ignore_index=True)
        elif(setIntveral == '30m'):
            res30m = res30m.append(
                {'S3': round(getLast(data, 'S3'), 2), 'S2': round(getLast(data, 'S2'), 2), 'S1': round(getLast(data, 'S1'), 2), 
                  'PIVOT': round(getLast(data, 'PIVOT'), 2), 'R1': round(getLast(data, 'R1'), 2), 'R2': round(getLast(data, 'R2'), 2), 'R3': round(getLast(data, 'R3'), 2)}, ignore_index=True)
        elif(setIntveral == '1h'):
            res1h = res1h.append(
                {'S3': round(getLast(data, 'S3'), 2), 'S2': round(getLast(data, 'S2'), 2), 'S1': round(getLast(data, 'S1'), 2), 
                 'PIVOT': round(getLast(data, 'PIVOT'), 2), 'R1': round(getLast(data, 'R1'), 2), 'R2': round(getLast(data, 'R2'), 2), 'R3': round(getLast(data, 'R3'), 2)}, ignore_index=True)
        # elif(setIntveral == '1d'):
        #     res1d = res1d.append(
        #         {'S3': round(getLast(data, 'S3'), 2), 'S2': round(getLast(data, 'S2'), 2), 'S1': round(getLast(data, 'S1'), 2), 
        #          'PIVOT': round(getLast(data, 'PIVOT'), 2), 'R1': round(getLast(data, 'R1'), 2), 'R2': round(getLast(data, 'R2'), 2), 'R3': round(getLast(data, 'R3'), 2)}, ignore_index=True)
            
    finally:
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
            ), style={'width': '20%', 'display': 'inline-block'})

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
                }
            ), style={'width': '20%', 'display': 'inline-block', 'margin': '5px'})

def draw_15m_div():
    return html.Div(dash_table.DataTable(
        id='table-15m',
        columns=[{"name": i, "id": i} for i in res15m.columns],
        data=res15m.to_dict('records'),
        style_cell={'textAlign': 'left', 'width': '10%'},
        style_header={
            'fontWeight': 'bold',
            'textAlign': 'left'
            }           
    ), style={'width': '25%', 'display': 'inline-block', 'margin': '15px'})

def draw_30m_div():
    return html.Div(dash_table.DataTable(
        id='table-30m',
        columns=[{"name": i, "id": i} for i in res30m.columns],
        data=res30m.to_dict('records'),
        style_cell={'textAlign': 'left', 'width': '10%'},
        style_header={
            'fontWeight': 'bold',
            'textAlign': 'left'
            }
        ), style={'width': '25%', 'display': 'inline-block', 'margin-left': '10px', 'margin-right': '25px'})

def draw_1h_div():
    return html.Div(dash_table.DataTable(
        id='table-1h',
        columns=[{"name": i, "id": i} for i in res1h.columns],
        data=res1h.to_dict('records'),
        style_cell={'textAlign': 'left', 'width': '10%'},
        style_header={
            'fontWeight': 'bold',
            'textAlign': 'left'
            }
        ), style={'width': '25%', 'display': 'inline-block'})

def draw_1d_div():
    return html.Div(dash_table.DataTable(
        id='table-1d',
        columns=[{"name": i, "id": i} for i in res1d.columns],
        data=res1d.to_dict('records'),
        style_cell={'textAlign': 'left', 'width': '10%'},
        style_header={
            'fontWeight': 'bold',
            'textAlign': 'left'
            }
        ), style={'width': '3%', 'display': 'inline-block', 'margin': '5px'})

def update_table():
    return [draw_script_div(),
    # draw_5m_div(),
    draw_15m_div(),
    draw_30m_div(),
    draw_1h_div()
    # draw_1d_div()
    ]

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
            draw_1h_div()
            # draw_1d_div()
            ])
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
        interval = np.array(["15m", "30m", "1h"])
        timeDiff = np.array(["15d", "1mo", "2mo"])
        lock = Lock()
        
        for row in dataset.itertuples():
            for i in range(len(interval)):
                for j in range(len(timeDiff)):
                    if(i == j and __name__ == '__main__'):
                    # if(i == j and __name__ == '__main__'):
                        name = "thread-"+row[2]+"-"+interval[i]
                        # do_processing(row[1], row[2], timeDiff[j], interval[i], lock)
                        t = threading.Thread(name = name, target=calculate_piviots, args=(row[1], row[2], timeDiff[j], interval[i], lock))
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
    app.run_server(debug=True, port=8081)
#plot_chart(indicator, 180, 'SBIN.NS')

#
