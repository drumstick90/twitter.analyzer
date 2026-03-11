import pandas as pd
import numpy as np
from datetime import datetime

class LikesAnalyzer:
    def __init__(self, tweets: list):
        self.tweets = tweets
        self.df = self._process_tweets()

    def _process_tweets(self):
        processed = []
        for tweet in self.tweets:
            if 'createdAt' in tweet:
                try:
                    date_str = tweet['createdAt']
                    # Handle different date formats if necessary
                    # The example used "%a %b %d %H:%M:%S %z %Y"
                    parsed_date = datetime.strptime(date_str, "%a %b %d %H:%M:%S %z %Y")
                    
                    tweet_info = {
                        'id': tweet.get('id', 'N/A'),
                        'created_at': parsed_date,
                        'date': parsed_date.date(),
                        'likes': tweet.get('likeCount', 0),
                        'retweets': tweet.get('retweetCount', 0),
                        'replies': tweet.get('replyCount', 0),
                        'text': tweet.get('text', 'N/A'),
                        'is_reply': tweet.get('isReply', False)
                    }
                    processed.append(tweet_info)
                except Exception as e:
                    continue
        return pd.DataFrame(processed)

    def get_daily_stats(self):
        if self.df.empty:
            return pd.DataFrame()
            
        daily_stats = self.df.groupby('date').agg({
            'likes': ['sum', 'mean', 'count', 'max'],
            'retweets': ['sum', 'mean'],
            'replies': ['sum', 'mean']
        }).round(2)
        
        # Flatten column names
        daily_stats.columns = ['_'.join(col).strip() for col in daily_stats.columns]
        daily_stats = daily_stats.reset_index()
        
        # Rename columns for clarity
        daily_stats.columns = [
            'date', 'total_likes', 'avg_likes', 'tweet_count', 'max_likes',
            'total_retweets', 'avg_retweets', 'total_replies', 'avg_replies'
        ]
        return daily_stats

    def get_monthly_stats(self):
        if self.df.empty:
            return pd.DataFrame()
            
        self.df['month'] = self.df['created_at'].dt.to_period('M')
        monthly_stats = self.df.groupby('month').agg({
            'likes': ['sum', 'mean', 'count'],
            'retweets': ['sum', 'mean'],
            'replies': ['sum', 'mean']
        }).round(2)
        
        monthly_stats.columns = ['_'.join(col).strip() for col in monthly_stats.columns]
        monthly_stats = monthly_stats.reset_index()
        monthly_stats.columns = [
            'month', 'total_likes', 'avg_likes', 'tweet_count',
            'total_retweets', 'avg_retweets', 'total_replies', 'avg_replies'
        ]
        return monthly_stats
