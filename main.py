from time import sleep
import streamlit as st
import pandas as pd
import numpy as np
import scipy

import fun_ProcessData as fun
import datetime as dt
import pydeck as pdk

st.set_page_config(layout="wide", page_icon='./CMI.png')

Select_Par = ['Parameter Name',
              'PC_Timestamp',
              'ECM_Run_Time', 'Engine_Run_Time',
              'TI_Vehicle_Trip_ECM_Distance', 'TI_Base_Total_Fuel_Used', 
              'Altitude',
              ## 发动机转速、扭矩相关参数
              'Engine_Speed', 'Net_Engine_Torque', 'PrcntLoadAtCurSpd',
              ## 发动机油耗相关参数
              'Total_Fueling', 'FCR_Instantaneous_Fuel_Rate', 'CBR_Chi_Table_Mask',
              ## 车速相关参数
              'Vehicle_Speed', 'Accelerator_Pedal_Position',
              ## 冷却液温度相关参数
              'Coolant_Temperature', 'Oil_Temperature', 'Ambient_Air_Tmptr', 'Fan_Speed', 'Fan_Drive_State',
              ## 变速箱挡位、坡度、重量参数
              'Clutch_Switch', 'Service_Brake_Switch', 
              'J39_CurrentGear', 'ActiveFaults',  'J39_Transmission_Grade', 'J39_Transmission_Gross_Mass', 'MME_Vehicle_Mass',
              'Combustion_Control_Path_Owner', 
              'P_SFR_tmh_SinceActiveRegen', 'V_SFP_gpl_Soot_Load_Comb', 'P_SFR_Regen_Trigger_State', 'V_SFR_Regen_Stage',
              'V_SCR5_pc_CE_for_Ctrl', 'V_SCP_trc_SCR_Bed'
              ]
GPS_Par = ['PC_Timestamp_GPS', 'GPS_Longitude_GPS', 'GPS_Latitude_GPS', 'GPS_Altitude_GPS', ]

@st.cache_data
def read_data(filepaths):
  candata = pd.DataFrame()
  gpsdata = pd.DataFrame()

  for i in filepaths:
    mat_CAN = scipy.io.loadmat(i, variable_names=Select_Par, squeeze_me=True)
    [mat_CAN.pop(i) for i in ['__header__', '__version__', '__globals__']]
    temp = pd.DataFrame(data=mat_CAN, columns=Select_Par)
    candata = pd.concat([candata, temp], ignore_index=True)
    try:
      mat_GPS = scipy.io.loadmat(i, variable_names=GPS_Par, squeeze_me=True)
      [mat_GPS.pop(i) for i in ['__header__', '__version__', '__globals__']]  
      temp = pd.DataFrame(data=mat_GPS, columns=GPS_Par)
      gpsdata = pd.concat([gpsdata, temp], ignore_index=True)
    except ValueError:
      gpsdata = pd.DataFrame(columns=GPS_Par)
  return candata, gpsdata


# Silder
with st.sidebar:
  st.image('./CMI.png', width=40)
  st.title('FPA油耗试验数据分析')
  testDate = st.date_input("请选择试验日期", dt.date.today())
  matFiles = st.file_uploader(label="请上传车辆*:red[mat]*数据", accept_multiple_files=True)
  engModel = st.radio('请选择车辆发动机马力(hp)', options=['M13NS6B570', 'Z14NS6B560', 'M10NS6B400'])
  

torq_570 = pd.read_csv(f'./data/M13NS6B570_FR21537.csv', skiprows=[0], usecols=[5, 6, 7])
torq_560 = pd.read_csv(f'./data/Z14NS6B560_FR20921.csv',skiprows=[0], usecols=[5, 6, 7])
torq = torq_560
if engModel == 'M13NS6B570':
  torq = torq_570
elif engModel == 'M8.5NS6B360':
  torq = pd.read_csv(f'./data/M8pt5NS6B360_FR98329.csv',skiprows=[0], usecols=[5, 6, 7])

