import pandas as pd
import yfinance as yf
from datetime import date
from dateutil import relativedelta

class ETF_data():

    # def __init__(self, filename='iShares-Global-Clean-Energy-ETF_fund.xlsx'):
    #     self.df_main = pd.read_excel(filename)
    #     self.df_main = self._transform_datetime(self.df_main)
    def __init__(self, df):
        self.df_main = df

        self.periods = []
        self.bonuses = []

        # self.add_bonus(7500, date(2022, 12, 1))
        # self.add_bonus(7500, date(2023, 12, 1))
        # self.add_period(350, date(2022, 12, 1), date(2023, 12, 1))
        # self.add_period(50, date(2023, 12, 1), None)

        # self.get_total_value_at_date_without_interest(date.today())
        # self.get_total_value_at_date_with_interest(date(2024,6,1))


    @classmethod
    def from_Excel(cls, filename):
        df = pd.read_excel(filename)
        df = cls._transform_datetime(df)

        return cls(df)

    @classmethod
    def from_yfinance_api(cls, ticker, filename=None):
        etf = yf.Ticker(ticker)
        df = etf.history(period="max")

        df = df.reset_index()
        df['Date'] = df['Date'].apply(lambda x: x.replace(tzinfo=None))
        #df = df.rename(columns={'Date': 'As Of'})
        df['NAV per Share'] = df[['High', 'Low']].mean(axis=1)
        if filename: df.to_excel(filename)
        df = cls._transform_datetime(df)

        return cls(df)

    @staticmethod
    def _transform_datetime(df):
        df['Date'] = pd.to_datetime(df['Date'], format='%b %d, %Y')
        
        return df  

    def get_total_value_at_date_without_interest(self, fixed_date):
        val_from_periods = 0
        for period in self.periods:
            if period[2] is None:         
                diff = relativedelta.relativedelta(fixed_date, period[1])
            else:
                diff = relativedelta.relativedelta(min(period[2],fixed_date), period[1])
           
            valdiff = period[0] * (diff.months + 12*diff.years + 1)            
            val_from_periods += valdiff           

        #val_from_bonuses = sum(list(zip(*self.bonuses))[0])
        considered_bonuses = [bonus for bonus in self.bonuses if fixed_date>=bonus[1]]
        if len(considered_bonuses)>0: val_from_bonuses = sum(list(zip(*considered_bonuses))[0])  
        else: val_from_bonuses=0   
                
        return val_from_periods + val_from_bonuses

    def get_total_value_at_date_with_interest(self, fixed_date):
        val_from_periods = 0
        val_from_bonuses = 0
        for period in self.periods: 
            val_from_this_period = 0           
            time_interval = period[1]
            if period[2] is None:
                #i_end = (self.df_main['As Of'] - pd.to_datetime(fixed_date)).abs().idxmin()           
               
                val_from_this_period = self._get_value_from_period_with_interest(*period[:2], fixed_date)
            
            else:
                #i_end = (self.df_main['As Of'] - pd.to_datetime(period[2])).abs().idxmin()             
                #val_from_this_period = self._get_value_from_period_with_interest(*period)
                val_from_this_period = self._get_value_from_period_with_interest(*period[:2], min(period[2],fixed_date))
               
                if fixed_date > period[2]:
                    i_start = (self.df_main['Date'] - pd.to_datetime(period[2])).abs().idxmin()
                    i_end = (self.df_main['Date'] - pd.to_datetime(fixed_date)).abs().idxmin()
                    val_from_this_period *= self._get_nav_ratio(i_start, i_end)
            
            val_from_periods += val_from_this_period        

        considered_bonuses = [bonus for bonus in self.bonuses if fixed_date>=bonus[1]]
        for bonus in considered_bonuses:    
            i_start = (self.df_main['Date'] - pd.to_datetime(bonus[1])).abs().idxmin()
            i_end = (self.df_main['Date'] - pd.to_datetime(fixed_date)).abs().idxmin()           

            #nav_begin = self.df_main[self.df_main['As Of'].apply(lambda x: x.date())==bonus[1]]['NAV per Share'].values[0]
            #nav_end = self.df_main[self.df_main['As Of'].apply(lambda x: x.date())==fixed_date]['NAV per Share'].values[0]
            val_from_bonuses += bonus[0]*self._get_nav_ratio(i_start,i_end)            

        #print(val_from_periods, val_from_bonuses)
        return val_from_periods + val_from_bonuses


    def add_period(self, amount, start_date, end_date):
        self.periods.append((amount, start_date, end_date))

    def add_bonus(self, amount, date):
        self.bonuses.append((amount, date))

    def _get_nav_ratio(self, i_start, i_end):
        nav_start = self.df_main.iloc[i_start]['NAV per Share']
        nav_end = self.df_main.iloc[i_end]['NAV per Share']

        return nav_end / nav_start
    
    def _get_value_from_period_with_interest(self, amount, start_date, end_date):
        val = 0
        i_end = (self.df_main['Date'] - pd.to_datetime(end_date)).abs().idxmin()            
        while start_date <= end_date:  #payment loop
            i_start = (self.df_main['Date'] - pd.to_datetime(start_date)).abs().idxmin()
            val += amount*self._get_nav_ratio(i_start, i_end)
            start_date = start_date + relativedelta.relativedelta(months=1)
        return val