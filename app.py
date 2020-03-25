# Another example
#https://community.plot.ly/t/choropleth-map-in-dash/4807

import plotly
from plotly.graph_objs import *
import pandas as pd
import numpy as np
from flask import Flask
import os
from datetime import datetime as dt
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State 

mainflename = "http://covidtracking.com/api/states/daily.csv"
globdf = pd.read_csv(mainflename).fillna(0)
globdf['date'] = pd.to_datetime(globdf['date'],format='%Y%m%d')
globdf['ratio'] = (globdf['positive']/(globdf['positive']+globdf['negative'])).fillna(0)  
globdf['negative'] = (globdf['positive']+globdf['negative']).fillna(0)  # make negative total

def _create_df(field,mode):
    '''
    mode = abs, rel, log10 
    field = 'positive','negative','pending','hospitalized','death' # positive
    '''
    if mode == 'abs':
        rtndf = pd.pivot_table(globdf,values=field,index='date',columns='state').fillna(0.)
    elif mode == 'rel': 
        rtndf = pd.pivot_table(globdf,values=field,index='date',columns='state').fillna(0.).pct_change().replace(np.inf,0.).fillna(0.)
    elif mode == 'log10':
        rtndf = np.log10(pd.pivot_table(globdf,values=field,index='date',columns='state').fillna(0.)+1)

    print(field)
    print(mode)
    return rtndf

stdf = _create_df('positive','log10')

server = Flask('my app')
server.secret_key = os.environ.get('secret_key', 'secret')

external_stylesheets = ["https://cdnjs.cloudflare.com/ajax/libs/skeleton/2.0.4/skeleton.min.css",
                "https://cdn.rawgit.com/plotly/dash-app-stylesheets/737dc4ab11f7a1a8d6b5645d26f69133d97062ae/dash-wind-streaming.css",
                "https://fonts.googleapis.com/css?family=Raleway:400,400i,700,700i",
                "https://fonts.googleapis.com/css?family=Product+Sans:400,400i,700,700i",
                "https://codepen.io/chriddyp/pen/bWLwgP.css",
                ]

app = dash.Dash('streaming-wind-app', server=server, external_stylesheets=external_stylesheets)

if 'DYNO' in os.environ:
    app.scripts.append_script({
        'external_url': 'https://cdn.rawgit.com/chriddyp/ca0d8f02a1659981a0ea7f013a378bbd/raw/e79f3f789517deec58f41251f7dbb6bee72c44ab/plotly_ga.js'
    })

app.layout = html.Div([
    html.Div([
        html.H3("Coronavirus CDC Data Choropleth Visualization"),
        #html.Img(src="https://s3-us-west-1.amazonaws.com/plotly-tutorials/logo/new-branding/dash-logo-by-plotly-stripe-inverted.png"),
    ], className='row'),
    html.Div([
        html.Div([
            html.Div(html.Label(["Data Type:",dcc.Dropdown(
                id='datatype',
                options=[
                {'label': 'Confirmed Cases', 'value': 'positive'},
                {'label': 'Total Tests', 'value': 'negative'},
                {'label': 'Hospitalized', 'value': 'hospitalized'},
                {'label': 'Deaths', 'value': 'death'},
                {'label': 'Positive Test Ratio', 'value': 'ratio'},
            ],
            style={'width': '100%', 'display': 'block'},
            value='positive'
            )]),className="two columns"),
            html.Div(
                html.Label(["Value Type:",dcc.Dropdown(
            id='valuetype',
            options=[
                {'label': 'Absolute', 'value': 'abs'},
                {'label': 'Relative', 'value': 'rel'},
                {'label': 'Log10', 'value': 'log10'},
            ],
            style={'width': '100%', 'display': 'block'},
            value='rel',
            )]),className="two columns")
        ],className='row'),
    
    html.Div(id='dd-output-container')
        ], className="row"
    ),
    html.Div([
        #html.Div([
        #    html.H3("Percentage of Delinquent Loans by State from 2000-01-01 to 2015-01-01")
        #], className='Title'),
        html.Div([
            dcc.Graph(id='my-graph'),
            html.H4('Date Slider (drag backwards to see prior dates)'),
            dcc.Slider(
                id='slide',
                min=0,
                max=len(stdf.index)-1,
                value=len(stdf.index)-1,
            ),
        ], className='twelve columns wind-speed'),
        #dcc.Interval(id='wind-speed-update', interval=1000),
    ], className='row wind-speed-row'),
], style={'padding': '0px 10px 15px 10px',
          'marginLeft': 'auto', 'marginRight': 'auto', "width": "1100px",
          'boxShadow': '0px 0px 5px 5px rgba(204,204,204,0.4)'})

