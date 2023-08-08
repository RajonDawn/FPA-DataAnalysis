import streamlit as st

sltTime2 = st.slider(label='请选择B车数据范围时间(min)', min_value=0, max_value=int(canDataset2['Time'].max()), step=5, value=(0, 60))

    sltCAN2 = canDataset2.loc[(canDataset2['Time']>sltTime2[0] )&(canDataset2['Time']<sltTime2[1])]
    fig_Alt = px.area(sltCAN2, x='Time', y='Altitude')
    st.plotly_chart(fig_Alt, theme='streamlit')


    subcol1, subcol2, subcol3, subcol4, subcol5 = st.columns(5)
    fuelUsed = sltCAN1['TI_Base_Total_Fuel_Used'].max() - sltCAN1['TI_Base_Total_Fuel_Used'].min()
    mileage = sltCAN1['TI_Vehicle_Total_Engine_Dist'].max() - sltCAN1['TI_Vehicle_Total_Engine_Dist'].min()
    with subcol1:
      st.metric(label='换挡次数:', value=fun.cal_ShiftGear(sltCAN1))
    with subcol2:
      st.metric(label='平均车速(km/h):', value=np.round(sltCAN1['Vehicle_Speed'].mean(),2))
    with subcol3:
      st.metric(label='里程(km):', value=np.round(mileage))
    with subcol4:
      st.metric(label='油耗(L/100km):', value=np.round(fuelUsed/mileage*100,2))
    with subcol5:
      st.metric(label='最大坡度:', value=np.round(sltCAN1['J39_Transmission_Grade'].max(),2))

      

    dc2 = fun.plotBubble(sltCAN2, 'Engine_Speed', 'Net_Engine_Torque')
    fig2 = px.scatter(dc2, x='Engine_Speed_rd', y='Net_Engine_Torque_rd', size='Pct_Time')
    st.plotly_chart(fig2, theme="streamlit")

    fig_EgV = px.scatter(sltCAN2, x='Vehicle_Speed', y='Engine_Speed')
    st.plotly_chart(fig_EgV, theme="streamlit")

    fig_Gear = px.histogram(sltCAN2, x="Engine_Speed")
    st.plotly_chart(fig_Gear, theme="streamlit")