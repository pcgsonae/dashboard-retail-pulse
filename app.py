# Retail Sales Dashboard 

import pandas as pd
import numpy as np
import plotly.express as px # pip install plotly-express
import plotly.graph_objects as go 
from datetime import date
from datetime import datetime
import streamlit as st # pip install streamlit 
from streamlit_option_menu import option_menu
from io import BytesIO
from xlsxwriter import Workbook

st.set_page_config(page_title = 'Retail Pulse',
                   page_icon = 'cart4',
                   layout = 'wide',
                   initial_sidebar_state= 'auto')

selected = option_menu(
  menu_title=None,
  options=["Retail Sales Turnover", "Inflation (HICP)"],
  icons=['cart4','cash-stack'],
  default_index=0,
  orientation='horizontal',
  styles={
      "container": {"padding": "0!important"},
      "icon": {"font-size": "22px"}, 
      "nav-link": {"font-size": "22px", "font-family": "sans-serif", "text-align": "center", "margin":"4px",},
      "nav-link-selected": {},
  }
)

if selected == 'Retail Sales Turnover':
  ## Creat df with data 
  @st.cache
  def get_m_data():
    retail_m = pd.read_excel('retail_data.xlsx', sheet_name = 'monthly')
    retail_m.Date = retail_m.Date.apply(lambda x: x.date())
    retail_m = retail_m.drop(retail_m[retail_m.Date < date(2010,1,1)].index)
    retail_m = retail_m[retail_m['UNIT'].str.contains('Index (2019=100)')==False]
    return retail_m
  retail_m = get_m_data()
  @st.cache
  def get_q_data():
    retail_q = pd.read_excel('retail_data.xlsx', sheet_name = 'quarterly')
    retail_q.Date = retail_q.Date.apply(lambda x: x.date())
    retail_q = retail_q.drop(retail_q[retail_q.Date < date(2010,1,1)].index)
    retail_q = retail_q[retail_q['UNIT'].str.contains('Index (2019=100)')==False]
    return retail_q
  retail_q = get_q_data()
  @st.cache
  def get_a_data():
    retail_a = pd.read_excel('retail_data.xlsx', sheet_name = 'annual')
    aux_date = retail_a['Date'].astype(str)
    retail_a['Date'] = pd.to_datetime(aux_date)
    retail_a.Date = retail_a.Date.apply(lambda x: x.date())
    retail_a = retail_a.drop(retail_a[retail_a.Date < date(2010,1,1)].index)
    retail_a = retail_a[retail_a['UNIT'].str.contains('Index (2019=100)')==False]
    return retail_a
  retail_a = get_a_data()
  retail = pd.concat([retail_m, retail_q, retail_a])
  retail['Total food and beverages'] = pd.to_numeric(retail['Total food and beverages'], errors='coerce')
  tmp = retail.select_dtypes(include=[np.number])
  retail.loc[:,tmp.columns] = np.round(tmp, 1)
  #
  # Mainpage
  #
  st.markdown("<h1 style='text-align: center; ' >Retail Sales Turnover</h1>",
            unsafe_allow_html=True)
  st.markdown("<p style='text-align: center;' >Evolution of retail sales in different countries (Source: Eurostat)</p>", unsafe_allow_html=True)
  st.markdown('##')
  #
  # ------------------------------------------------------------------------------
  # Query
  st.sidebar.header('Select the query type:')
  query_type_list = ['One country, more than one product',
                   'More than one country, one product',
                   'One country, one product, two measurements']
  query_type = st.sidebar.radio(
    'Options:',
    options=query_type_list,
    index=0,
    horizontal=True)
  st.sidebar.markdown('##')
  st.sidebar.header('Please filter here:')
  prod_list = ['Audio and video equipment and household appliances', 'Automotive fuel',
            'Clothing and footwear', 'Computer, peripheral units and software',
            'Total food and beverages',
            'Food and beverages in specializes stores', 'Health and beauty',
            'Hyper and supers', 'Total (excluding fuels)', 'Total non-food products (excluding fuels)']
  #
  if query_type in ['More than one country, one product']:
    geo = st.sidebar.multiselect(
      'Select the country:',
      options=retail['geo'].unique(),
      default = ['Portugal','Spain'])
    prod = st.sidebar.selectbox(
      'Select the product:',
      options=prod_list,
      index=9)
    indic_bt = st.sidebar.selectbox(
      'Select the measurement:',
      retail['indic_bt'].unique(),
      index=0)
  elif query_type in ['One country, more than one product']:
    geo = st.sidebar.selectbox(
      'Select the country:',
      options=retail['geo'].unique(),
      index=0)
    prod = st.sidebar.multiselect(
      'Select the product:',
      options=prod_list,
      default=['Total (excluding fuels)', 'Total food and beverages', 'Total non-food products (excluding fuels)'])
    indic_bt = st.sidebar.selectbox(
      'Select the measurement:',
      retail['indic_bt'].unique(),
      index=0)
  elif query_type in ['One country, one product, two measurements']:
    geo = st.sidebar.selectbox(
      'Select the country:',
      options = retail['geo'].unique(),
      index=0)
    prod = st.sidebar.selectbox(
      'Select the product:',
      options=prod_list,
      index=9)
    indic_bt = ['Nominal', 'Real']  
  freq = st.sidebar.selectbox(
      'Select the frequency:',
      options=retail['Freq'].unique(),
      index=0)
  left, right = st.sidebar.columns(2) 
  with left:
    if freq in ['Monthly']:
      min_date = st.selectbox(
        'Select the period:',
        options = retail.loc[retail['Freq']=='Monthly']['Date'].unique(),
        index = 120,
        format_func = lambda x: x.strftime('%b %Y'))
    elif freq in ['Quarterly']:
      min_date = st.selectbox(
        'Select the period:',
        options = retail.loc[retail['Freq']=='Quarterly']['Date'].unique(),
        index = 40, 
        format_func = lambda x: f'{x.year}Q{(x.month-1)//3+1}')
    else:
      min_date = st.selectbox(
        'Select the period:',
        options = retail.loc[retail['Freq']=='Annual']['Date'].unique(),
        index = 5, 
        format_func = lambda x: x.strftime('%Y'))
  with right:
    if freq in ['Monthly']:
      max_date = st.selectbox(
        label = ' ',
        options = retail.loc[retail['Freq']=='Monthly']['Date'].unique(),
        index = 178, 
        format_func = lambda x: x.strftime('%b %Y'))
    elif freq in ['Quarterly']:
      max_date = st.selectbox(
        label = ' ',
        options = retail.loc[retail['Freq']=='Quarterly']['Date'].unique(),
        index = 58,
        format_func = lambda x:  f'{x.year}Q{(x.month-1)//3+1}')
    else:
      max_date = st.selectbox(
        label = ' ',
        options = retail.loc[retail['Freq']=='Annual']['Date'].unique(),
        index = 14,
        format_func = lambda x: x.strftime('%Y'))
  date_test = max_date - min_date
  if date_test.days < 0:
    st.warning('The end date cannot be lower than the begin date')
    st.stop()
  elif date_test.days == 0 :
    st.warning('The end date cannot be equal to the begin date')
    st.stop()    
  if freq in ['Annual']:
    UNIT = st.sidebar.selectbox(
      'Select the unit:',
      options = ['YoY % (Current year YTD %)', 'vs 2019 % (Current year YTD %)'], 
      index = 0)
  else:  
    UNIT = st.sidebar.selectbox(
      'Select the unit:',
      options = ['YoY %', 'vs 2019 %', 'Chain %'], 
      index = 0)
  # ------------------------------------------------------------------------------
  # Query
  retail_selection = retail.query('geo == @geo & Freq == @freq & indic_bt == @indic_bt  & UNIT == @UNIT & Date >= @min_date & Date <= @max_date')
  #
  retail_selection_2 = retail.query('geo == @geo & Freq == @freq & indic_bt == @indic_bt  & UNIT == @UNIT')
  #
  retail_selection_3 = retail.query('Freq == @freq & indic_bt == @indic_bt  & UNIT == @UNIT')
  # ------------------------------------------------------------------------------
  # Top KPI 
  if query_type in ['One country, more than one product']:
    #Selection
    st.markdown('---')
    st.header(f'Selection:')
    country = retail_selection_2['geo'].iloc[-1]
    left, middle_left, middle_right, right = st.columns(4)          
    with left:
      st.subheader(f'Country: {country}')
    with middle_left:
      st.subheader(f'Frequency: {freq}')
    with middle_right:
      st.subheader(f'Unit: {UNIT}')
    with right:
      st.subheader(f'Measurement: {indic_bt}')
    if freq in ['Annual']:
      st.info('Year to Date considering available information until November 2024.')
    #KPIs
    st.markdown('---')
    # auxiliar dates for header
    if freq in ['Monthly']:
      date = retail_selection_2['Date'].iloc[-1].strftime('%B %Y')
    elif freq in ['Quarterly']:
      year = retail_selection_2['Date'].iloc[-1].year
      quarter = (retail_selection_2['Date'].iloc[-1].month-1)//3+1
      date = f'{year:}Q{quarter}'
    else:
      date = retail_selection_2['Date'].iloc[-1].strftime('%Y')
    # header
    st.header(f'Results for: {date} (last available period)')  
    # auxiliar values for KPIs
    total = (retail_selection_2['Total (excluding fuels)'].iloc[-1])
    total_1 = (retail_selection_2['Total (excluding fuels)'].iloc[-2])
    delta_total = round(total - total_1,1) 
    food = (retail_selection_2['Total food and beverages'].iloc[-1])
    food_1 = (retail_selection_2['Total food and beverages'].iloc[-2])
    delta_food = round(food - food_1,1)
    non_food = (retail_selection_2['Total non-food products (excluding fuels)'].iloc[-1])
    non_food_1 = (retail_selection_2['Total non-food products (excluding fuels)'].iloc[-2])
    delta_non_food = round(non_food - non_food_1,1)
    # KPIs
    left_column, middle_column, right_column = st.columns(3)
    if UNIT in ['YoY %'] and freq in ['Monthly']:
      date = retail_selection_2['Date'].iloc[-2].strftime('%B %Y')
      with left_column:
        if np.isnan(total) == True:
          st.metric('Total (excluding fuels) Retail Sales:',
                    f'Non disclosed info',
                    f'Updated when available',
                   delta_color='off')
        else:  
          st.metric('Total (excluding fuels) Retail Sales:',
                    f'{total} YoY %',
                    f'{delta_total} p.p (vs. {date})',
                   delta_color='off')
      with middle_column:
          st.metric('Total Food and Beverages Sales:',
                    f'{round(food,1)} YoY %',
                    f'{delta_food} p.p. (vs. {date})',
                   delta_color='off')
      with right_column:
          st. metric('Total Non Food and Beverages  (excluding fuels) Sales:',
                     f'{non_food} YoY %',
                     f'{delta_non_food} p.p. (vs. {date})',
                    delta_color='off')
    elif UNIT in ['YoY %'] and freq in ['Quarterly']:
      year = retail_selection_2['Date'].iloc[-2].year
      quarter = (retail_selection_2['Date'].iloc[-2].month-1)//3+1
      date = f'{year:}Q{quarter}'
      with left_column:
        if np.isnan(total) == True:
          st.metric('Total (excluding fuels) Retail Sales:',
                    f'Non disclosed info',
                    f'Updated when available',
                   delta_color='off')
        else:
          st.metric('Total (excluding fuels) Retail Sales:',
                    f'{total} YoY %',
                    f'{delta_total} p.p (vs. {date})',
                   delta_color='off')
      with middle_column:
        st.metric('Total Food and Beverages Sales:',
                  f'{round(food,1)} YoY %',
                  f'{delta_food} p.p. (vs. {date})',
                 delta_color='off')
      with right_column:
        st. metric('Total Non Food and Beverages (excluding fuels) Sales:',
                   f'{non_food} YoY %',
                   f'{delta_non_food} p.p. (vs. {date})',
                  delta_color='off')
    elif UNIT in ['YoY % (Current year YTD %)'] and freq in ['Annual']:
      date = retail_selection_2['Date'].iloc[-2].strftime('%Y')
      with left_column:
        if np.isnan(total) == True:
          st.metric('Total (excluding fuels) Retail Sales:',
                    f'Non disclosed info',
                    f'Updated when available',
                   delta_color='off')
        else:
          st.metric('Total (excluding fuels) Retail Sales:',
                    f'{total} YoY %',
                    f'{delta_total} p.p (vs. {date})',
                   delta_color='off')
      with middle_column:
        st.metric('Total Food and Beverages Sales:',
                  f'{round(food,1)} YoY %',
                  f'{delta_food} p.p. (vs. {date})',
                 delta_color='off')
      with right_column:
        st. metric('Total Non Food and Beverages (excluding fuels) Sales:',
                   f'{non_food} YoY %',
                   f'{delta_non_food} p.p. (vs. {date})',
                  delta_color='off')
    elif UNIT in ['Chain %'] and freq in ['Monthly']:
      date = retail_selection_2['Date'].iloc[-2].strftime('%B %Y')
      with left_column:
        if np.isnan(total) == True:
          st.metric('Total (excluding fuels) Retail Sales:',
                    f'Non disclosed info',
                    f'Updated when available',
                   delta_color='off')
        else:
          st.metric('Total (excluding fuels) Retail Sales:',
                    f'{total} MoM %',
                    f'{delta_total} p.p (vs. {date})',
                   delta_color='off')
      with middle_column:
        st.metric('Total Food and Beverages Sales:',
                  f'{round(food,1)} MoM %',
                  f'{delta_food} p.p. (vs. {date})',
                 delta_color='off')
      with right_column:
        st. metric('Total Non Food and Beverages (excluding fuels) Sales:',
                   f'{non_food} MoM %',
                   f'{delta_non_food} p.p. (vs. {date})',
                  delta_color='off')
    elif UNIT in ['Chain %'] and freq in ['Quarterly']:
      year = retail_selection_2['Date'].iloc[-2].year
      quarter = (retail_selection_2['Date'].iloc[-2].month-1)//3+1
      date = f'{year:}Q{quarter}'
      with left_column:
        if np.isnan(total) == True:
          st.metric('Total (excluding fuels) Retail Sales:',
                    f'Non disclosed info',
                    f'Updated when available',
                   delta_color='off')
        else:
          st.metric('Total (excluding fuels) Retail Sales:',
                    f'{total} QoQ %',
                    f'{delta_total} p.p (vs. {date})',
                   delta_color='off')
      with middle_column:
        st.metric('Total Food and Beverages Sales:',
                  f'{round(food,1)} QoQ %',
                  f'{delta_food} p.p. (vs. {date})',
                 delta_color='off')
      with right_column:
        st. metric('Total Non Food and Beverages (excluding fuels) Sales:',
                   f'{non_food} QoQ %',
                   f'{delta_non_food} p.p. (vs. {date})',
                  delta_color='off')
    elif UNIT in ['vs 2019 %'] and freq in ['Monthly']:
      date = retail_selection_2['Date'].iloc[-2].strftime('%B %Y')
      date_2 = retail_selection_2['Date'].iloc[-49].strftime('%B %Y') #Need to update every year
      with left_column:
        if np.isnan(total) == True:
          st.metric('Total (excluding fuels) Retail Sales:',
                    f'Non disclosed info',
                    f'Updated when available',
                   delta_color='off')
        else:
          st.metric('Total (excluding fuels) Retail Sales:',
                    f'{total} % (vs. {date_2})',
                    f'{delta_total} p.p (vs. {date})',
                   delta_color='off')
      with middle_column:
        st.metric('Total Food and Beverages Sales:',
                  f'{round(food,1)} % (vs. {date_2})',
                  f'{delta_food} p.p. (vs. {date})',
                 delta_color='off')
      with right_column:
        st. metric('Total Non Food and Beverages (excluding fuels) Sales:',
                   f'{non_food} % (vs. {date_2})',
                   f'{delta_non_food} p.p. (vs. {date})',
                  delta_color='off')
    elif UNIT in ['vs 2019 %'] and freq in ['Quarterly']:
      year = retail_selection_2['Date'].iloc[-2].year
      quarter = (retail_selection_2['Date'].iloc[-2].month-1)//3+1
      date = f'{year:}Q{quarter}'
      year_2 = retail_selection_2['Date'].iloc[-16].year
      quarter_2 = (retail_selection_2['Date'].iloc[-1].month-1)//3+1
      date_2 = f'{year_2:}Q{quarter_2}'
      with left_column:
        if np.isnan(total) == True:
          st.metric('Total (excluding fuels) Retail Sales:',
                    f'Non disclosed info',
                    f'Updated when available',
                   delta_color='off')
        else:
          st.metric('Total (excluding fuels) Retail Sales:',
                    f'{total} % (vs. {date_2})',
                    f'{delta_total} p.p (vs. {date})',
                   delta_color='off')
      with middle_column:
        st.metric('Total Food and Beverages Sales:',
                  f'{round(food,1)} % (vs. {date_2})',
                  f'{delta_food} p.p. (vs. {date})',
                 delta_color='off')
      with right_column:
        st. metric('Total Non Food and Beverages (excluding fuels) Sales:',
                   f'{non_food} % (vs. {date_2})',
                   f'{delta_non_food} p.p. (vs. {date})',
                  delta_color='off')
    elif UNIT in ['vs 2019 % (Current year YTD %)'] and freq in ['Annual']:
      date = retail_selection_2['Date'].iloc[-2].strftime('%Y')
      date_2 = retail_selection_2['Date'].iloc[-5].strftime('%Y')
      with left_column:
        if np.isnan(total) == True:
          st.metric('Total (excluding fuels) Retail Sales:',
                    f'Non disclosed info',
                    f'Updated when available',
                   delta_color='off')
        else:
          st.metric('Total (excluding fuels) Retail Sales:',
                    f'{total} % (vs. {date_2})',
                    f'{delta_total} p.p (vs. {date})',
                   delta_color='off')
      with middle_column:
        st.metric('Total Food and Beverages Sales:',
                  f'{round(food,1)} % (vs. {date_2})',
                  f'{delta_food} p.p. (vs. {date})',
                 delta_color='off')
      with right_column:
        st. metric('Total Non Food and Beverages (excluding fuels) Sales:',
                   f'{non_food} % (vs. {date_2})',
                   f'{delta_non_food} p.p. (vs. {date})',
                  delta_color='off')      
  elif query_type in ['More than one country, one product']:
    #Selection
    st.markdown('---')
    st.header('Selection')
    left_column, middle_column, middle_right, right_column = st.columns(4)
    with left_column:
      st.subheader(f'Product: {prod}')
    with middle_column:
      st.subheader(f'Frequency: {freq}')
    with middle_right:
      st.subheader(f'Unit: {UNIT}')
    with right_column:
      st.subheader(f'Measurement: {indic_bt}')
    if freq in ['Annual']:
      st.info('Year to Date considering available information until November 2024.')
    #KPIs
    st.markdown('---')
    # auxiliar dates for header
    if freq in ['Monthly']:
      date = retail_selection_2['Date'].iloc[-1].strftime('%B %Y')
    elif freq in ['Quarterly']:
      year = retail_selection_2['Date'].iloc[-1].year
      quarter = (retail_selection_2['Date'].iloc[-1].month-1)//3+1
      date = f'{year:}Q{quarter}'
    else:
      date = retail_selection_2['Date'].iloc[-1].strftime('%Y')
    # header
    st.header(f'Results for: {date} (last available period)')
    left, right = st.columns(2)
    # auxiliar values for KPIs
    pt = (retail_selection_3.loc[retail_selection_3['geo']=='Portugal'][prod].iloc[-1])
    pt_1 = (retail_selection_3.loc[retail_selection_3['geo']=='Portugal'][prod].iloc[-2])
    delta_pt = round(pt - pt_1,1)
    es = (retail_selection_3.loc[retail_selection_3['geo']=='Spain'][prod].iloc[-1])
    es_1 = (retail_selection_3.loc[retail_selection_3['geo']=='Spain'][prod].iloc[-2])
    delta_es = round(es - es_1,1)
    if UNIT in ['YoY %'] and freq in ['Monthly']:
      date = retail_selection_3['Date'].iloc[-2].strftime('%B %Y')
      with left:
        if np.isnan(pt) == True:
          st.metric('Portugal:',
                    f'Non disclosed info',
                    f'Updated when available',
                   delta_color='off')
        else:
          st.metric('Portugal:',
                    f'{pt} YoY %',
                    f'{delta_pt} p.p (vs. {date})',
                   delta_color='off')
      with right:
        if np.isnan(es) == True:
          st.metric('Spain:',
                    f'Non disclosed info',
                    f'Updated when available',
                   delta_color='off')
        else:
          st.metric('Spain:',
                    f'{es} YoY %',
                    f'{delta_es} p.p. (vs. {date})',
                   delta_color='off')
    elif UNIT in ['YoY %'] and freq in ['Quarterly']:
      year = retail_selection_3['Date'].iloc[-2].year
      quarter = (retail_selection_3['Date'].iloc[-2].month-1)//3+1
      date = f'{year:}Q{quarter}'
      with left:
        if np.isnan(pt) == True:
          st.metric('Portugal:',
                    f'Non disclosed info',
                    f'Updated when available',
                   delta_color='off')
        else:
          st.metric('Portugal:',
                    f'{pt} YoY %',
                    f'{delta_pt} p.p (vs. {date})',
                   delta_color='off')
      with right:
        if np.isnan(es) == True:
          st.metric('Spain:',
                    f'Non disclosed info',
                    f'Updated when available',
                   delta_color='off')
        else:
          st.metric('Spain:',
                    f'{es} YoY %',
                    f'{delta_es} p.p. (vs. {date})',
                   delta_color='off')
    elif UNIT in ['YoY % (Current year YTD %)'] and freq in ['Annual']:
      date = retail_selection_3['Date'].iloc[-2].strftime('%Y')
      with left:
        if np.isnan(pt) == True:
          st.metric('Portugal:',
                    f'Non disclosed info',
                    f'Updated when available',
                   delta_color='off')
        else:
          st.metric('Portugal:',
                    f'{pt} YoY %',
                    f'{delta_pt} p.p (vs. {date})',
                   delta_color='off')
      with right:
        if np.isnan(es) == True:
          st.metric('Spain:',
                    f'Non disclosed info',
                    f'Updated when available',
                   delta_color='off')
        else:
          st.metric('Spain:',
                    f'{es} YoY %',
                    f'{delta_es} p.p. (vs. {date})',
                   delta_color='off')
    elif UNIT in ['Chain %'] and freq in ['Monthly']:
      date = retail_selection_3['Date'].iloc[-2].strftime('%B %Y')
      with left:
        if np.isnan(pt) == True:
          st.metric('Portugal:',
                    f'Non disclosed info',
                    f'Updated when available',
                   delta_color='off')
        else:
          st.metric('Portugal:',
                    f'{pt} MoM %',
                    f'{delta_pt} p.p (vs. {date})',
                   delta_color='off')
      with right:
        if np.isnan(es) == True:
          st.metric('Spain:',
                    f'Non disclosed info',
                    f'Updated when available',
                   delta_color='off')
        else:
          st.metric('Spain:',
                    f'{es} MoM %',
                    f'{delta_es} p.p. (vs. {date})',
                   delta_color='off')
    elif UNIT in ['Chain %'] and freq in ['Quarterly']:
      year = retail_selection_3['Date'].iloc[-2].year
      quarter = (retail_selection_3['Date'].iloc[-2].month-1)//3+1
      date = f'{year:}Q{quarter}'
      with left:
        if np.isnan(pt) == True:
          st.metric('Portugal:',
                    f'Non disclosed info',
                    f'Updated when available',
                   delta_color='off')
        else:
          st.metric('Portugal:',
                    f'{pt} QoQ %',
                    f'{delta_pt} p.p (vs. {date})',
                   delta_color='off')
      with right:
        if np.isnan(es) == True:
          st.metric('Spain:',
                    f'Non disclosed info',
                    f'Updated when available',
                   delta_color='off')
        else:
          st.metric('Spain:',
                    f'{es} QoQ %',
                    f'{delta_es} p.p. (vs. {date})',
                   delta_color='off')
    elif UNIT in ['vs 2019 %'] and freq in ['Monthly']:
      date = retail_selection_3['Date'].iloc[-2].strftime('%B %Y')
      date_2 = retail_selection_3['Date'].iloc[-49].strftime('%B %Y') #Need to update every year
      with left:
        if np.isnan(pt) == True:
          st.metric('Portugal:',
                    f'Non disclosed info',
                    f'Updated when available',
                   delta_color='off')
        else:
          st.metric('Portugal:',
                    f'{pt} % (vs. {date_2})',
                    f'{delta_pt} p.p (vs. {date})',
                   delta_color='off')
      with right:
        if np.isnan(es) == True:
          st.metric('Spain:',
                    f'Non disclosed info',
                    f'Updated when available',
                   delta_color='off')
        else:
          st.metric('Spain:',
                    f'{es} % (vs. {date_2})',
                    f'{delta_es} p.p. (vs. {date})',
                   delta_color='off')
    elif UNIT in ['vs 2019 %'] and freq in ['Quarterly']:
      year = retail_selection_3['Date'].iloc[-2].year
      quarter = (retail_selection_3['Date'].iloc[-2].month-1)//3+1
      date = f'{year:}Q{quarter}'
      year_2 = retail_selection_3['Date'].iloc[-16].year
      quarter_2 = (retail_selection_3['Date'].iloc[-1].month-1)//3+1
      date_2 = f'{year_2:}Q{quarter_2}'
      with left:
        if np.isnan(pt) == True:
          st.metric('Portugal:',
                    f'Non disclosed info',
                    f'Updated when available',
                   delta_color='off')
        else:
          st.metric('Portugal:',
                    f'{pt} % (vs. {date_2})',
                    f'{delta_pt} p.p (vs. {date})',
                   delta_color='off')
      with right:
        if np.isnan(es) == True:
          st.metric('Spain:',
                    f'Non disclosed info',
                    f'Updated when available',
                   delta_color='off')
        else:
          st.metric('Spain:',
                    f'{es} % (vs. {date_2})',
                    f'{delta_es} p.p. (vs. {date})',
                   delta_color='off')
    elif UNIT in ['vs 2019 % (Current year YTD %)'] and freq in ['Annual']:
      date = retail_selection_3['Date'].iloc[-2].strftime('%Y')
      date_2 = retail_selection_3['Date'].iloc[-5].strftime('%Y')
      with left:
        if np.isnan(pt) == True:
          st.metric('Portugal:',
                    f'Non disclosed info',
                    f'Updated when available',
                   delta_color='off')
        else:
          st.metric('Portugal:',
                    f'{pt} % (vs. {date_2})',
                    f'{delta_pt} p.p (vs. {date})',
                   delta_color='off')
      with right:
        if np.isnan(es) == True:
          st.metric('Spain:',
                    f'Non disclosed info',
                    f'Updated when available',
                   delta_color='off')
        else:
          st.metric('Spain:',
                    f'{es} % (vs. {date_2})',
                    f'{delta_es} p.p. (vs. {date})',
                   delta_color='off')       
  elif query_type in ['One country, one product, two measurements']:
    #Selection
    st.markdown('---')
    st.header('Selection')
    country = retail_selection_2['geo'].iloc[-1]
    left_column, middle_column, middle_right, right_column = st.columns(4)
    with left_column:
      st.subheader(f'Country: {country}')
    with middle_column:
      st.subheader(f'Product: {prod}')
    with middle_right:
      st.subheader(f'Unit: {UNIT}')
    with right_column:
      st.subheader(f'Frequency: {freq}')
    if freq in ['Annual']:
      st.info('Year to Date considering available information until November 2024.')
    #KPIs
    st.markdown('---')
    # auxiliar dates for header
    if freq in ['Monthly']:
      date = retail_selection_2['Date'].iloc[-1].strftime('%B %Y')
    elif freq in ['Quarterly']:
      year = retail_selection_2['Date'].iloc[-1].year
      quarter = (retail_selection_2['Date'].iloc[-1].month-1)//3+1
      date = f'{year:}Q{quarter}'
    else:
      date = retail_selection_2['Date'].iloc[-1].strftime('%Y')
    # header
    st.header(f'Results for: {date} (last available period)')
    left, right = st.columns(2)
    # auxiliar values for KPIs
    nom = (retail_selection_2.loc[retail_selection_2['indic_bt']=='Nominal'][prod].iloc[-1])
    nom_1 = (retail_selection_2.loc[retail_selection_2['indic_bt']=='Nominal'][prod].iloc[-2])
    delta_nom = round(nom - nom_1,1)
    real = (retail_selection_2.loc[retail_selection_2['indic_bt']=='Real'][prod].iloc[-1])
    real_1 = (retail_selection_2.loc[retail_selection_2['indic_bt']=='Real'][prod].iloc[-2])
    delta_real = round(real - real_1,1)
    if UNIT in ['YoY %'] and freq in ['Monthly']:
      date = retail_selection_2['Date'].iloc[-2].strftime('%B %Y')
      with left:
        if np.isnan(nom) == True:
          st.metric('Nominal:',
                    f'Non disclosed info',
                    f'Updated when available',
                   delta_color='off')
        else:
          st.metric('Nominal:',
                    f'{nom} YoY %',
                    f'{delta_nom} p.p (vs. {date})',
                   delta_color='off')
      with right:
        if np.isnan(real) == True:
          st.metric('Real:',
                    f'Non disclosed info',
                    f'Updated when available',
                   delta_color='off')
        else:
          st.metric('Real:',
                    f'{real} YoY %',
                    f'{delta_real} p.p. (vs. {date})',
                   delta_color='off')
    elif UNIT in ['YoY %'] and freq in ['Quarterly']:
      year = retail_selection_2['Date'].iloc[-2].year
      quarter = (retail_selection_2['Date'].iloc[-2].month-1)//3+1
      date = f'{year:}Q{quarter}'
      with left:
        if np.isnan(nom) == True:
          st.metric('Nominal:',
                    f'Non disclosed info',
                    f'Updated when available',
                   delta_color='off')
        else:
          st.metric('Nominal:',
                    f'{nom} YoY %',
                    f'{delta_nom} p.p (vs. {date})',
                   delta_color='off')
      with right:
        if np.isnan(real) == True:
          st.metric('Real:',
                    f'Non disclosed info',
                    f'Updated when available',
                   delta_color='off')
        else:
          st.metric('Real:',
                    f'{real} YoY %',
                    f'{delta_real} p.p. (vs. {date})',
                   delta_color='off')
    elif UNIT in ['YoY % (Current year YTD %)'] and freq in ['Annual']:
      date = retail_selection_2['Date'].iloc[-2].strftime('%Y')
      with left:
        if np.isnan(nom) == True:
          st.metric('Nominal:',
                    f'Non disclosed info',
                    f'Updated when available',
                   delta_color='off')
        else:
          st.metric('Nominal:',
                    f'{nom} YoY %',
                    f'{delta_nom} p.p (vs. {date})',
                   delta_color='off')
      with right:
        if np.isnan(real) == True:
          st.metric('Real:',
                    f'Non disclosed info',
                    f'Updated when available',
                   delta_color='off')
        else:
          st.metric('Real:',
                    f'{real} YoY %',
                    f'{delta_real} p.p. (vs. {date})',
                   delta_color='off')
    elif UNIT in ['Chain %'] and freq in ['Monthly']:
      date = retail_selection_2['Date'].iloc[-2].strftime('%B %Y')
      with left:
        if np.isnan(nom) == True:
          st.metric('Nominal:',
                    f'Non disclosed info',
                    f'Updated when available',
                   delta_color='off')
        else:
          st.metric('Nominal:',
                    f'{nom} MoM %',
                    f'{delta_nom} p.p (vs. {date})',
                   delta_color='off')
      with right:
        if np.isnan(real) == True:
          st.metric('Real:',
                    f'Non disclosed info',
                    f'Updated when available',
                   delta_color='off')
        else:
          st.metric('Real:',
                    f'{real} MoM %',
                    f'{delta_real} p.p. (vs. {date})',
                   delta_color='off')
    elif UNIT in ['Chain %'] and freq in ['Quarterly']:
      year = retail_selection_2['Date'].iloc[-2].year
      quarter = (retail_selection_2['Date'].iloc[-2].month-1)//3+1
      date = f'{year:}Q{quarter}'
      with left:
        if np.isnan(nom) == True:
          st.metric('Nominal:',
                    f'Non disclosed info',
                    f'Updated when available',
                   delta_color='off')
        else:
          st.metric('Nominal:',
                    f'{nom} QoQ %',
                    f'{delta_nom} p.p (vs. {date})',
                   delta_color='off')
      with right:
        if np.isnan(real) == True:
          st.metric('Real:',
                    f'Non disclosed info',
                    f'Updated when available',
                   delta_color='off')
        else:
          st.metric('Real:',
                    f'{real} QoQ %',
                    f'{delta_real} p.p. (vs. {date})',
                   delta_color='off')
    elif UNIT in ['vs 2019 %'] and freq in ['Monthly']:
      date = retail_selection_2['Date'].iloc[-2].strftime('%B %Y')
      date_2 = retail_selection_2['Date'].iloc[-49].strftime('%B %Y') #Need to update every year
      with left:
        if np.isnan(nom) == True:
          st.metric('Nominal:',
                    f'Non disclosed info',
                    f'Updated when available',
                   delta_color='off')
        else:
          st.metric('Nominal:',
                    f'{nom} % (vs. {date_2})',
                    f'{delta_nom} p.p (vs. {date})',
                   delta_color='off')
      with right:
        if np.isnan(real) == True:
          st.metric('Real:',
                    f'Non disclosed info',
                    f'Updated when available',
                   delta_color='off')
        else:
          st.metric('Real:',
                    f'{real} % (vs. {date_2})',
                    f'{delta_real} p.p. (vs. {date})',
                   delta_color='off')
    elif UNIT in ['vs 2019 %'] and freq in ['Quarterly']:
      year = retail_selection_2['Date'].iloc[-2].year
      quarter = (retail_selection_2['Date'].iloc[-2].month-1)//3+1
      date = f'{year:}Q{quarter}'
      year_2 = retail_selection_2['Date'].iloc[-16].year
      quarter_2 = (retail_selection_2['Date'].iloc[-1].month-1)//3+1
      date_2 = f'{year_2:}Q{quarter_2}'
      with left:
        if np.isnan(nom) == True:
          st.metric('Nominal:',
                    f'Non disclosed info',
                    f'Updated when available',
                   delta_color='off')
        else:
          st.metric('Nominal:',
                    f'{nom} % (vs. {date_2})',
                    f'{delta_nom} p.p (vs. {date})',
                   delta_color='off')
      with right:
        if np.isnan(real) == True:
          st.metric('Real:',
                    f'Non disclosed info',
                    f'Updated when available',
                   delta_color='off')
        else:
          st.metric('Real:',
                    f'{real} % (vs. {date_2})',
                    f'{delta_real} p.p. (vs. {date})',
                   delta_color='off')
    elif UNIT in ['vs 2019 % (Current year YTD %)'] and freq in ['Annual']:
      date = retail_selection_2['Date'].iloc[-2].strftime('%Y')
      date_2 = retail_selection_2['Date'].iloc[-5].strftime('%Y')
      with left:
        if np.isnan(nom) == True:
          st.metric('Nominal:',
                    f'Non disclosed info',
                    f'Updated when available',
                   delta_color='off')
        else:
          st.metric('Nominal:',
                    f'{nom} % (vs. {date_2})',
                    f'{delta_nom} p.p (vs. {date})',
                   delta_color='off')
      with right:
        if np.isnan(real) == True:
          st.metric('Real:',
                    f'Non disclosed info',
                    f'Updated when available',
                   delta_color='off')
        else:
          st.metric('Real:',
                    f'{real} % (vs. {date_2})',
                    f'{delta_real} p.p. (vs. {date})',
                   delta_color='off')    
  #
  # ------------------------------------------------------------------------------
  st.markdown('---')
  #
  prod = np.array(prod)
  col_list = ['Date', 'geo', 'indic_bt']
  columns = np.append(col_list,prod)
  df = pd.DataFrame(retail_selection, columns=columns)
  df[prod] = df[prod].apply(pd.to_numeric, errors='coerce')
  #df[columns] = df.round(decimals=1)
  #
  # Plot
  if query_type in ['One country, more than one product']:
    st.header('Graph')
    fig_plot = px.line(
        df,
        x='Date',
        y=prod,
        orientation='v',
        template='seaborn')
    fig_plot.update_traces(
        mode='markers+lines', 
        hovertemplate=None)
    if UNIT in ['Index (2019=100)']:
        fig_plot.update_yaxes(title="Index (2019=100)", showspikes=True, tickfont_size = 18)
    else:
        fig_plot.update_yaxes(title="%", showspikes=True, tickfont_size = 18)
    if freq in ['Annual']:
      fig_plot.update_xaxes(title="",
                            autorange = True,
                            rangeslider_visible=True,
                            rangeselector_visible=True,
                            tickformat = "%Y",
                            dtick = 'M12',
                            showspikes=True, 
                            tickfont_size = 18)
    else: 
      fig_plot.update_xaxes(title="",
                            autorange = True,
                            rangeslider_visible=True,
                            rangeselector_visible=True,
                            showspikes=True,
                            tickfont_size = 18)
    fig_plot.update_layout(  # customize font and legend orientation & position
        hovermode="x",
        legend=dict(
            title=None, orientation="h",  x=0.5, xanchor="center", font=dict(size=18)),
        hoverlabel_font_size=18)
    fig_plot.update_layout(
        autosize=True,
        height=500,
        margin=dict(l=50, r=50, t=50, b=20),)
    fig_plot.update_layout(
        plot_bgcolor="rgb(240,240,235)")
    st.plotly_chart(fig_plot, use_container_width=True)
  if query_type in ['More than one country, one product']:
    st.header('Graph')
    df2 = df.pivot(index=['Date', 'indic_bt'], columns=['geo'], values=prod)
    df2 = df2.reset_index(level=['Date', 'indic_bt'])
    fig_plot = px.line(
        df2,
        x='Date',
        y=geo,
        orientation='v',
        template='seaborn')
    fig_plot.update_traces(mode='markers+lines', hovertemplate=None)
    if UNIT in ['Index (2019=100)']:
        fig_plot.update_yaxes(title="Index (2019=100)", showspikes=True,tickfont_size = 18)
    else:
        fig_plot.update_yaxes(title="%", showspikes=True,tickfont_size = 18)
    if freq in ['Annual']:
      fig_plot.update_xaxes(title="",
                            autorange = True,
                            rangeslider_visible=True,
                            rangeselector_visible=True,
                            tickformat = "%Y",
                            dtick = "M12",
                            showspikes=True,
                            tickfont_size = 18)
    elif freq in ['Quarterly']:
      fig_plot.update_xaxes(title="",
                            autorange = True,
                            rangeslider_visible=True,
                            rangeselector_visible=True,
                            showspikes=True,
                            tickfont_size = 18)   
    else: 
      fig_plot.update_xaxes(title="",
                            autorange = True,
                            rangeslider_visible=True,
                            rangeselector_visible=True,
                            showspikes=True,
                            tickfont_size = 18)
    fig_plot.update_layout(  # customize font and legend orientation & position
        hovermode="x",
        legend=dict(
            title=None, orientation="h",  x=0.5, xanchor="center", font=dict(size=18)),
        hoverlabel_font_size=18)
    fig_plot.update_layout(
        autosize=True,
        height=500,
        margin=dict(l=50, r=50, t=50, b=20),)
    fig_plot.update_layout(
        plot_bgcolor="rgb(240,240,235)")
    st.plotly_chart(fig_plot, use_container_width=True)
  if query_type in ['One country, one product, two measurements']:
    st.header('Graph')
    df3 = df.pivot(index=['Date', 'geo',], columns=['indic_bt'], values=prod)
    df3 = df3.reset_index(level=['Date', 'geo'])
    fig_plot = px.line(
        df3,
        x='Date',
        y=indic_bt,
        orientation='v',
        template='seaborn')
    fig_plot.update_traces(mode='markers+lines', hovertemplate=None)
    if UNIT in ['Index (2019=100)']:
        fig_plot.update_yaxes(title="Index (2019=100)", showspikes=True,tickfont_size = 18)
    else:
        fig_plot.update_yaxes(title="%", showspikes=True,tickfont_size = 18)
    if freq in ['Annual']:
      fig_plot.update_xaxes(title="",
                            autorange = True,
                            rangeslider_visible=True,
                            rangeselector_visible=True,
                            tickformat = "%Y",
                            dtick = "M12",
                            showspikes=True,
                            tickfont_size = 18)
    elif freq in ['Quarterly']:
      fig_plot.update_xaxes(title="",
                            autorange = True,
                            rangeslider_visible=True,
                            rangeselector_visible=True,
                            showspikes=True,
                            tickfont_size = 18)
    else: 
      fig_plot.update_xaxes(title="",
                            autorange = True,
                            rangeslider_visible=True,
                            rangeselector_visible=True, 
                            showspikes=True,
                            tickfont_size = 18)
    fig_plot.update_layout(  # customize font and legend orientation & position
        hovermode="x",
        legend=dict(
            title=None, orientation="h",  x=0.5, xanchor="center", font=dict(size=18)),
        hoverlabel_font_size=18)
    fig_plot.update_layout(
        autosize=True,
        height=500,
        margin=dict(l=50, r=50, t=50, b=20),)
    fig_plot.update_layout(
        plot_bgcolor="rgb(240,240,235)")
    st.plotly_chart(fig_plot, use_container_width=True)
  #
  # Table
  st.header('Table')
  #
  df = df.reset_index(drop=False)
  df = df.rename(columns={'geo': 'Country', 'indic_bt': 'Measurement'})
  df = df.drop(columns=['index'])
  df.sort_values(by='Date', ascending = False, inplace=True)
  #
  if query_type in ['One country, more than one product']:
    @st.cache
    def convert_df_xlsx(df):
        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        num_col = len(df.columns)
        df.to_excel(writer, index=False, sheet_name='Sheet1')
        workbook = writer.book
        worksheet = writer.sheets['Sheet1']
        format1 = workbook.add_format({'num_format': '0.00'})
        worksheet.set_column(0, num_col, 30, format1)
        writer.close()
        processed_data = output.getvalue()
        return processed_data
    xlsx = convert_df_xlsx(df)
    st.download_button('Download selected data as xlsx', 
                        data=xlsx, file_name='retail_data.xlsx')
    fig = go.Figure(data=go.Table(
      header=dict(values=list(df.columns),
                  fill_color = '#99C7FF',
                  align='center',
                  font=dict(size=16),
                  height=50),
      cells=dict(values=df.transpose().values.tolist(),
                 fill_color = '#F0F0EB',
                 align='center',
                 font=dict(size=15),
                 height=30)))
    fig.update_layout(
        autosize=True,
        height=500,
        margin=dict(l=10, r=10, t=10, b=20))
    st.plotly_chart(fig,use_container_width=True)    
  if query_type in ['More than one country, one product']:
    df2 = df2.set_index(['Date', 'indic_bt'])
    df2 = df2.reset_index(drop=False)
    df2 = df2.rename(columns={'geo': 'Country', 'indic_bt': 'Measurement'})
    df2.sort_values(by='Date', ascending = False, inplace=True)
    @st.cache
    def convert_df_xlsx(df2):
        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        num_col = len(df2.columns)
        df2.to_excel(writer, index=False, sheet_name='Sheet1')
        workbook = writer.book
        worksheet = writer.sheets['Sheet1']
        format1 = workbook.add_format({'num_format': '0.0'})
        worksheet.set_column(0, num_col, 30, format1)
        writer.close()
        processed_data = output.getvalue()
        return processed_data
    xlsx = convert_df_xlsx(df2)
    st.download_button('Download selected data as xlsx',
                       data=xlsx, file_name='retail_data.xlsx')
    fig = go.Figure(data=go.Table(
      header=dict(values=list(df2.columns),
                  fill_color = '#99C7FF',
                  align='center',
                  font=dict(size=16),
                  height=50),
      cells=dict(values=df2.transpose().values.tolist(),
                 fill_color = '#F0F0EB',
                 align='center',
                 font=dict(size=15),
                 height=30)))
    fig.update_layout(
        autosize=True,
        height=500,
        margin=dict(l=10, r=10, t=10, b=20))
    st.plotly_chart(fig,use_container_width=True)
  if query_type in ['One country, one product, two measurements']:
    df3 = df3.set_index(['Date', 'geo'])
    df3 = df3.reset_index(drop=False)
    df3 = df3.rename(columns={'geo': 'Country', 'indic_bt': 'Measurement'})
    df3.sort_values(by='Date', ascending = False, inplace=True)
    @st.cache
    def convert_df_xlsx(df3):
        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        num_col = len(df3.columns)
        df3.to_excel(writer, index=False, sheet_name='Sheet1')
        workbook = writer.book
        worksheet = writer.sheets['Sheet1']
        format1 = workbook.add_format({'num_format': '0.0'})
        worksheet.set_column(0, num_col, 30, format1)
        writer.close()
        processed_data = output.getvalue()
        return processed_data
    xlsx = convert_df_xlsx(df3)
    st.download_button('Download selected data as xlsx',
                       data=xlsx, file_name='retail_data.xlsx')
    fig = go.Figure(data=go.Table(
      header=dict(values=list(df3.columns),
                  fill_color = '#99C7FF',
                  align='center',
                  font=dict(size=16),
                  height=50),
      cells=dict(values=df3.transpose().values.tolist(),
                 fill_color = '#F0F0EB',
                 align='center',
                 font=dict(size=15),
                 height=30)))
    fig.update_layout(
        autosize=True,
        height=500,
        margin=dict(l=10, r=10, t=10, b=20))
    st.plotly_chart(fig,use_container_width=True)

    
