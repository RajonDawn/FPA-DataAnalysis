import streamlit as st
import pandas as pd

import fun_ProcessData as fun
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import datetime


st.set_page_config(layout="wide", page_icon='./CMI.png')

# canDataset1 = pd.DataFrame()
# canDataset2 = pd.DataFrame()
@st.cache_data
def read_data(filepath):
  data = pd.read_csv(filepath)
  return data

canDataset1 = read_data(r"C:\Users\rh517\Desktop\Current\07 M15油耗试验\4 道路试验(永乐东-蓝天东-腰市)\单车总数据\第一组对照\J7-平原高速.csv")
canDataset2 = read_data(r"C:\Users\rh517\Desktop\Current\07 M15油耗试验\4 道路试验(永乐东-蓝天东-腰市)\单车总数据\第一组对照\Yingtu-平原高速1.csv")


# Silder
with st.sidebar:
  st.image('./CMI.png', width=40)
  st.title('CCI油耗试验数据分析')
  st.date_input("请选择试验日期", datetime.date(2023, 6, 5))

  uploaded_canFile1 = st.file_uploader("请上传A车总线数据", accept_multiple_files=False)
  uploaded_canFile2 = st.file_uploader("请上传B车数据文件", accept_multiple_files=False)
  # fuelMap = st.file_uploader('请输入M15FuelMap数据文件', accept_multiple_files=False)
  c1, c2 = st.columns(2)
  with c1:
    hpA = st.radio('请选择A车发动机马力(hp)', options=[620, 660])
  with c2:
    hpB = st.radio('请选择B车发动机马力(hp)', options=[620, 660])
  
  if (uploaded_canFile1 is not None) and (uploaded_canFile2 is not None):
    # Can be used wherever a "file-like" object is accepted:
    canDataset1 = pd.read_csv(uploaded_canFile1, skiprows=[1])
    canDataset2 = pd.read_csv(uploaded_canFile2, skiprows=[1])

  torq_620 = pd.DataFrame({'Speed':[550,600,700,800,900,1400,1500,1600,1700,1800,1830,1900,2000],
                           'Torque':[1300,1300,1900,2500,2800,2800,2770,2660,2545,2420,2370,2225,2115]})

  torq_660 = pd.DataFrame({'Speed':[550,600,700,800,900,1400,1500,1600,1700,1800,1830,1900,2000],
                           'Torque':[1300,1300,1900,2500,3200,3200,3000,2830,2700,2575,2520,2365,2250]})       

  torq1 = torq_620
  torq2 = torq_620 
  if hpA == 660:
    torq1 = torq_660
  if hpB == 660:
    torq2 = torq_660


#### 主界面

if (len(canDataset1)>10) and (len(canDataset2)>10):
  canDataset1 = fun.clean_df(canDataset1)
  canDataset2 = fun.clean_df(canDataset2)
    
  col1, col2 = st.columns(2, gap='large')

  number1Srt = col1.number_input('请输入数据开始时间', value=0, key='AStartTime')
  number1End = col1.number_input('请输入数据结束时间', value=canDataset1['Time'].max())

  sltTime1 = col1.slider(label='请选择A车数据范围时间(min)', min_value=0, max_value=int(canDataset1['Time'].max()), step=5, value=(number1Srt, number1End))

  number2Srt = col2.number_input('请输入数据开始时间', value=0, key='BStartTime')
  number2End = col2.number_input('请输入数据结束时间', value=canDataset2['Time'].max())
  sltTime2 = col2.slider(label='请选择B车数据范围时间(min)', min_value=0, max_value=int(canDataset2['Time'].max()), step=5, value=(number2Srt, number2End))

  sltCAN1 = canDataset1.loc[(canDataset1['Time']>sltTime1[0] )&(canDataset1['Time']<sltTime1[1])]
  sltCAN2 = canDataset2.loc[(canDataset2['Time']>sltTime2[0] )&(canDataset2['Time']<sltTime2[1])]

  numberCols = list(sltCAN1.select_dtypes('number'))
  # numberCols.remove('Parameter Name')

  for df, col, label in zip([sltCAN1, sltCAN2], [col1, col2], ['A','B']):
    with col:
      fig_Alt = fun.plotAltVSpd(df)
      fig_Alt.update_layout(height = 400)
      st.plotly_chart(fig_Alt, theme='streamlit', height=400)

      subcol1, subcol2, subcol3, subcol4, subcol5 = st.columns(5)
      fuelUsed = df['FCR_Instantaneous_Fuel_Rate'].sum() / 3600
      mileage = df['Vehicle_Speed'].sum()/3600
      with subcol1:
        st.metric(label='换挡次数:', value=fun.cal_ShiftGear(df))
      with subcol2:
        st.metric(label='平均车速(km/h):', value=np.round(df['Vehicle_Speed'].mean(),2))
      with subcol3:
        st.metric(label='总里程(km):', value=np.round(mileage))
      with subcol4:
        st.metric(label='油耗(L/100km):', value=np.round(fuelUsed/mileage*100,2))
      with subcol5:
        st.metric(label='95分位坡度:', value=np.percentile(df['J39_Transmission_Grade'].dropna(), 95))


