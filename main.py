# -*- coding: utf-8 -*-
"""
Created on Sat Dec 11 13:54:30 2021

@author: HP
"""
import pandas as pd
import datetime
import numpy as np
import matplotlib.pyplot as plt
from pandas.plotting import scatter_matrix
from nsetools import Nse
from nsepython import *
import plotly.graph_objects as go
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State

nse = Nse()
app = dash.Dash(__name__)

def equity_history_virgin(symbol,series,start_date,end_date):
    url="https://www.nseindia.com/api/historical/cm/equity?symbol="+symbol+"&series=[%22"+series+"%22]&from="+str(start_date)+"&to="+str(end_date)+""
    payload = nsefetch(url)
    print("url : ", url)
    return pd.json_normalize(payload, record_path =['data'])

def equity_history(symbol,series,start_date,end_date):
    start_date = datetime.datetime.strptime(start_date, "%d-%m-%Y")
    end_date = datetime.datetime.strptime(end_date, "%d-%m-%Y")
#    print("Starting Date: "+str(start_date))
#    print("Ending Date: "+str(end_date))

    #We are calculating the difference between the days
    diff = end_date-start_date

#    print("Total Number of Days: "+str(diff.days))
#    print("Total FOR Loops in the program: "+str(int(diff.days/40)))
#    print("Remainder Loop: " + str(diff.days-(int(diff.days/40)*40)))
    
    total=pd.DataFrame()
    for i in range (0,int(diff.days/40)):

        temp_date = (start_date+datetime.timedelta(days=(40))).strftime("%d-%m-%Y")
        start_date = datetime.datetime.strftime(start_date, "%d-%m-%Y")
        
#        print("Loop = "+str(i))
#        print("====")
#        print("Starting Date: "+str(start_date))
#        print("Ending Date: "+str(temp_date))
#        print("====")

        total=total.append(equity_history_virgin(symbol,series,start_date,temp_date))

#        print("Length of the Table: "+ str(len(total)))

        #Preparation for the next loop
        start_date = datetime.datetime.strptime(temp_date, "%d-%m-%Y")


    start_date = datetime.datetime.strftime(start_date, "%d-%m-%Y")
    end_date = datetime.datetime.strftime(end_date, "%d-%m-%Y")

#    print("End Loop")
#    print("====")
#    print("Starting Date: "+str(start_date))
#    print("Ending Date: "+str(end_date))
#    print("====")

    total=total.append(equity_history_virgin(symbol,series,start_date,end_date))

#    print("Finale")
#    print("Length of the Total Dataset: "+ str(len(total)))
#    payload = total.iloc[::-1].reset_index(drop=True)
#    print(total)
    return total

@app.callback(
    Output("dd-output-container", "figure"),
    Input("demo-button", "n_clicks"),
    Input("demo-dropdown", "value"),
    Input("my-date-picker-range", "start_date"),
    Input("my-date-picker-range", "end_date")
)
def plot_graph(n_clicks, value, start_date, end_date):
    print("start_date", start_date)
    start_arr = start_date.split("-")
    print("start_arr", start_arr)
    start_date = datetime.datetime(int(start_arr[0]), int(start_arr[1]), int(start_arr[2])).strftime("%d-%m-%Y")
    print("start_date", start_date)
    end_date = end_date.split("T")[0]
    end_arr = end_date.split("-")
    end_date = datetime.datetime(int(end_arr[0]), int(end_arr[1]), int(end_arr[2])).strftime("%d-%m-%Y")
    print("end_date", end_date)
    historic_data = equity_history(value, 'EQ', str(start_date), str(end_date))
#   for row in dataset.itertuples():
#    print(row)
#    print("Data For ", row[1], "is : ", nse.get_quote(row[2]))

    fig = go.Figure(data=[
            go.Candlestick(
                    x=historic_data['CH_TIMESTAMP'],
                    open=historic_data['CH_OPENING_PRICE'],
                    high=historic_data['CH_TRADE_HIGH_PRICE'],
                    low=historic_data['CH_TRADE_LOW_PRICE'],
                    close=historic_data['CH_CLOSING_PRICE']
                    )
            ])
    fig.update_layout(xaxis_rangeslider_visible=False)
    return fig
    


dataset = pd.read_csv("C:\\Users\\HP\\Desktop\\Data.csv", usecols= ['Company Name','Symbol'])
now = datetime.datetime.now()
app.layout = html.Div([
    dcc.Dropdown(
        id='demo-dropdown',
        options=[{'label':row[1], 'value':row[2]} for row in dataset.itertuples()],
        persistence= True
    ),
    dcc.DatePickerRange(
        id='my-date-picker-range',
        calendar_orientation='vertical',
        display_format='DD-MM-YYYY',
#        min_date_allowed=date(2001, 1, 1),
#        max_date_allowed=date(now.year, now.month, now.day),
#        initial_visible_month=date(now.year, now.month, now.day),
        end_date=datetime.datetime(now.year, now.month, now.day),
        persistence= True,
        persisted_props= ["start_date", "end_date"]
    ),
    html.Button('Submit',
        id='demo-button',
        n_clicks=0
    ),
    dcc.Graph(
        id='dd-output-container'
    )
])
   

app.run_server(debug=True, use_reloader=False) 