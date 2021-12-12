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

nse = Nse()

def equity_history_virgin(symbol,series,start_date,end_date):
    url="https://www.nseindia.com/api/historical/cm/equity?symbol="+symbol+"&series=[%22"+series+"%22]&from="+str(start_date)+"&to="+str(end_date)+""
    payload = nsefetch(url)
    res = pd.json_normalize(payload, record_path =['data'])
    for index, row in res.iterrows():
        print(row['CH_TRADE_HIGH_PRICE'], row['CH_SYMBOL'])
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

dataset = pd.read_csv("C:\\Users\\HP\\Desktop\\Data.csv", usecols= ['Company Name','Symbol'])
line_count = 0
historic_data = equity_history('SBIN', 'EQ', '08-06-2020', '14-06-2021')
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
app = dash.Dash()
app.layout = html.Div([
    dcc.Graph(figure=fig)
])

app.run_server(debug=True, use_reloader=False) 