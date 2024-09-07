import streamlit as st

from class_ETF_data import ETF_data
from class_ETF_collection import ETF_collection

from datetime import date
from dateutil import relativedelta
import matplotlib.pyplot as plt

import pickle
import io


def add_etf_to_contract():
    st.session_state.etfs_in_contract[option_etf] = float(fraction_etf)#/100.

    st.write(st.session_state.etfs_in_contract)

def add_period_to_contract():    
    if flag_unlimited:
        st.session_state.payments['periods'].append([float(value_period), start_date_period, None])
    else:
        st.session_state.payments['periods'].append([float(value_period), start_date_period, end_date_period])
    #st.write(st.session_state.payments)

def add_bonus_to_contract():
    st.session_state.payments['bonuses'].append([float(value_bonus), date_bonus])
    #st.write(st.session_state.payments)

def build_start_screen():
    st.session_state.page_no = 0    
    st.session_state.etfs_in_contract = {}

def build_period_screen():
    st.session_state.page_no = 1   

def build_bonus_screen():
    st.session_state.page_no = 2

def load_contract():
    st.session_state.page_no = 3

def write_contract():
    st.session_state.page_no = 4

def plot_etf_evolution(x, y_without_interest, y_with_interest, title):
    fig, ax = plt.subplots()
    plt.title(title)
    ax.plot(x, y_without_interest, label='without interest')
    ax.plot(x, y_with_interest, label='with interest')
    plt.legend()
    plt.xticks(rotation=90)
    plt.grid()

    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    gain_total = y_with_interest[-1]/y_without_interest[-1]
    gain_relative_percent = (gain_total - 1)*100
    timespan = relativedelta.relativedelta(x[-1], x[0])
    gain_yearly = (gain_total**(1/(timespan.years + timespan.months/12.)) - 1) * 100

    text = f'Total gain:          {gain_relative_percent:.3g}%\nAvg yearly gain: {gain_yearly:.3g}%'
    plt.text(0.55, 0.15, text, transform=ax.transAxes, fontsize=12,
        verticalalignment='top', bbox=props)

    st.pyplot(fig)

def build_analysis_screen(main_collection):
    st.session_state.page_no = 5
    
    dates_for_plot = []
    running_sum_without_interest = []
    running_sum_with_interest = []
    all_values_without_interest = {}
    all_values_with_interest = {}

    #running_date = date(2022, 11, 1)
    running_date = main_collection.start_date

    while running_date <= date.today():
        running_value_without_interest = {name: etf['etf'].get_total_value_at_date_without_interest(running_date)
                                for name, etf in main_collection.ETFs.items()}
        running_value_with_interest = {name: etf['etf'].get_total_value_at_date_with_interest(running_date)
                                for name, etf in main_collection.ETFs.items()}

        running_sum_without_interest.append(sum(running_value_without_interest.values()))
        running_sum_with_interest.append(sum(running_value_with_interest.values()))
        dates_for_plot.append(running_date)

        running_date += relativedelta.relativedelta(months=1)

        for etf in running_value_without_interest.keys():
            if not etf in all_values_without_interest.keys(): all_values_without_interest[etf] = []
            all_values_without_interest[etf].append(running_value_without_interest[etf])
            if not etf in all_values_with_interest.keys(): all_values_with_interest[etf] = []
            all_values_with_interest[etf].append(running_value_with_interest[etf])
        
    fig, ax = plt.subplots()
    
    #print(running_sum_without_interest)
    #print(running_sum_with_interest)
    plot_etf_evolution(dates_for_plot, running_sum_without_interest, running_sum_with_interest, 'Total insurance')

    for etf in all_values_without_interest:
        plot_etf_evolution(dates_for_plot, all_values_without_interest[etf], all_values_with_interest[etf], etf)       

if 'page_no' not in st.session_state:
    st.session_state.page_no = 0
if 'etfs_in_contract' not in st.session_state:
    st.session_state.etfs_in_contract = {}
if 'payments' not in st.session_state:
    st.session_state.payments = {}
    st.session_state.payments['periods'] = []
    st.session_state.payments['bonuses'] = []

available_etfs = ('iShares-Global-Clean-Energy-ETF',
                'iShares-SP-500-Information-Technology-Sector-UCITS-ETF',
                'NASDAQ-100-ETF',
                'iShares-Core-MSCI-World-ETF')

if __name__=='__main__':           

    if st.session_state.page_no == 0:
        option_etf = st.selectbox('Choose ETF', available_etfs)
        fraction_etf = st.text_input('ETF fraction in percent here')   
        st.button('Add ETF to contract', on_click=add_etf_to_contract)
        st.button('Proceed', on_click=build_period_screen)
        st.button('Load contract', on_click=load_contract)
        st.session_state.flag_download_2 = st.checkbox('Get data from API and download new pickle file ', value=False)

    elif st.session_state.page_no == 1:                
        #option_etf = st.selectbox('Choose ETF', st.session_state.etfs_in_contract.keys())
        value_period = st.text_input('Payment period value here')
        start_date_period = st.date_input('Payment period start date here')
        flag_unlimited = st.checkbox('Payment still ongoing', value=True)
        end_date_period = st.date_input('Payment period end date here', disabled=flag_unlimited)
        st.button('Add Payment', on_click=add_period_to_contract)
        st.button('Proceed', on_click=build_bonus_screen)

    elif st.session_state.page_no == 2:        
        #option_etf = st.selectbox('Choose ETF', st.session_state.etfs_in_contract.keys())
        value_bonus = st.text_input('Bonus value here')
        date_bonus = st.date_input('Bonus date here')
        st.button('Add Bonus', on_click=add_bonus_to_contract)
        st.button('Finish contract', on_click=write_contract)           
        st.session_state.flag_download = st.checkbox('Download from API', value=False)
       

    elif st.session_state.page_no == 3:
        pickle_in = st.file_uploader('Choose file to load', type='pkl')
        if pickle_in is not None:
            main_collection = pickle.load(pickle_in)
            if st.session_state.flag_download_2:
                for etf_key, etf_val in main_collection.ETFs.items():           
                    etf_val['etf'].df_main = ETF_data.from_yfinance_api(main_collection.etf_name_map[etf_key][1], filename=main_collection.etf_name_map[etf_key][0]).df_main                   

                buffer = io.BytesIO()
                pickle.dump(main_collection, buffer)
                buffer.seek(0)   

                st.download_button(
                label="Proceed and Download",
                data=buffer,
                file_name='main_collection.pkl',
                mime="application/octet-stream",
                on_click=build_analysis_screen,
                args=(main_collection,)
            )                
          
            #print(main_collection.ETFs['iShares-Global-Clean-Energy-ETF']['etf'].df_main)
            build_analysis_screen(main_collection)
    
    elif st.session_state.page_no == 4:
        main_collection = ETF_collection(st.session_state.etfs_in_contract, st.session_state.payments, from_api=st.session_state.flag_download)
    
        buffer = io.BytesIO()
        pickle.dump(main_collection, buffer)
        buffer.seek(0)

        st.download_button(
                label="Proceed and Download",
                data=buffer,
                file_name='main_collection.pkl',
                mime="application/octet-stream",
                on_click=build_analysis_screen,
                args=(main_collection,)
            )    
        st.button(
                label="Proceed without Download",
                on_click=build_analysis_screen,
                args=(main_collection,)
            )

    st.button('Back to Start Screen', on_click=build_start_screen)        
