import pandas as pd
import numpy as np

class TemporalAnalyzer:
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def prepare_hourly_matrix(self):
        """
        Prepare data for hourly heatmap.
        Expects a DataFrame with 'hour_00', 'hour_01', ... columns 
        OR raw tweets with 'created_at'.
        """
        # Check if we have the matrix format
        hour_cols = [f'hour_{h:02d}' for h in range(24)]
        if all(col in self.df.columns for col in hour_cols):
            return self.df
            
        # Otherwise, if we have raw tweets, we need to aggregate
        if 'created_at' in self.df.columns:
            # TODO: Implement aggregation from raw tweets
            pass
            
        return self.df

    def get_monthly_distribution(self):
        hour_cols = [f'hour_{h:02d}' for h in range(24)]
        if all(col in self.df.columns for col in hour_cols):
            if 'month' not in self.df.columns and 'date' in self.df.columns:
                self.df['month'] = self.df['date'].dt.month
                
            return self.df.groupby('month')[hour_cols].sum().reset_index()
        return None

    def get_weekday_distribution(self):
        hour_cols = [f'hour_{h:02d}' for h in range(24)]
        if all(col in self.df.columns for col in hour_cols):
            if 'day_of_week' in self.df.columns:
                weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                weekday_map = {day: i for i, day in enumerate(weekday_order)}
                self.df['weekday_order'] = self.df['day_of_week'].map(weekday_map)
                
                return self.df.groupby('weekday_order')[hour_cols].mean().reset_index()
        return None
