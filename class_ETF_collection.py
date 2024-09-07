from class_ETF_data import ETF_data
from datetime import date

class ETF_collection():
    etf_name_map = {'iShares-Global-Clean-Energy-ETF': ('data/iShares-Global-Clean-Energy-ETF_fund.xlsx', 'ICLN'),
                    'iShares-SP-500-Information-Technology-Sector-UCITS-ETF': ('data/iShares-SP-500-Information-Technology-Sector-UCITS-ETF-USD_fund.xlsx', 'IXN'),
                    'NASDAQ-100-ETF': ('data/NASDAQ-100-UCITS-ETF-DE_fund.xlsx', 'QQQ'),
                    'iShares-Core-MSCI-World-ETF': ('data/iShares-Core-MSCI-World-UCITS-ETF_fund.xlsx', 'URTH')}
    
    def __init__(self, etf_distribution, payments, from_api=False):
        self.ETFs = {}

        self.set_etf_distribution(etf_distribution)

        self.start_date = date.max #for min check
        payments_per_ETF = []
        for name, content in self.ETFs.items():
            payments_per_ETF.append({'name': name, 'bonuses': [], 'periods': []})
            for bonus in payments['bonuses']:
                bonus_for_etf = bonus.copy()
                bonus_for_etf[0] *= content['fraction']
                payments_per_ETF[-1]['bonuses'].append(bonus_for_etf) 
                self.start_date = min(self.start_date, bonus_for_etf[1])
            for period in payments['periods']:
                period_for_etf = period.copy()
                period_for_etf[0] *= content['fraction']
                payments_per_ETF[-1]['periods'].append(period_for_etf)
                self.start_date = min(self.start_date, period_for_etf[1])
        
        for etf_data in payments_per_ETF:
            self.add_ETF(etf_data, from_api=from_api)

    def set_etf_distribution(self, dist_dict):
        for etf, dist in dist_dict.items():
            if not etf in self.ETFs.keys(): self.ETFs[etf] = {}
            self.ETFs[etf]['fraction'] = dist/100

    def add_ETF(self, etf_ini, from_api=False):
        if from_api: self.ETFs[etf_ini['name']]['etf'] = ETF_data.from_yfinance_api(self.etf_name_map[etf_ini['name']][1], filename=self.etf_name_map[etf_ini['name']][0])
        else: self.ETFs[etf_ini['name']]['etf'] = ETF_data.from_Excel(self.etf_name_map[etf_ini['name']][0])
                
        for bonus in etf_ini['bonuses']:
            self.ETFs[etf_ini['name']]['etf'].add_bonus(*bonus)

        for period in etf_ini['periods']:            
            self.ETFs[etf_ini['name']]['etf'].add_period(*period)