@app.callback(Output('my-graph','figure'),[Input('slide','value'),Input('datatype','value'),Input('valuetype','value')])
def update_graph(slide,datatype,valuetype):
    #import ipdb
    #ipdb.set_trace()
    tmpdf = _create_df(datatype,valuetype)
    tmpdf = pd.DataFrame(tmpdf.iloc[slide,:])
    maxval = np.max(tmpdf)
    #title = 'Tmp title'

    if valuetype == 'log10': 
        barname = 'Log10(Count)'
    elif valuetype == 'abs':
        barname = 'Count'
    elif valuetype == 'rel':
        barname = "Relative"

    if datatype == "positive":
        dtxt = "Positive Cases"
    elif datatype == "negative":
        dtxt = "Total Tests"
    elif datatype == "hospitalized":
        dtxt = "Hospitalized Cases"
    elif datatype == "death": 
        dtxt = "Deaths"
    elif datatype == "ratio": 
        dtxt = "Positive to Total Test Ratio"

    title_str = 'COVID-19 ' + dtxt + ' on ' + str(stdf.index[slide].date())

    tmpdf.columns = ['Del_Per']

    scl = [[0.0, 'rgb(242,240,247)'],[0.2, 'rgb(218,218,235)'],[0.4, 'rgb(188,189,220)'],\
           [0.6, 'rgb(158,154,200)'],[0.8, 'rgb(117,107,177)'],[1.0, 'rgb(84,39,143)']]

    scl = [[1.0, 'rgb(0,13,255)'],
           [0.9, 'rgb(25,37,255)'],
           [0.8, 'rgb(51,61,255)'],
           [0.7, 'rgb(75,85,255)'],
           [0.6, 'rgb(102,110,255)'],
           [0.5, 'rgb(127,134,255)'],
           [0.4, 'rgb(153,158,255)'],
           [0.3, 'rgb(178,182,255)'],
           [0.2, 'rgb(204,206,255)'],
           [0.1, 'rgb(229,230,255)'],
           [0.0, 'rgb(255,255,255)']
           ]

    scl = [[0.0, 'rgb(255,255,255)'],[0.2, 'rgb(204,206,255)'],[0.4, 'rgb(153,158,255)'],\
           [0.6, 'rgb(102,110,255)'],[0.8, 'rgb(51,61,255)'],[1.0, 'rgb(0,13,255)']]

    data_dict = [ dict(
             type='choropleth',
             #type='choropleth',
             z = tmpdf['Del_Per'],
             locationmode = 'USA-states',
             locations = tmpdf.index,
             #text = tmpdf['text'],
             zmin = 0.,
             zmax = maxval,

             colorscale = scl,
             autocolorscale = False,
             showscale=True,

             colorbar = dict(
             autotick = False,
             #ticksuffix = '%',
             title = barname,
             #title = 'Mortgage<br>Delq. Pctg.',
             ),
             font = dict(size=12),

             text = tmpdf.index,
             hovertemplate =  "<b>State: %{text}</b><br>" +
             "Value: %{z:.3f}<br>" +
            "<extra></extra>"
             ,

            #"Cases: %{y:$,.0f}<br>" +
            #"Pct.: %{x:.0%}<br>" +
             
             #marker = dict(
             #   colorbar = dict(
             #   title = "Mortgage <br> DelinquencyAA (%)"),
             #   ),
            ) 
        ]

    layout_dict = dict(
    title = title_str,
    font=dict(size=18),
    geo = dict(
    scope='usa',
    projection=dict( type='albers usa' ),
    showlakes = True,
    lakecolor = 'rgb(255, 255, 255)'),
    width = 1100,
    height = 800,
    )


    return {
        'data':data_dict,
        'layout':layout_dict,
    }


if __name__ == '__main__':
    app.run_server()
