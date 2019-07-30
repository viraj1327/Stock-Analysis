import pandas_datareader.data as web
#import datetime
from datetime import datetime, timedelta
import dash
import dash_table as dt
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import pandas as pd
from newsapi import NewsApiClient
from textblob import TextBlob
import plotly.graph_objs as go
import numpy as np
from plotly.tools import FigureFactory as FF
import matplotlib.pyplot as plt

app = dash.Dash()
df=pd.read_csv("/Users/viraj/Desktop/Avant/App/companylist.csv")
newsapi = NewsApiClient(api_key='19566a6cc96747eeadf90d82c464489k')


companies=df[(df['Sector']=='Technology') & (df['MarketCap']>='$1.00B')]['Symbol']

def generate_table(dataframe,max_rows=10):
    return html.Table(
        # Header
        [html.Tr([html.Th(col) for col in dataframe.columns])] +

        # Body
        [html.Tr([
            html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
        ]) for i in range(min(len(dataframe), max_rows))]
    )


def word_stripping(word):
    if ("Inc." | "Corporation") in word:
    # if word.contains('Inc.'):
        return word.rstrip("Inc.") |  word.rstrip("Corporation")
    else:
        return word



def news_dataFrame(data):
    articles_list=list()
    sample=list()
    sample1=list()

    for i in range(1,6):
        all_articles = newsapi.get_everything(q=df[df['Symbol']==data]['Short_Name'].values[0],
                                              sources='google-news',
                                              domains='https://news.google.com',
                                              # from_param=datetime.datetime.now() + datetime.timedelta(-30),
                                              from_param=(datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"), #'2019-05-30'/2019-04-15
                                              # to=datetime.datetime.now(),
                                              to = datetime.today().strftime('%Y-%m-%d') , #'2019-06-29'/2019-05-11
                                              language='en',
                                              sort_by='publishedAt',
                                              page=i)
        for i in all_articles['articles']:
            sample.append(i['description'])
            sample1.append(i['publishedAt'])



    new_df=pd.DataFrame({
    'News': sample,
    'Published_Date&Time': sample1
    })
    new_df['News'].replace('', np.nan, inplace=True)
    new_df.dropna(subset=['News'], inplace=True)
    new_df['Published_Date']=pd.to_datetime(new_df["Published_Date&Time"]).dt.date
    new_df['Published_Time']=pd.to_datetime(new_df["Published_Date&Time"]).dt.time
    new_df['Polarity']=new_df['News'].apply(lambda text: TextBlob(text).sentiment.polarity)
    new_df['Subjectivity']=new_df['News'].apply(lambda text: TextBlob(text).sentiment.subjectivity)
    new_df['Sentiment']=np.where(new_df['Polarity']>0,"Positive","Negative")
    new_df['Sentiment'][new_df['Polarity']==0]="Netural"

    return new_df

app.layout = html.Div(children=[
        html.H1('Stock prices'),
        html.Hr(),
        html.Hr(),
        dcc.Dropdown(id='my-dropdown', options=[
            {'label': i, 'value': i} for i in companies.unique()
        ],
        placeholder='Filter by Company...'),
        html.Hr(),
        # html.Div(id='output-container'),
        html.Div(id='data-frame'),
        html.Hr(),
        html.Div(id='graph',style={'width':'100%','height': '450px','border':'2px black solid'}),
        html.Hr(),
        # dt.DataTable(id='data-table')


        html.Div(
        [
        html.Div([
        html.H1('Top News'),
        html.Table(id='Data-Table')
        ],
        style={'width':'50%','height': '900px','border':'2px black solid','float':'left'}),
        html.Div(id='piecharts',  style= {'width': '45%','height':'450px','border':'2px black solid', 'float':'right'})
        ])
        ])


@app.callback(
    Output(component_id='graph', component_property='children'),
    [Input(component_id='my-dropdown', component_property='value')]
)

def update_value(input_data):
    start=datetime.now() - timedelta(days=30)#datetime.now() + datetime.timedelta(-30)
    end = datetime.now()
    df2 = web.DataReader(input_data, 'yahoo', start, end)
    return dcc.Graph(
        figure=go.Figure(
        data=[
        go.Ohlc(x=df2.index,
                open=df2['Open'],
                high=df2['High'],
                low=df2['Low'],
                close=df2['Close'])
        ],
        layout={
        'title': str(df[df['Symbol']==input_data]['Name'].values[0])+ ' ' +'Stock Prices in a Last 30 days',
        'yaxis': {'title': str(df[df['Symbol']==input_data]['Name'].values[0])+ ' '+'Stock'}
        }
            )
        )
@app.callback(
    Output(component_id='data-frame', component_property='children'),
    [Input(component_id='my-dropdown', component_property='value')]
)

def update_value(input_data):
    return generate_table(df[df['Symbol']==input_data][['Symbol','Name','Sector','industry','MarketCap']])




@app.callback(
    Output('Data-Table', 'children'),
    [Input('my-dropdown', 'value')]
)

def update_table(data):
    new_df= news_dataFrame(data)
    return generate_table(new_df[['News','Polarity','Sentiment']])

@app.callback(
    Output('piecharts', 'children'),
    [Input('my-dropdown', 'value')]
)

def update_value(value):
    new_df= news_dataFrame(value)

    return dcc.Graph(
    figure=go.Figure(
        data=[
        go.Pie(
        labels = new_df['Sentiment'].unique(),
        values = new_df['Sentiment'].value_counts()
        )],
        layout= go.Layout(
        title='Pecenatges Distribution of the News'
        )
        )
        )

if __name__ == '__main__':
    app.run_server(debug=True)
