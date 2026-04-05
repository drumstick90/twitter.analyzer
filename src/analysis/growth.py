import pandas as pd
import numpy as np

class GrowthAnalyzer:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self._preprocess()

    def _preprocess(self):
        # Ensure date column exists and is pandas-datetimelike (not plain datetime.date / object)
        if 'date' not in self.df.columns and 'date_short' in self.df.columns:
            self.df['date'] = self.df['date_short']

        if 'date' in self.df.columns:
            self.df['date'] = pd.to_datetime(self.df['date'])

        if 'date' in self.df.columns:
            self.df['month'] = self.df['date'].dt.month
            self.df['week_of_year'] = self.df['date'].dt.isocalendar().week
            self.df['quarter'] = self.df['date'].dt.quarter
            
            # Add month names
            month_names = ['Gen', 'Feb', 'Mar', 'Apr', 'Mag', 'Giu', 
                          'Lug', 'Ago', 'Set', 'Ott', 'Nov', 'Dic']
            self.df['month_name'] = self.df['month'].apply(lambda x: month_names[x-1] if pd.notnull(x) else '')

    def analyze_monthly(self):
        monthly_stats = self.df.groupby('month').agg({
            'tweets_singoli': 'sum',
            'thread_count': 'sum',
            'thread_tweets_total': 'sum',
            'tweets_totali': 'sum',
            'month_name': 'first'
        }).reset_index()
        
        monthly_stats['growth_rate'] = monthly_stats['tweets_totali'].pct_change() * 100
        return monthly_stats

    def analyze_quarterly(self):
        quarterly_stats = self.df.groupby('quarter').agg({
            'tweets_singoli': 'sum',
            'thread_count': 'sum',
            'thread_tweets_total': 'sum',
            'tweets_totali': 'sum'
        }).reset_index()
        
        quarterly_stats['growth_rate'] = quarterly_stats['tweets_totali'].pct_change() * 100
        # Approximate days in quarter
        quarterly_stats['avg_daily'] = quarterly_stats['tweets_totali'] / [90, 91, 92, 92][:len(quarterly_stats)]
        return quarterly_stats

    def analyze_weekly(self):
        weekly_stats = self.df.groupby('week_of_year').agg({
            'tweets_singoli': 'sum',
            'thread_count': 'sum',
            'thread_tweets_total': 'sum',
            'tweets_totali': 'sum'
        }).reset_index()
        
        weekly_stats['growth_rate'] = weekly_stats['tweets_totali'].pct_change() * 100
        return weekly_stats

    def get_summary_stats(self, monthly_stats, quarterly_stats):
        first_month = monthly_stats.iloc[0]['tweets_totali']
        last_month = monthly_stats.iloc[-1]['tweets_totali']
        monthly_growth = ((last_month - first_month) / first_month) * 100 if first_month else 0
        
        first_quarter = quarterly_stats.iloc[0]['tweets_totali']
        last_quarter = quarterly_stats.iloc[-1]['tweets_totali']
        quarterly_growth = ((last_quarter - first_quarter) / first_quarter) * 100 if first_quarter else 0
        
        return {
            'monthly_growth': monthly_growth,
            'quarterly_growth': quarterly_growth,
            'start_tweets_per_month': first_month,
            'end_tweets_per_month': last_month
        }