tab1, tab2, tab3 = st.tabs(["🚚Summary", "🔥Engine", "⚙️Transmission"])
with tab1:
  st.subheader('自定义图像', )
  col11, col12 = st.columns(2, gap='large')
  bubbleXlab = col11.selectbox('请选择x轴参数', options=numberCols, index=numberCols.index('Engine_Speed'), key='bubbleXColumn')
  bubbleYlab = col11.selectbox('请选择y轴参数', options=numberCols, index=numberCols.index('Net_Engine_Torque'), key='bubbleYColumn')
  bubbleXbin = col12.number_input('请选择x轴区间密度', value=100, key='bubbleXSize')
  bubbleYbin = col12.number_input('请选择y轴区间密度', value=200, key='bubbleYSize')

  if (bubbleXlab!='Parameter Name') and (bubbleYlab!='Parameter Name'):
    figBubble = fun.plotBubble(sltCAN1, bubbleXlab, bubbleYlab, bubbleXbin, bubbleYbin, torq1)
    col11.plotly_chart(figBubble, theme="streamlit", use_container_width=True)

    figBubble = fun.plotBubble(sltCAN2, bubbleXlab, bubbleYlab,  bubbleXbin, bubbleYbin, torq2)
    col12.plotly_chart(figBubble, theme="streamlit", use_container_width=True)


  histXlab = col11.selectbox('请选择x轴参数', options=numberCols, index=numberCols.index('Engine_Speed'), key='histColumn')
  histXbin = col12.number_input('请选择x轴区间密度', value=100, key='histBinSize')

  if histXlab!='Parameter Name':
    figHist = fun.plotHist(sltCAN1, histXlab, histXbin)
    col11.plotly_chart(figHist, theme="streamlit", use_container_width=True)

    figHist = fun.plotHist(sltCAN2, histXlab, histXbin)
    col12.plotly_chart(figHist, theme="streamlit", use_container_width=True)



  lineYCols = col11.multiselect('请选择左纵轴参数', options=numberCols,  key='lineYCols')
  lineYYCols = col12.multiselect('请选择右纵轴参数', options=numberCols, key='lineYYCols')

  if lineYCols or lineYYCols:
    figLine = fun.plotLine(sltCAN1, lineYCols, lineYYCols)
    col11.plotly_chart(figLine, theme=None, use_container_width=True)

    figLine = fun.plotLine(sltCAN2, lineYCols, lineYYCols)
    col12.plotly_chart(figLine, theme=None, use_container_width=True)



  

with tab2:
  col21, col22 = st.columns(2, gap='large')
  for col, df in zip([col21, col22], [sltCAN1, sltCAN2]):
    with col:
      pie_CCPO = fun.plotPie('CCPO分布', df, 'Service_Brake_Switch')
      st.plotly_chart(pie_CCPO, theme="streamlit")

      pie_Chi = fun.plotPie('刹车比例', df, 'Service_Brake_Switch')
      st.plotly_chart(pie_Chi, theme="streamlit")

      sca_ABT = fun.plotABT(df)
      st.plotly_chart(sca_ABT,  use_container_width=True)


with tab3:
  # st.subheader('', )
  shift = st.radio('换挡点分布', options=['升档', '降档'])
  col31, col32 = st.columns(2, gap='large')
  for col, df in zip([col31, col32], [sltCAN1, sltCAN2]):
    with col:
      df.loc[:, 'Shift'] = np.nan
      df.loc[df['J39_SelectedGear'] - df['J39_CurrentGear']>0, 'Shift'] = '升档'
      df.loc[df['J39_SelectedGear'] - df['J39_CurrentGear']<0, 'Shift'] = '降档'
      # df.loc[df[df['J39_CurrentGear'] ==0].index, 'Shift'] = 'N'

      df.loc[:, 'J39_CurrentGear'] = df['J39_CurrentGear'].astype(str)
      sca_Shift = px.scatter(df[df['Shift']==shift], \
        x='Engine_Speed', \
        y='Net_Engine_Torque', \
        color='J39_CurrentGear', 
        category_orders = {'J39_CurrentGear': list(range(0, 13,1)) })
      st.plotly_chart(sca_Shift, theme="streamlit", use_container_width=True)

