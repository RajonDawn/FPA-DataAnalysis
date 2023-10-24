from importlib.machinery import DEBUG_BYTECODE_SUFFIXES
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import plotly.express as px


def clean_GPS(df):
  '''对GPS数据进行重命名和清洗，去除中国边境内以外的点'''
  df.rename(columns={'GPS_Latitude_GPS':'lat', 'GPS_Longitude_GPS':'lon', 'GPS_Speed_GPS':'spd'}, inplace=True)
  df['lat'] = (df['lat'] //100) + (df['lat'] % 100) / 60
  df['lon'] = (df['lon'] //100) + (df['lon'] % 100) / 60
  df = df.drop(df[(df['lon'] < 73.666) | (df['lon'] > 135.08333)].index)
  df = df.drop(df[(df['lat'] < 4) | (df['lat'] > 53.5)].index)
  df.dropna(subset=['lat', 'lon'], inplace=True)
  
  df['PC_Timestamp_GPS'] = pd.to_datetime(df['PC_Timestamp_GPS'], infer_datetime_format=True)
  df['Timestamp'] = df['PC_Timestamp_GPS'].apply(lambda x: x.strftime('%Y-%m-%d %H:%M'))

  #while len(df)>3000:
    #df = df.loc[0::2,:]
  return df

  

def clean_df(df_source):
  df_source = df_source[pd.to_numeric(df_source['Engine_Speed'], errors='coerce').notnull()]
  df_source.sort_values(by='ECM_Run_Time', inplace=True)
  df_source = df_source[pd.to_numeric(df_source['Engine_Speed'], errors='coerce').notnull()]
  df_source = df_source[df_source['Engine_Speed']>200]
  df_source = df_source[df_source['Engine_Speed']<3000]
  df_source.reset_index(inplace=True, drop=True)
  if 'Time' not in list(df_source):
    df_source.loc[:, 'Time'] = range(len(df_source))
    df_source.loc[:, 'Time'] = df_source.loc[:, 'Time'] 
  df_source.loc[:, 'Altitude'] = df_source['Altitude'].rolling(window=15,).mean()
  df_source['PC_Timestamp'] = pd.to_datetime(df_source['PC_Timestamp'])
  if 'FCR_Instantaneous_Fuel_Rate' not in list(df_source):
    df_source.loc['FCR_Instantaneous_Fuel_Rate'] = df_source['Total_Fueling'] * df_source['Engine_Speed'] *6 * 60/2/1000000
  df_source['Engine Power'] = df_source['Engine_Speed'] * df_source['Net_Engine_Torque'] / 9550
  # df_source['CBR_Chi_Table_Mask'] = df_source['CBR_Chi_Table_Mask'].apply(lambda x: hex(x).split[1])
  return df_source

def plotAltVSpd(df): 
# use specs parameter in make_subplots function
# to create secondary y-axis
  fig = make_subplots(specs=[[{"secondary_y": True}]])

  fig.add_trace(
      go.Scatter(x=df['PC_Timestamp'], y=df['Altitude'], fill='tozeroy',  line_color='Silver', name='Altitude', opacity=0.4),
      secondary_y=False
      )

  fig.add_trace(
      go.Scatter(x=df['PC_Timestamp'], y=df['Vehicle_Speed'], line_color='deepskyblue', name='Vehicle Speed', opacity=0.7),
      secondary_y=True,)
  # Adding title text to the figure
  fig.update_layout(
      title_text="海拔及车速曲线图", 
      showlegend=True
  )
  
  fig.update_xaxes(title_text="Time")
  fig.update_yaxes(title_text="Altitude", rangemode="tozero", secondary_y=False, tickmode = "auto", nticks=5)
  fig.update_yaxes(title_text="Vehicle Speed", rangemode="tozero", secondary_y=True, tickmode = "auto", nticks=5)
  fig.update_layout(font={'size': 18})
  fig.update_layout(height = 400)

  fig.update_layout(legend=dict(
    yanchor="top",
    y=1.1,
    xanchor="center",
    x=0.5,
    orientation='h',valign='top',
))

  return fig


def cal_ShiftGear(df_source):
  '''计算换挡次数'''
  df_source.loc[:, 'Shift'] = 0
  df_source.loc[df_source['J39_CurrentGear'].diff()!=0, 'Shift'] = 1
  return df_source['Shift'].sum()
  
def cal_Brake(df_source):
  brakeTime = sum(df_source['Service_Brake_Switch']>0)
  brakeCount = sum(df_source['Service_Brake_Switch'].diff()==1)
  
  brakeCount_30 = sum((df_source['Service_Brake_Switch'].diff()==1) & (df_source['Vehicle_Speed']>30))
  return [brakeTime, brakeCount, brakeCount_30]



def plotBubble(df_source, xcol, ycol, xbins, ybins, df_torque):
  df = df_source[[xcol, ycol, 'Fan_Drive_State']].copy()
  df[xcol] = np.round(df[xcol]/xbins)*xbins
  df[ycol] = np.round(df[ycol]/ybins)*ybins

  output = df.groupby(by=[xcol, ycol], as_index=False)['Fan_Drive_State'].count()
  output['Pct_Time'] = np.round(output['Fan_Drive_State']/sum(output['Fan_Drive_State'])*100, 2)
  output = output[output['Pct_Time']>0.01]
  
  fig_bubble = px.scatter(output, x=xcol, y=ycol, size='Pct_Time', text = [str(i) for i in output['Pct_Time']], opacity= 0.5, )
  fig_output = fig_bubble
  if ('Engine_Speed' in xcol) and ('Net_Engine_Torque' in ycol):
    fig_torq = px.line(df_torque, x='Speed (rpm)', y='Torque (Nm)')
    fig_torq.update_traces(line=dict(color = 'red'))
  
    fig_output = go.Figure(data=fig_bubble.data + fig_torq.data)
    fig_output.update_layout(xaxis_title=xcol,  yaxis_title=ycol, height = 600)
    fig_output.update_xaxes(showgrid=True)
    fig_output.update_yaxes(showgrid=True)

  fig_output.update_layout(font={'size': 14})
  return fig_output

def plotHist(df_source, col, bins):
  df = df_source[col].dropna()
  fig_hist = px.histogram(df, x=col, histnorm='percent', opacity=0.7, text_auto='.2f')
  fig_hist.update_traces(xbins=dict(size=bins),)
  fig_hist.update_layout(font={'size': 18}, bargap=0.2)
  fig_hist.update_traces(textposition='inside', textfont_size=12,)
  return fig_hist

def plotLine(df_source, lColumns, rColumns):
  fig = make_subplots(specs=[[{"secondary_y": True}]])

  for temp in lColumns:
    fig.add_trace(
        go.Scatter(x=df_source['PC_Timestamp'], y=df_source[temp], name=temp, opacity=0.7),
        secondary_y=False
        )
  for temp in rColumns:
    fig.add_trace(
        go.Scatter(x=df_source['PC_Timestamp'], y=df_source[temp], name=temp, opacity=0.7),
        secondary_y=True,)
  fig.update_xaxes(title_text="Time")
  fig.update_layout(showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center",  x=0.5))

  fig.update_layout(font={'size': 18}, \

    hovermode='x', 
    modebar={'add':["hovercompare", "togglehover", "togglespikelines", 'toImage','resetViews']},\
  )
  fig.update_yaxes(secondary_y=False, tickmode = "auto", nticks=5)
  fig.update_yaxes(secondary_y=True, tickmode = "auto", nticks=5)
  return fig


def plotPie(title, df_source, col):

  
  df = df_source[pd.to_numeric(df_source[col], errors='coerce',  downcast='signed').notnull()]
  df[col] = pd.to_numeric(df_source[col], errors='coerce',  downcast='signed')

  if col == 'CBR_Chi_Table_Mask':
    df = df[df[col]>1]

  orders = df[col].unique()
  orders.sort()

  output = df.groupby(col)['Engine_Speed'].count()
  output = output.reset_index().rename({'Engine_Speed': 'Counts'}, axis=1)
  
  fig = px.pie(output, names=col, values='Counts', category_orders={col: list(orders)})
  fig.update_layout(title=title, font={'size': 18})

  fig.update_layout(legend=dict(
    yanchor="top",
    y=-0.1,
    xanchor="center",
    x=0.5,
    orientation='h',valign='top',
))
  return fig
  

def plotBox(title, df_source, col):
  df = df_source[pd.to_numeric(df_source[col], errors='coerce').notnull()].copy()

  x = px.box(df, x=col, )
  return x

# def plotViolin

def plotABT(df_source, ):
  df = df_source[pd.to_numeric(df_source['Accelerator_Pedal_Position'], errors='coerce').notnull()].copy()
  df['Accelerator_Pedal_Position'] =  pd.to_numeric(df_source['Accelerator_Pedal_Position'], errors='coerce')
  df['Accelerator_Pedal_Position'] = df['Accelerator_Pedal_Position'].round()

  df['ABT'] = np.nan
  abt = [str(x) for x in range(10, 101, 10)]
  for i in abt:
    temp = (df['Accelerator_Pedal_Position']< int(i)+3) & (df['Accelerator_Pedal_Position']> int(i)-3)
    df.loc[temp, 'ABT'] = i

  df.dropna(subset=['ABT'], inplace=True)
  fig = px.scatter(df, x='Engine_Speed', y='Net_Engine_Torque', color='ABT', category_orders = {'ABT': abt }, opacity=0.5)
  fig.update_layout(font={'size': 18}, height = 600)
  return fig


def plotViolin(df_source, col):
  df = df_source[pd.to_numeric(df_source[col], errors='coerce').notnull()].copy()
  fig = px.violin(
    df,
    y=col,
    box=True,   # 开启之后在小提琴图里面绘制箱型图
    points='all',  # all-全部   outliers-离群点   False-不显示，默认
)

  return fig


def plotScatter(df_source, x, y):
  fig = px.scatter(df_source, x, y)
  return fig
