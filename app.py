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

def _makedfs(datatype):
    confirmed_url = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_19-covid-Confirmed.csv'
    deaths_url = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_19-covid-Deaths.csv'
    recovered_url = 'https://github.com/CSSEGISandData/COVID-19/blob/master/csse_covid_19_data/csse_covid_19_time_series/time_series_19-covid-Recovered.csv'

    statesdf = pd.read_csv('https://raw.githubusercontent.com/steve98654/covid19-US/master/states.csv')    # table of state names and abbreviations
    state_list = statesdf['State'].values

    if datatype == 'Confirmed Cases':  # datatype switch
        df = pd.read_csv(confirmed_url,error_bad_lines=False)
    elif datatype == 'Deaths':
        df = pd.read_csv(deaths_url,error_bad_lines=False)
    #elif datatype == 'Recovered':
    #    df = pd.read_csv(recovered_url,error_bad_lines=False)


    # data wrangling     
    df = df[df['Country/Region'] == 'US']
    df = df[df['Province/State'].isin(state_list)]  
    df = df.set_index('Province/State')
    dropcols = ['Country/Region','Lat','Long']
    df = df.drop(dropcols,axis=1).T
    df.index = pd.to_datetime(df.index)
    start_date = '2020-03-10' # no data prior to this date
    df = df[start_date:]
    df = df.stack().reset_index()
    df.columns = ['date','state','cases']
    df['state'] = df['state'].map(dict(zip(statesdf['State'],statesdf['Abbreviation'])))
    df['date'] = df['date'].map(str)
    pct_change = pd.pivot_table(df,values='cases',index='date',columns='state').pct_change().tail(-1).fillna(0).replace(np.inf,0).unstack().reset_index()
    df = pd.merge(df,pct_change,on=['date','state'])
    df = df.rename(columns={0:"Case-%Change"})
    df['date'] = df['date'].apply(lambda x:x.split(" ")[0])

    absdf = df.pivot_table(index='date',columns='state',values='cases')  
    reldf = df.pivot_table(index='date',columns='state',values='Case-%Change')  

    return absdf, reldf

conf_absdf, conf_reldf = _makedfs('Confirmed Cases')
death_absdf, death_reldf = _makedfs('Deaths')
#recover_absdf, recover_reldf = _makedfs('Recovered')

absdf = conf_absdf
reldf = conf_reldf

# stdf = pd.read_pickle('dashboard_default_df.pkl')

####### put in callback 

#absolute_cases = False
#if absolute_cases: 
#    absdf = np.log10(absdf+1) # add one to avoid np.infty errors
#    title = "COVID-19 Total Cases"
#    maxval = np.max(absdf)
#else: 
#    title = "COVID-19 Daily %Change "
#    maxval = 1

stdf = reldf
################


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
                {'label': 'Confirmed Cases', 'value': 'confirmed'},
                {'label': 'Deaths', 'value': 'deaths'},
                #{'label': 'Recovered', 'value': 'recovered'}
            ],
            style={'width': '100%', 'display': 'block'},
            value='confirmed'
            )]),className="two columns"),
            html.Div(
                html.Label(["Value Type:",dcc.Dropdown(
            id='valuetype',
            options=[
                {'label': 'Absolute', 'value': 'absolute'},
                {'label': 'Relative', 'value': 'relative'},
            ],
            style={'width': '100%', 'display': 'block'},
            value='absolute',
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
    if valuetype == 'absolute':
        if datatype == "confirmed":
            tmpdf = pd.DataFrame(conf_absdf.iloc[slide,:])
            maxval = np.max(conf_absdf)
            title = "Total Confirmed Cases as of "
        elif datatype == "deaths":
            tmpdf = pd.DataFrame(death_absdf.iloc[slide,:])
            maxval = np.max(death_absdf)
            title = "Total Deaths as of "
        elif datatype == "recovered":
            tmpdf = pd.DataFrame(recover_absdf.iloc[slide,:])
            maxval = np.max(recover_absdf)
            title = "Total Recoveries as of "
        
        barname = "log10(Cases)"
        tmpdf = np.log10(tmpdf+1) # add one to avoid np.infty errors
        #title = "COVID-19 Total Absolute " + datatype

    elif valuetype == 'relative':
        maxval = 1.
        if datatype == "confirmed":
            tmpdf = pd.DataFrame(conf_reldf.iloc[slide,:])
            title = "Daily Percentage Change in Confirmed Cases as of "
        elif datatype == "deaths":
            tmpdf = pd.DataFrame(death_reldf.iloc[slide,:])
            title = "Daily Percentage Change in Deaths as of "
        elif datatype == "recovered":
            tmpdf = pd.DataFrame(recover_reldf.iloc[slide,:])
            title = "Daily Percentage Change in Recoveries as of "

        barname = "Daily Pct.<br>Change"

    title_str = 'COVID-19 ' + title + str(stdf.index[slide])

    #import ipdb 
    #ipdb.set_trace()
    tmpdf.columns = ['Del_Per']
    #tmpdf['vls'] = tmpdf.values
    #tmpdf['state'] = tmpdf.index

    scl = [[0.0, 'rgb(242,240,247)'],[0.2, 'rgb(218,218,235)'],[0.4, 'rgb(188,189,220)'],\
           [0.6, 'rgb(158,154,200)'],[0.8, 'rgb(117,107,177)'],[1.0, 'rgb(84,39,143)']]

    #tmpdf['text'] = tmpdf['state'] + '<br>' +\
    #                'Del % ' + tmpdf['vls'].astype(str) 

    data_dict = [ dict(
             type='choropleth',
             #type='choropleth',
             z = tmpdf['Del_Per'],
             locationmode = 'USA-states',
             locations = tmpdf.index,
             #text = tmpdf['text'],
             zmin = 0.,
             zmax = maxval,

             #colorscale = scl,
             autocolorscale = True,
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