##------------------------------------------------------------------------------------------------------------------------------------------------------------------##    
    
  
if selected == 'Inflation (HICP)':
  ## Creat df with data 
  @st.cache
  def get_m_data():
      hicp_m = pd.read_excel('hicp_data.xlsx',
                             sheet_name='monthly', usecols = 'B:M')
      hicp_m.Date = hicp_m.Date.apply(lambda x: x.date())
      hicp_m = hicp_m.drop(hicp_m[hicp_m.Date < date(2010,1,1)].index)
      return hicp_m
  hicp_m = get_m_data()
  @st.cache
  def get_q_data():
      hicp_q = pd.read_excel('hicp_data.xlsx',
                             sheet_name='quarterly', usecols = 'B:M')
      aux_date = hicp_q['Date'].astype(str)
      hicp_q['Date'] = pd.to_datetime(aux_date)
      hicp_q.Date = hicp_q.Date.apply(lambda x: x.date())
      hicp_q = hicp_q.drop(hicp_q[hicp_q.Date < date(2010,1,1)].index)
      return hicp_q
  hicp_q = get_q_data()
  @st.cache
  def get_a_data():
      hicp_a = pd.read_excel('hicp_data.xlsx',
                             sheet_name='annual', usecols = 'B:M')
      aux_date = hicp_a['Date'].astype(str)
      hicp_a['Date'] = pd.to_datetime(aux_date)
      hicp_a.Date = hicp_a.Date.apply(lambda x: x.date())
      hicp_a = hicp_a.drop(hicp_a[hicp_a.Date < date(2010,1,1)].index)
      return hicp_a
  hicp_a = get_a_data()
  hicp = pd.concat([hicp_m, hicp_q, hicp_a])
  tmp = hicp.select_dtypes(include=[np.number])
  hicp.loc[:,tmp.columns] = np.round(tmp, 1)
  # Mainpage
  st.markdown("<h1 style='text-align: center; ' >Harmonized Indices of Consumer Prices</h1>",
              unsafe_allow_html=True)
  st.markdown("<p style='text-align: center;' >Evolution of inflation (HICP) in different countries (Source: Eurostat)</p>", unsafe_allow_html=True)
  st.markdown('##')
  #------------------------------------------------------------------------------
  st.sidebar.header('Select the query type:')
  query_type_list = ['One country, more than one product',
                     'More than one country, one product']
  query_type = st.sidebar.radio(
      'Options:',
      options=query_type_list,
      index=0,
      horizontal=True)
  st.sidebar.markdown('##')
  st.sidebar.header('Please filter here:')
  prod_list = ['Audio-visual, photo. and inform. equipm.',
               'Clothing and footwear', 'Food and non-alcoholic beverages', 
               'Fuels', 'Household appliances', 
               'Medical products, appliances and equipment',
               'Overall excl. energy and unprocessed food', 'Total']
  if query_type in ['More than one country, one product']:
      geo = st.sidebar.multiselect(
          'Select the country:',
          options=hicp['Geo'].unique(),
          default=['Portugal', 'Spain'])
      prod = st.sidebar.selectbox(
          'Select the product:',
          options=prod_list,
          index=7)
  elif query_type in ['One country, more than one product']:
      geo = st.sidebar.selectbox(
          'Select the country:',
          options=hicp['Geo'].unique(),
          index=0)
      prod = st.sidebar.multiselect(
          'Select the product:',
          options=prod_list,
          default=['Total', 'Food and non-alcoholic beverages', 'Overall excl. energy and unprocessed food', 'Fuels'])
  freq = st.sidebar.selectbox(
      'Select the frequency:',
      options=hicp['freq'].unique(),
      index=0
  )
  if freq in ['Annual']:
    UNIT = 'YoY % (Current year YTD %)'
    st.sidebar.info('YoY % (Current year YTD %)')
  else:  
    UNIT = st.sidebar.selectbox(
      'Select the unit:',
      options=['YoY %', "Chain %"],
      index=0)  
  left, right = st.sidebar.columns(2) 
  with left:
    if freq in ['Monthly']:
      min_date = st.selectbox(
        'Select the period:',
        options = hicp.loc[hicp['freq']=='Monthly']['Date'].unique(),
        index = 120,
        format_func = lambda x: x.strftime('%b %Y'))
    elif freq in ['Quarterly']:
      min_date = st.selectbox(
        'Select the period:',
        options = hicp.loc[hicp['freq']=='Quarterly']['Date'].unique(),
        index = 40, 
        format_func = lambda x: f'{x.year}Q{(x.month-1)//3+1}')
    else:
      min_date = st.selectbox(
        'Select the period:',
        options = hicp.loc[hicp['freq']=='Annual']['Date'].unique(),
        index = 5, 
        format_func = lambda x: x.strftime('%Y'))
  with right:
    if freq in ['Monthly']:
      max_date = st.selectbox(
        label = ' ',
        options = hicp.loc[hicp['freq']=='Monthly']['Date'].unique(),
        index = 177, 
        format_func = lambda x: x.strftime('%b %Y'))
    elif freq in ['Quarterly']:
      max_date = st.selectbox(
        label = ' ',
        options = hicp.loc[hicp['freq']=='Quarterly']['Date'].unique(),
        index = 58,
        format_func = lambda x:  f'{x.year}Q{(x.month-1)//3+1}')
    else:
      max_date = st.selectbox(
        label = ' ',
        options = hicp.loc[hicp['freq']=='Annual']['Date'].unique(),
        index = 14,
        format_func = lambda x: x.strftime('%Y'))
  #
  date_test = max_date - min_date
  if date_test.days < 0:
    st.warning('The end date cannot be lower than the begin date')
    st.stop()
  elif date_test.days == 0 :
    st.warning('The end date cannot be equal to the begin date')
    st.stop()
  #  
  # ------------------------------------------------------------------------------
  # Query
  hicp_selection = hicp.query('Geo == @geo & freq == @freq  & Unit == @UNIT & Date >= @min_date & Date <= @max_date')
  #
  hicp_selection_2 = hicp.query('Geo == @geo & freq == @freq & Unit == @UNIT')
  #
  hicp_selection_3 = hicp.query('freq == @freq & Unit == @UNIT')
  # ------------------------------------------------------------------------------
  # Top KPI 
  if query_type in ['One country, more than one product']:
      #Selection
      st.markdown('---')
      st.header(f'Selection:')
      country = hicp_selection_2['Geo'].iloc[-1]
      left, middle, right = st.columns(3)          
      with left:
        st.subheader(f'Country: {country}')
      with middle:
        st.subheader(f'Frequency: {freq}')
      with right:
        st.subheader(f'Unit: {UNIT}')
      if freq in ['Annual']:
        st.info('Year to Date considering available information until November 2024.')
      #KPIs
      st.markdown('---')
      # auxiliar dates for header
      if freq in ['Monthly']:
        date = hicp_selection_2['Date'].iloc[-1].strftime('%B %Y')
      elif freq in ['Quarterly']:
        year = hicp_selection_2['Date'].iloc[-1].year
        quarter = (hicp_selection_2['Date'].iloc[-1].month-1)//3+1
        date = f'{year:}Q{quarter}'
      else:
        date = hicp_selection_2['Date'].iloc[-1].strftime('%Y')
      # header
      st.header(f'Results for: {date} (last available period)')  
      # auxiliar values for KPIs
      total = (hicp_selection_2['Total'].iloc[-1])
      total_1 = (hicp_selection_2['Total'].iloc[-2])
      delta_total = round(total - total_1,1)
      food = (hicp_selection_2['Food and non-alcoholic beverages'].iloc[-1])
      food_1 = (hicp_selection_2['Food and non-alcoholic beverages'].iloc[-2])
      delta_food = round(food - food_1,1)
      core = (hicp_selection_2['Overall excl. energy and unprocessed food'].iloc[-1])
      core_1 = (hicp_selection_2['Overall excl. energy and unprocessed food'].iloc[-2])
      delta_core = round(core - core_1,1)
      energy = (hicp_selection_2['Fuels'].iloc[-1])
      energy_1 = (hicp_selection_2['Fuels'].iloc[-2])
      delta_energy = round(energy - energy_1,1)
      # KPIs
      left_column, middle_column, middle_2_column, right_column = st.columns(4)
      if UNIT in ['YoY %'] and freq in ['Monthly']:
        date = hicp_selection_2['Date'].iloc[-2].strftime('%B %Y')
        #date_2 = hicp_selection_2['Date'].iloc[-3].strftime('%B %Y')
        with left_column:
            st.metric('Total:',
                      f'{total} YoY %',
                      f'{delta_total} p.p (vs. {date})',
                     delta_color='off')
        with middle_column:
            st.metric('Food and non-alcoholic beverages:',
                      f'{food} YoY %',
                      f'{delta_food} p.p. (vs. {date})',
                     delta_color='off')
        with middle_2_column:
            st.metric('Fuels:',
                      f'{energy} YoY %',
                      f'{delta_energy} p.p. (vs. {date})',
                     delta_color='off')    
        with right_column:
            st. metric('Overall excl. energy and unprocessed food:',
                       f'{core} YoY %',
                       f'{delta_core} p.p. (vs. {date})',
                      delta_color='off')
      elif UNIT in ['YoY %'] and freq in ['Quarterly']:
        year = hicp_selection_2['Date'].iloc[-2].year
        quarter = (hicp_selection_2['Date'].iloc[-2].month-1)//3+1
        date = f'{year:}Q{quarter}'
        #year_2 = hicp_selection_2['Date'].iloc[-3].year
        #quarter_2 = (hicp_selection_2['Date'].iloc[-3].month-1)//3+1
        #date_2 = f'{year_2:}Q{quarter_2}'
        with left_column:
          st.metric('Total:',
                    f'{total} YoY %',
                    f'{delta_total} p.p (vs. {date})',
                   delta_color='off')
        with middle_column:
          st.metric('Food and non-alcoholic beverages:',
                    f'{food} YoY %',
                    f'{delta_food} p.p. (vs. {date})',
                   delta_color='off')
        with middle_2_column:
          st.metric('Fuels:',
                    f'{energy} YoY %',
                    f'{delta_energy} p.p. (vs. {date})',
                   delta_color='off')   
        with right_column:
          st. metric('Overall excl. energy and unprocessed food:',
                     f'{core} YoY %',
                     f'{delta_core} p.p. (vs. {date})',
                    delta_color='off')
      elif UNIT in ['YoY % (Current year YTD %)'] and freq in ['Annual']:
        date = hicp_selection_2['Date'].iloc[-2].strftime('%Y')
        #date_2 = hicp_selection_2['Date'].iloc[-3].strftime('%Y')
        with left_column:
          st.metric('Total:',
                    f'{total} YoY %',
                    f'{delta_total} p.p (vs. {date})',
                   delta_color='off')
        with middle_column:
          st.metric('Food and non-alcoholic beverages:',
                    f'{food} YoY %',
                    f'{delta_food} p.p. (vs. {date})',
                   delta_color='off')
        with middle_2_column:
            st.metric('Fuels:',
                      f'{energy} YoY %',
                      f'{delta_energy} p.p. (vs. {date})',
                     delta_color='off')             
        with right_column:
          st. metric('Overall excl. energy and unprocessed food:',
                     f'{core} YoY %',
                     f'{delta_core} p.p. (vs. {date})',
                    delta_color='off')
      elif UNIT in ['Chain %'] and freq in ['Monthly']:
        date = hicp_selection_2['Date'].iloc[-2].strftime('%B %Y')
        #date_2 = hicp_selection_2['Date'].iloc[-3].strftime('%B %Y')
        with left_column:
          st.metric('Total:',
                    f'{total} MoM %',
                    f'{delta_total} p.p (vs. {date})',
                   delta_color='off')
        with middle_column:
          st.metric('Food and non-alcoholic beverages:',
                    f'{food} MoM %',
                    f'{delta_food} p.p. (vs. {date})',
                   delta_color='off')
        with middle_2_column:
            st.metric('Fuels:',
                      f'{energy} YoY %',
                      f'{delta_energy} p.p. (vs. {date})',
                     delta_color='off')             
        with right_column:
          st. metric('Overall excl. energy and unprocessed food:',
                     f'{core} MoM %',
                     f'{delta_core} p.p. (vs. {date})',
                    delta_color='off')
      elif UNIT in ['Chain %'] and freq in ['Quarterly']:
        year = hicp_selection_2['Date'].iloc[-2].year
        quarter = (hicp_selection_2['Date'].iloc[-2].month-1)//3+1
        date = f'{year:}Q{quarter}'
        #year_2 = hicp_selection_2['Date'].iloc[-3].year
        #quarter_2 = (hicp_selection_2['Date'].iloc[-3].month-1)//3+1
        #date_2 = f'{year_2:}Q{quarter_2}'
        with left_column:
          st.metric('Total:',
                    f'{total} QoQ %',
                    f'{delta_total} p.p (vs. {date})',
                   delta_color='off')
        with middle_column:
          st.metric('Food and non-alcoholic beverages:',
                    f'{food:1f} QoQ %',
                    f'{delta_food} p.p. (vs. {date})',
                   delta_color='off')
        with middle_2_column:
            st.metric('Fuels:',
                      f'{energy} YoY %',
                      f'{delta_energy} p.p. (vs. {date})',
                     delta_color='off')             
        with right_column:
          st. metric('Overall excl. energy and unprocessed food:',
                     f'{core} QoQ %',
                     f'{delta_core} p.p. (vs. {date})',
                    delta_color='off')
  elif query_type in ['More than one country, one product']:
      #Selection
      st.markdown('---')
      st.header('Selection')
      left_column, middle_column, right_column = st.columns(3)
      with left_column:
        st.subheader(f'Product: {prod}')
      with middle_column:
        st.subheader(f'Frequency: {freq}')
      with right_column:
        st.subheader(f'Unit: {UNIT}')
      if freq in ['Annual']:
        st.info('Year to Date considering available information until November 2024.')
      #KPIs
      st.markdown('---')
      # auxiliar dates for header
      if prod in ['Total']:    
          if freq in ['Monthly']:
            date = hicp_selection_3['Date'].iloc[-1].strftime('%B %Y')
          elif freq in ['Quarterly']:
            year = hicp_selection_3['Date'].iloc[-1].year
            quarter = (hicp_selection_3['Date'].iloc[-1].month-1)//3+1
            date = f'{year:}Q{quarter}'
          else:
            date = hicp_selection_3['Date'].iloc[-1].strftime('%Y')
      else:
          if freq in ['Monthly']:
            date = hicp_selection_3['Date'].iloc[-2].strftime('%B %Y')
          elif freq in ['Quarterly']:
            year = hicp_selection_3['Date'].iloc[-2].year
            quarter = (hicp_selection_3['Date'].iloc[-2].month-1)//3+1
            date = f'{year:}Q{quarter}'
          else:
            date = hicp_selection_3['Date'].iloc[-2].strftime('%Y')
      # header
      st.header(f'Results for: {date} (last available period)')
      left, right = st.columns(2)
      # auxiliar values for KPIs
      if prod in ['Total']:
          pt = (hicp_selection_3.loc[hicp_selection_3['Geo']=='Portugal'][prod].iloc[-1])
          pt_1 = (hicp_selection_3.loc[hicp_selection_3['Geo']=='Portugal'][prod].iloc[-2])
          delta_pt = round(pt - pt_1,1)
          es = (hicp_selection_3.loc[hicp_selection_3['Geo']=='Spain'][prod].iloc[-1])
          es_1 = (hicp_selection_3.loc[hicp_selection_3['Geo']=='Spain'][prod].iloc[-2])
          delta_es = round(es - es_1,1)
      else:
          pt = (hicp_selection_3.loc[hicp_selection_3['Geo']=='Portugal'][prod].iloc[-1])
          pt_1 = (hicp_selection_3.loc[hicp_selection_3['Geo']=='Portugal'][prod].iloc[-2])
          delta_pt = round(pt - pt_1,1)
          es = (hicp_selection_3.loc[hicp_selection_3['Geo']=='Spain'][prod].iloc[-1])
          es_1 = (hicp_selection_3.loc[hicp_selection_3['Geo']=='Spain'][prod].iloc[-2])
          delta_es = round(es - es_1,1)
      #KPIs
      if prod in ['Total']:
          if UNIT in ['YoY %'] and freq in ['Monthly']:
            date = hicp_selection_3['Date'].iloc[-2].strftime('%B %Y')
            with left:
                st.metric('Portugal:',
                          f'{pt} YoY %',
                          f'{delta_pt} p.p (vs. {date})',
                         delta_color='off')
            with right:
                st.metric('Spain:',
                          f'{es} YoY %',
                          f'{delta_es} p.p. (vs. {date})',
                         delta_color='off')
          elif UNIT in ['YoY %'] and freq in ['Quarterly']:
            year = hicp_selection_3['Date'].iloc[-2].year
            quarter = (hicp_selection_3['Date'].iloc[-2].month-1)//3+1
            date = f'{year:}Q{quarter}'
            with left:
              st.metric('Portugal:',
                        f'{pt} YoY %',
                        f'{delta_pt} p.p (vs. {date})',
                       delta_color='off')
            with right:
              st.metric('Spain:',
                        f'{es} YoY %',
                        f'{delta_es} p.p. (vs. {date})',
                       delta_color='off')
          elif UNIT in ['YoY % (Current year YTD %)'] and freq in ['Annual']:
            date = hicp_selection_3['Date'].iloc[-2].strftime('%Y')
            with left:
              st.metric('Portugal:',
                        f'{pt} YoY %',
                        f'{delta_pt} p.p (vs. {date})',
                       delta_color='off')
            with right:
              st.metric('Spain:',
                        f'{es} YoY %',
                        f'{delta_es} p.p. (vs. {date})',
                       delta_color='off')
          elif UNIT in ['Chain %'] and freq in ['Monthly']:
            date = hicp_selection_3['Date'].iloc[-2].strftime('%B %Y')
            with left:
              st.metric('Portugal:',
                        f'{pt} MoM %',
                        f'{delta_pt} p.p (vs. {date})',
                       delta_color='off')
            with right:
              st.metric('Spain:',
                        f'{es} MoM %',
                        f'{delta_es} p.p. (vs. {date})',
                       delta_color='off')
          elif UNIT in ['Chain %'] and freq in ['Quarterly']:
            year = hicp_selection_3['Date'].iloc[-2].year
            quarter = (hicp_selection_3['Date'].iloc[-2].month-1)//3+1
            date = f'{year:}Q{quarter}'
            with left:
              st.metric('Portugal:',
                        f'{pt} QoQ %',
                        f'{delta_pt} p.p (vs. {date})',
                       delta_color='off')
            with right:
              st.metric('Spain:',
                        f'{es} QoQ %',
                        f'{delta_es} p.p. (vs. {date})',
                       delta_color='off')
      else:
          if UNIT in ['YoY %'] and freq in ['Monthly']:
            date = hicp_selection_3['Date'].iloc[-2].strftime('%B %Y')
            with left:
                st.metric('Portugal:',
                          f'{pt} YoY %',
                          f'{delta_pt} p.p (vs. {date})',
                         delta_color='off')
            with right:
                st.metric('Spain:',
                          f'{es} YoY %',
                          f'{delta_es} p.p. (vs. {date})',
                         delta_color='off')
          elif UNIT in ['YoY %'] and freq in ['Quarterly']:
            year = hicp_selection_3['Date'].iloc[-2].year
            quarter = (hicp_selection_3['Date'].iloc[-2].month-1)//3+1
            date = f'{year:}Q{quarter}'
            with left:
              st.metric('Portugal:',
                        f'{pt} YoY %',
                        f'{delta_pt} p.p (vs. {date})',
                       delta_color='off')
            with right:
              st.metric('Spain:',
                        f'{es} YoY %',
                        f'{delta_es} p.p. (vs. {date})',
                       delta_color='off')
          elif UNIT in ['YoY % (Current year YTD %)'] and freq in ['Annual']:
            date = hicp_selection_3['Date'].iloc[-3].strftime('%Y')
            with left:
              st.metric('Portugal:',
                        f'{pt} YoY %',
                        f'{delta_pt} p.p (vs. {date})',
                       delta_color='off')
            with right:
              st.metric('Spain:',
                        f'{es} YoY %',
                        f'{delta_es} p.p. (vs. {date})',
                       delta_color='off')
          elif UNIT in ['Chain %'] and freq in ['Monthly']:
            date = hicp_selection_3['Date'].iloc[-3].strftime('%B %Y')
            with left:
              st.metric('Portugal:',
                        f'{pt} MoM %',
                        f'{delta_pt} p.p (vs. {date})',
                       delta_color='off')
            with right:
              st.metric('Spain:',
                        f'{es} MoM %',
                        f'{delta_es} p.p. (vs. {date})',
                       delta_color='off')
          elif UNIT in ['Chain %'] and freq in ['Quarterly']:
            year = hicp_selection_3['Date'].iloc[-2].year
            quarter = (hicp_selection_3['Date'].iloc[-2].month-1)//3+1
            date = f'{year:}Q{quarter}'
            with left:
              st.metric('Portugal:',
                        f'{pt} QoQ %',
                        f'{delta_pt} p.p (vs. {date})',
                       delta_color='off')
            with right:
              st.metric('Spain:',
                        f'{es} QoQ %',
                        f'{delta_es} p.p. (vs. {date})',
                       delta_color='off')
  #
  # ------------------------------------------------------------------------------
  st.markdown('---')
  #
  prod = np.array(prod)
  col_list = ['Date', 'Geo', 'Unit']
  columns = np.append(col_list,prod)
  df = pd.DataFrame(hicp_selection, columns=columns)
  #df[columns] = df.round(decimals=1)
  #
  # Plot
  if query_type in ['One country, more than one product']:
      st.header('Graph')
      fig_plot = px.line(
          df,
          x='Date',
          y=prod,
          orientation='v',
          template='seaborn')
      fig_plot.update_traces(
          mode='markers+lines', 
          hovertemplate=None)
      fig_plot.update_yaxes(title="%", showspikes=True,tickfont_size = 18)
      if freq in ['Annual']:
        fig_plot.update_xaxes(title="",
                              autorange = True,
                              rangeslider_visible=True,
                              rangeselector_visible=True,
                              tickformat = "%Y",
                              dtick = 'M12',
                              showspikes=True,
                              tickfont_size = 18)
      else: 
        fig_plot.update_xaxes(title="",
                              autorange = True,
                              rangeslider_visible=True,
                              rangeselector_visible=True,
                              showspikes=True,
                              tickfont_size = 18)
      fig_plot.update_layout(  # customize font and legend orientation & position
          hovermode="x",
          legend=dict(
              title=None, orientation="h",  x=0.5, xanchor="center", font=dict(size=18)),
          hoverlabel_font_size=18)
      fig_plot.update_layout(
          autosize=True,
          height=500,
          margin=dict(l=50, r=50, t=50, b=20),)
      fig_plot.update_layout(
          plot_bgcolor="rgb(240,240,235)")
      st.plotly_chart(fig_plot, use_container_width=True)    
  if query_type in ['More than one country, one product']:
      st.header('Graph')
      df2 = df.pivot(index=['Date', 'Unit'], columns=['Geo'], values=prod)
      df2 = df2.reset_index(level=['Date', 'Unit'])
      fig_plot = px.line(
          df2,
          x='Date',
          y=geo,
          orientation='v',
          template='seaborn')
      fig_plot.update_traces(mode='markers+lines', hovertemplate=None)
      fig_plot.update_yaxes(title="%", showspikes=True,tickfont_size = 18)
      if freq in ['Annual']:
        fig_plot.update_xaxes(title="",
                              autorange = True,
                              rangeslider_visible=True,
                              rangeselector_visible=True,
                              tickformat = "%Y",
                              dtick = "M12",
                              showspikes=True,
                              tickfont_size = 18)
      elif freq in ['Quarterly']:
        fig_plot.update_xaxes(title="",
                              autorange = True,
                              rangeslider_visible=True,
                              rangeselector_visible=True,
                              showspikes=True,
                              tickfont_size = 18)   
      else: 
        fig_plot.update_xaxes(title="",
                              autorange = True,
                              rangeslider_visible=True,
                              rangeselector_visible=True,
                              showspikes=True,
                              tickfont_size = 18)
      fig_plot.update_layout(  # customize font and legend orientation & position
          hovermode="x",
          legend=dict(
              title=None, orientation="h",  x=0.5, xanchor="center", font=dict(size=18)),
          hoverlabel_font_size=18)
      fig_plot.update_layout(
          autosize=True,
          height=500,
          margin=dict(l=50, r=50, t=50, b=20),)
      fig_plot.update_layout(
          plot_bgcolor="rgb(240,240,235)")
      st.plotly_chart(fig_plot, use_container_width=True)
  #    
  # Table
  st.header('Table')
  #
  df = df.reset_index(drop=False)
  df = df.rename(columns={'Geo': 'Country', 'Unit': 'Unit'})
  df = df.drop(columns=['index'])
  df.sort_values(by='Date', ascending = False, inplace=True)
  #
  if query_type in ['One country, more than one product']:
      @st.cache
      def convert_df_xlsx(df):
          output = BytesIO()
          writer = pd.ExcelWriter(output, engine='xlsxwriter')
          num_col = len(df.columns)
          df.to_excel(writer, index=False, sheet_name='Sheet1')
          workbook = writer.book
          worksheet = writer.sheets['Sheet1']
          format1 = workbook.add_format({'num_format': '0.00'})
          worksheet.set_column(0, num_col, 30, format1)
          writer.close()
          processed_data = output.getvalue()
          return processed_data
      xlsx = convert_df_xlsx(df)
      st.download_button('Download selected data as xlsx',
                         data=xlsx, file_name='hicp_data.xlsx')
      fig = go.Figure(data=go.Table(
        header=dict(values=list(df.columns),
                    fill_color = '#99C7FF',
                    align='center',
                    font=dict(size=16),
                    height=50),
        cells=dict(values=df.transpose().values.tolist(),
                   fill_color = '#F0F0EB',
                   align='center',
                   font=dict(size=15),
                   height=30)))
      fig.update_layout(
          autosize=True,
          height=500,
          margin=dict(l=10, r=10, t=10, b=20))
      st.plotly_chart(fig,use_container_width=True)
  if query_type in ['More than one country, one product']:
      df2 = df2.set_index(['Date', 'Unit'])
      df2 = df2.reset_index(drop=False)
      df2 = df2.rename(columns={'geo': 'Country', 'Unit': 'Unit'})
      df2.sort_values(by='Date', ascending = False, inplace=True)
      @st.cache
      def convert_df_xlsx(df2):
          output = BytesIO()
          writer = pd.ExcelWriter(output, engine='xlsxwriter')
          num_col = len(df2.columns)
          df2.to_excel(writer, index=False, sheet_name='Sheet1')
          workbook = writer.book
          worksheet = writer.sheets['Sheet1']
          format1 = workbook.add_format({'num_format': '0.0'})
          worksheet.set_column(0, num_col, 30, format1)
          writer.close()
          processed_data = output.getvalue()
          return processed_data
      xlsx = convert_df_xlsx(df2)
      st.download_button('Download selected data as xlsx',
                         data=xlsx, file_name='hicp_data.xlsx')
      fig = go.Figure(data=go.Table(
        header=dict(values=list(df2.columns),
                    fill_color = '#99C7FF',
                    align='center',
                    font=dict(size=16),
                    height=50),
        cells=dict(values=df2.transpose().values.tolist(),
                   fill_color = '#F0F0EB',
                   align='center',
                   font=dict(size=15),
                   height=30)))
      fig.update_layout(
          autosize=True,
          height=500,
          margin=dict(l=10, r=10, t=10, b=20))
      st.plotly_chart(fig,use_container_width=True)
  
  
# ------------------------------------------------------------------------------
# Disclosures
st.markdown('##')
st.caption("Values on Retail Pulse are often provisional and subject to monthly official revisions. For further information visit https://ec.europa.eu/eurostat/cache/metadata/en/sts_esms.htm .")
st.caption('Developed by SONAE Group Strategy Planning and Control.')

    

hide_st_style = """
                <style>
                # Hide Streamlite Style
                MainMenu {visibility: hidden;}
                footer {visibility: hidden;}    
                header {visibility: hidden;}
                </style>
                """
st.markdown(hide_st_style, unsafe_allow_html=True)