#### 主界面
if len(matFiles)>0:
  canDataset, gpsDataset = read_data(matFiles)
  for i in Select_Par:
    if i not in list(canDataset):
      canDataset[i] = np.nan

  canDataset = fun.clean_df(canDataset)
  gpsDataset = fun.clean_GPS(gpsDataset)

  if len(canDataset)>0:
    strDatetime = pd.to_datetime(canDataset['PC_Timestamp']).min().to_pydatetime()
    endDatetime = pd.to_datetime(canDataset['PC_Timestamp']).max().to_pydatetime()
  else:
    strDatetime = dt.datetime.combine(dt.date.today(), dt.time(0,0,0))
    endDatetime = dt.datetime.combine(dt.date.today(), dt.time(23,59,59))

  col1, col2 = st.columns(2,  gap='large')

  col11, col12 = col1.columns(2,  gap='large')
  x1 = col11.date_input(label='请输入数据开始日期', value=strDatetime)
  x2 = col12.time_input(label='请输入数据开始时间', value=strDatetime, step=dt.timedelta(minutes=5)) #step=0:10:00)


  y1 = col11.date_input(label='请输入数据结束日期', value=endDatetime)
  y2 = col12.time_input(label='请输入数据结束时间', value=endDatetime, step=dt.timedelta(minutes=5)) #step=0:10:00)

  sltTime = []
  sltTime.append(dt.datetime.combine(x1, x2))
  sltTime.append(dt.datetime.combine(y1, y2))
  sltCAN = pd.DataFrame()

  # if col1.button('确认'):
  sltCAN = canDataset.loc[(canDataset['PC_Timestamp']>=sltTime[0] )&(canDataset['PC_Timestamp']<=sltTime[1])]


  numberCols = list(sltCAN.select_dtypes('number'))
  fig_Alt = fun.plotAltVSpd(sltCAN)
  col1.plotly_chart(fig_Alt,  height=400)


  try:
    gpsdf = gpsDataset.loc[(gpsDataset['PC_Timestamp_GPS']>=sltTime[0] )&(gpsDataset['PC_Timestamp_GPS']<=sltTime[1])]
    col2.pydeck_chart(pdk.Deck(
      map_style=None,
      initial_view_state=pdk.ViewState(
          latitude=34.32,
          longitude=108.55,
          zoom=2.5,
      ),
      layers=[
          pdk.Layer(
            'ScatterplotLayer',
            data=gpsdf,
            opacity=0.7,
            get_position='[lon, lat]',
            get_radius=100,
            radius_scale=6,
            radius_min_pixels=5,
            radius_max_pixels=5,

            pickable=True,
            extruded=True,
            get_fill_color=[255,0,0],
          )
      ], 
      tooltip={"text": "{Timestamp}"}
    ))
  except KeyError:
    gpsdf = gpsDataset




  tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8= st.tabs(["🚚Summary", "🔥Engine", "⚙️Transmission", "💨Exhuast", "☢️Fan", '⛰️Environment', '🚚Drive Ability', '📊Customization'])

  if len(canDataset)>0:
    with tab1:
      sltCAN.loc['FCR_Instantaneous_Fuel_Rate'] = sltCAN['Total_Fueling'] * sltCAN['Engine_Speed']*6*60/2/1000000
      subcol1, subcol2, subcol3, subcol4, subcol5, subcol6 = st.columns(6)
      fuelUsed = sltCAN['FCR_Instantaneous_Fuel_Rate'].sum() / 3600
      mileage = sltCAN['Vehicle_Speed'].sum()/3600
      
      mileage2 = sltCAN['TI_Vehicle_Trip_ECM_Distance'].max() - sltCAN['TI_Vehicle_Trip_ECM_Distance'].min()
      fuelUsed2 = sltCAN['TI_Base_Total_Fuel_Used'].max() - sltCAN['TI_Base_Total_Fuel_Used'].min()
      
      subcol1.metric(label='数据累计时间(h):', value=np.round(len(sltCAN)/3600, 2))
      subcol1.metric(label='数据累计里程(km):', value=np.round(mileage))
      subcol1.metric(label='怠速占比(%):', value=np.round(sum(sltCAN['Combustion_Control_Path_Owner']==11)/len(sltCAN)*100,2), help='CCPO=11的时间占比')

      subcol2.metric(label='平均车速(km/h):', value=np.round(sltCAN['Vehicle_Speed'].mean(),2))
      subcol2.metric(label='行驶车速(km/h):', value=np.round(sltCAN.loc[sltCAN['Vehicle_Speed']>2, 'Vehicle_Speed'].mean(),2))

      coast = ( (sltCAN['Combustion_Control_Path_Owner']==136) | (sltCAN['J39_CurrentGear']==0) ) & ((sltCAN['Vehicle_Speed']>15))
      subcol2.metric(label='空挡滑行占比(%):', value=np.round(sum(coast)/len(sltCAN)*100,2), help='车速小于700且车速>30km/h的时间占比')

      subcol3.metric(label='计算油耗(L/100km):', value=np.round(fuelUsed/mileage*100,2))
      subcol3.metric(label='ECM计算油耗(L/100km):', value=np.round(fuelUsed2/mileage2*100,2))
      subcol3.metric(label='再生次数:', value=sum(sltCAN['P_SFR_tmh_SinceActiveRegen'].diff()<0), help='根据P_SFR_tmh_SinceActiveRegen上下做差，如果出现负数，则再生次数+1')

      subcol4.metric(label='百公里换挡次数:', value=np.round(fun.cal_ShiftGear(sltCAN)/mileage2*100,2))
      subcol4.metric(label='百公里刹车次数:', value=np.round((fun.cal_Brake(sltCAN))[2]/mileage2*100,2))
      subcol4.metric(label='百公里刹车时长(s):', value=np.round((fun.cal_Brake(sltCAN))[0]/mileage2*100,2))

      subcol5.metric(label='50%分位坡度中值:', value=sltCAN['J39_Transmission_Grade'].median())
      # subcol5.metric(label='75%分位分位坡度中值:', value=np.percentile(sltCAN['J39_Transmission_Grade'].dropna(), 95))
      subcol5.metric(label='平均转速(rpm):', value=np.round(sltCAN['Engine_Speed'].dropna().mean(), 2))

      subcol6.metric(label='功率平均值(kw):', value=np.round((sltCAN.loc[sltCAN['Engine Power']>0, 'Engine Power']).mean(),2), help='发动机正功率行的平均值')
      # subcol6.metric(label='车重中位值(t):', value=np.round(np.percentile(sltCAN['J39_Transmission_Gross_Mass'].dropna(), 50)/1000, 2), help='变速箱车重参数的中位值')
      x = sltCAN['Engine Power']>0
      subcol6.metric(label='功耗(kwh):', value=np.round(sum(sltCAN.loc[x, 'Engine Power'])/3600, 2))


      
    with tab2: ################################# 发动机

      col1, col2 = st.columns(2, gap='large')
      egLoad_EgSpd_Bubble = fun.plotBubble(sltCAN, 'Engine_Speed', 'Net_Engine_Torque', 100, 200, torq)
      col1.plotly_chart(egLoad_EgSpd_Bubble, theme="streamlit")

      pie_CCPO = fun.plotPie('CCPO', sltCAN, 'Combustion_Control_Path_Owner')
      col1.plotly_chart(pie_CCPO, theme="streamlit")


      sca_ABT = fun.plotABT(sltCAN)
      col2.plotly_chart(sca_ABT,  use_container_width=True)

      chi_CCPO = fun.plotPie('Chi表', sltCAN, 'CBR_Chi_Table_Mask')
      col2.plotly_chart(chi_CCPO, theme="streamlit")

      cltHist = fun.plotHist(sltCAN, 'Coolant_Temperature', 2)
      st.plotly_chart(cltHist, theme="streamlit", use_container_width=True)

      oilHist = fun.plotHist(sltCAN, 'Oil_Temperature', 2)
      st.plotly_chart(oilHist, theme="streamlit", use_container_width=True)


    with tab3: ################################# 变速箱
      # st.subheader('', )
      # shift = st.radio('换挡点分布', options=['升档', '降档'])
      
      gearHist = fun.plotHist(sltCAN, 'J39_CurrentGear', 1)
      st.plotly_chart(gearHist, theme="streamlit", use_container_width=True)

      col1, col2 = st.columns(2, gap='large')
      vSpd_Gear_Bubble = fun.plotBubble(sltCAN, 'Vehicle_Speed', 'J39_CurrentGear', 5, 1, torq)
      col1.plotly_chart(vSpd_Gear_Bubble, theme="streamlit")

      egSpd_Gear_Bubble = fun.plotBubble(sltCAN, 'Engine_Speed', 'J39_CurrentGear', 100, 1, torq)
      col2.plotly_chart(egSpd_Gear_Bubble, theme="streamlit")


      col1, col2 = st.columns(2, gap='large')

      gearLab = col1.selectbox('请选择列参数', options=numberCols, index=numberCols.index('J39_CurrentGear'))
      num = col2.number_input('请选择列值', value=12)
      figBubble = fun.plotBubble(sltCAN[sltCAN[gearLab]==num], 'Engine_Speed', 'Net_Engine_Torque', 100, 200, torq)
      st.plotly_chart(figBubble, key='gearSpdTorq',theme="streamlit")

    with tab4:
      st.subheader('后处理相关参数', )
      cesLine = fun.plotLine(sltCAN, ['V_SFP_gpl_Soot_Load_Comb'], ['P_SFR_tmh_SinceActiveRegen'])
      st.plotly_chart(cesLine, theme=None, use_container_width=True)

      col1, col2 = st.columns(2, gap='large')
      P_SFR_Regen_Trigger_State = fun.plotPie('P_SFR_Regen_Trigger_State', sltCAN, 'P_SFR_Regen_Trigger_State')
      col1.plotly_chart(P_SFR_Regen_Trigger_State, theme="streamlit")

      V_SFR_Regen_Stage = fun.plotPie('V_SFR_Regen_Stage', sltCAN, 'V_SFR_Regen_Stage')
      col2.plotly_chart(V_SFR_Regen_Stage, theme="streamlit")

      x = fun.plotBox('箱线图', sltCAN, 'V_SCR5_pc_CE_for_Ctrl')
      st.plotly_chart(x, theme="streamlit", use_container_width=True)

      scrBedHist = fun.plotHist(sltCAN, 'V_SCP_trc_SCR_Bed', 10)
      st.plotly_chart(scrBedHist, theme="streamlit", use_container_width=True)


      
    with tab5: ################################# 风扇因素
      fanSpdHist = fun.plotHist(sltCAN, 'Fan_Speed', 100)
      st.plotly_chart(fanSpdHist, theme="streamlit", use_container_width=True)

      col1, col2 = st.columns(2, gap='large')
      fanDriPie = fun.plotPie('风扇驱动状态', sltCAN, 'Fan_Drive_State')
      col1.plotly_chart(fanDriPie, theme="streamlit")

      fanSpd_EgSpd_Bubble = fun.plotBubble(sltCAN, 'Engine_Speed', 'Fan_Speed', 100, 100, torq)
      col2.plotly_chart(fanSpd_EgSpd_Bubble, theme="streamlit")


    with tab6: ################################# 环境因素
      col1, col2 = st.columns(2, gap='large')
      gradeHist = fun.plotHist(sltCAN, 'J39_Transmission_Grade', 1)
      col1.plotly_chart(gradeHist, theme="streamlit", use_container_width=True)
      altitudeHist = fun.plotHist(sltCAN, 'Altitude', 100)
      col1.plotly_chart(altitudeHist, theme="streamlit", use_container_width=True)

      massHist = fun.plotHist(sltCAN, 'J39_Transmission_Gross_Mass', 1000)
      col2.plotly_chart(massHist, theme="streamlit", use_container_width=True)
      brakePie = fun.plotPie('刹车比例', sltCAN, 'Service_Brake_Switch')
      col2.plotly_chart(brakePie, theme="streamlit", use_container_width=True)

      mme = fun.plotViolin(sltCAN, 'MME_Vehicle_Mass')
      st.plotly_chart(mme, theme="streamlit",  use_container_width=True)

    with tab7: ################################# 驾驶因素
      accHist = fun.plotHist(sltCAN, 'Accelerator_Pedal_Position', 5)
      st.plotly_chart(accHist, theme="streamlit", use_container_width=True)

      diffNum = st.number_input(label='请输入步进大小', value=1)

      sltCAN['Diff_of_Accelerator'] = sltCAN['Accelerator_Pedal_Position'].diff(periods=diffNum)
      accDiff = fun.plotScatter(sltCAN, 'Vehicle_Speed', 'Diff_of_Accelerator')
      st.plotly_chart(accDiff, theme="streamlit",  use_container_width=True)

      

    with tab8: ################################# 自定义
      st.subheader('自定义图像', )
      col1, col2 = st.columns(2, gap='large')
      bubbleXlab = col1.selectbox('请选择x轴参数', options=numberCols, index=numberCols.index('Engine_Speed'), key='bubbleXColumn')
      bubbleYlab = col1.selectbox('请选择y轴参数', options=numberCols, index=numberCols.index('Net_Engine_Torque'), key='bubbleYColumn')
      bubbleXbin = col2.number_input('请选择x轴区间密度', value=100, key='bubbleXSize')
      bubbleYbin = col2.number_input('请选择y轴区间密度', value=200, key='bubbleYSize')

      if (bubbleXlab!='Parameter Name') and (bubbleYlab!='Parameter Name'):
        figBubble = fun.plotBubble(sltCAN, bubbleXlab, bubbleYlab, bubbleXbin, bubbleYbin, torq)
        st.plotly_chart(figBubble, key='userDefine', use_container_width=True)
      
      col1, col2 = st.columns(2, gap='large')
      histXlab = col1.selectbox('请选择x轴参数', options=numberCols, index=numberCols.index('Engine_Speed'), key='histColumn')
      histXbin = col2.number_input('请选择x轴区间密度', value=100, key='histBinSize')

      if histXlab!='Parameter Name':
        figHist = fun.plotHist(sltCAN, histXlab, histXbin)
        st.plotly_chart(figHist, theme="streamlit", use_container_width=True)


      lineYCols = st.multiselect('请选择左纵轴参数', options=numberCols,  key='lineYCols')
      lineYYCols = st.multiselect('请选择右纵轴参数', options=numberCols, key='lineYYCols')

      if lineYCols or lineYYCols:
        figLine = fun.plotLine(sltCAN, lineYCols, lineYYCols)
        st.plotly_chart(figLine, theme=None, use_container_width=True)
