#!/usr/bin/env python3
"""
Analysis script for @NTFabiano's 2023 tweets focusing on likes trends and engagement patterns.
"""

import json
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import numpy as np
from collections import defaultdict, Counter
import re

class NTFabiano2023Analyzer:
    def __init__(self, data_dir="NTFabiano_tweets_analysis"):
        self.data_dir = data_dir
        self.tweets_2023 = []
        self.df = None
        
    def load_2023_data(self):
        """Load all 2023 tweet data from JSON files."""
        print("🔍 Loading 2023 tweet data...")
        
        # Find all 2023 files
        files = [f for f in os.listdir(self.data_dir) if f.startswith("tweets_NTFabiano_2023_page_")]
        files.sort()  # Sort by page number
        
        print(f"📁 Found {len(files)} 2023 data files")
        
        for file in files:
            file_path = os.path.join(self.data_dir, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    tweets = json.load(f)
                    self.tweets_2023.extend(tweets)
                print(f"✅ Loaded {len(tweets)} tweets from {file}")
            except Exception as e:
                print(f"❌ Error loading {file}: {e}")
        
        print(f"📊 Total 2023 tweets loaded: {len(self.tweets_2023)}")
        
    def parse_dates(self):
        """Parse tweet creation dates and extract temporal features."""
        print("📅 Parsing tweet dates...")
        
        for tweet in self.tweets_2023:
            try:
                # Parse the createdAt field
                date_str = tweet['createdAt']
                # Format: "Fri Aug 15 11:31:59 +0000 2025"
                parsed_date = datetime.strptime(date_str, "%a %b %d %H:%M:%S %z %Y")
                
                # Extract temporal features
                tweet['parsed_date'] = parsed_date
                tweet['date'] = parsed_date.date()
                tweet['hour'] = parsed_date.hour
                tweet['day_of_week'] = parsed_date.strftime('%A')
                tweet['month'] = parsed_date.strftime('%B')
                tweet['week_of_year'] = parsed_date.isocalendar()[1]
                
            except Exception as e:
                print(f"⚠️  Error parsing date for tweet {tweet.get('id', 'unknown')}: {e}")
                tweet['parsed_date'] = None
                tweet['date'] = None
                tweet['hour'] = None
                tweet['day_of_week'] = None
                tweet['month'] = None
                tweet['week_of_year'] = None
    
    def create_dataframe(self):
        """Convert tweets to pandas DataFrame for analysis."""
        print("📋 Creating DataFrame...")
        
        # Extract key metrics
        data = []
        for tweet in self.tweets_2023:
            if tweet.get('parsed_date'):  # Only include tweets with valid dates
                data.append({
                    'id': tweet['id'],
                    'text': tweet['text'],
                    'created_at': tweet['parsed_date'],
                    'date': tweet['date'],
                    'hour': tweet['hour'],
                    'day_of_week': tweet['day_of_week'],
                    'month': tweet['month'],
                    'week_of_year': tweet['week_of_year'],
                    'likes': tweet.get('likeCount', 0),
                    'retweets': tweet.get('retweetCount', 0),
                    'replies': tweet.get('replyCount', 0),
                    'quotes': tweet.get('quoteCount', 0),
                    'views': tweet.get('viewCount', 0),
                    'bookmarks': tweet.get('bookmarkCount', 0),
                    'is_reply': tweet.get('isReply', False),
                    'source': tweet.get('source', 'Unknown'),
                    'lang': tweet.get('lang', 'Unknown'),
                    'text_length': len(tweet.get('text', '')),
                    'has_media': bool(tweet.get('extendedEntities', {}).get('media')),
                    'is_automated': tweet.get('isAutomated', False),
                    'automated_by': tweet.get('automatedBy')
                })
        
        self.df = pd.DataFrame(data)
        print(f"📊 DataFrame created with {len(self.df)} tweets")
        
        # Convert date columns to proper types
        self.df['created_at'] = pd.to_datetime(self.df['created_at'])
        self.df['date'] = pd.to_datetime(self.df['date'])
        
        # Sort by date
        self.df = self.df.sort_values('created_at')
        
    def analyze_likes_trends(self):
        """Analyze likes trends over time."""
        print("\n" + "="*60)
        print("📈 LIKES TREND ANALYSIS FOR 2023")
        print("="*60)
        
        if self.df is None or len(self.df) == 0:
            print("❌ No data available for analysis")
            return
        
        # Basic statistics
        print(f"📊 Total tweets analyzed: {len(self.df)}")
        print(f"❤️  Total likes received: {self.df['likes'].sum():,}")
        print(f"📈 Average likes per tweet: {self.df['likes'].mean():.1f}")
        print(f"🔥 Highest likes: {self.df['likes'].max():,}")
        print(f"💤 Lowest likes: {self.df['likes'].min():,}")
        print(f"📊 Median likes: {self.df['likes'].median():.1f}")
        
        # Likes distribution
        print(f"\n📊 Likes Distribution:")
        print(f"  0-10 likes: {len(self.df[self.df['likes'] <= 10])} tweets ({len(self.df[self.df['likes'] <= 10])/len(self.df)*100:.1f}%)")
        print(f"  11-50 likes: {len(self.df[(self.df['likes'] > 10) & (self.df['likes'] <= 50)])} tweets ({len(self.df[(self.df['likes'] > 10) & (self.df['likes'] <= 50)])/len(self.df)*100:.1f}%)")
        print(f"  51-100 likes: {len(self.df[(self.df['likes'] > 50) & (self.df['likes'] <= 100)])} tweets ({len(self.df[(self.df['likes'] > 50) & (self.df['likes'] <= 100)])/len(self.df)*100:.1f}%)")
        print(f"  100+ likes: {len(self.df[self.df['likes'] > 100])} tweets ({len(self.df[self.df['likes'] > 100])/len(self.df)*100:.1f}%)")
        
        # Monthly trends
        print(f"\n📅 Monthly Likes Trends:")
        monthly_likes = self.df.groupby('month')['likes'].agg(['sum', 'mean', 'count']).round(1)
        monthly_likes = monthly_likes.reindex(['January', 'February', 'March', 'April', 'May', 'June', 
                                             'July', 'August', 'September', 'October', 'November', 'December'])
        
        for month in monthly_likes.index:
            if month in monthly_likes.index:
                row = monthly_likes.loc[month]
                print(f"  {month}: {row['sum']:,.0f} total likes, {row['mean']:.1f} avg, {row['count']} tweets")
        
        # Weekly trends
        print(f"\n📅 Weekly Likes Trends:")
        weekly_likes = self.df.groupby('week_of_year')['likes'].agg(['sum', 'mean', 'count']).round(1)
        print(f"  Best week: Week {weekly_likes['sum'].idxmax()} with {weekly_likes['sum'].max():,.0f} total likes")
        print(f"  Worst week: Week {weekly_likes['sum'].idxmin()} with {weekly_likes['sum'].min():,.0f} total likes")
        
        # Daily patterns
        print(f"\n🌅 Daily Patterns:")
        daily_likes = self.df.groupby('day_of_week')['likes'].agg(['sum', 'mean', 'count']).round(1)
        daily_likes = daily_likes.reindex(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])
        
        for day in daily_likes.index:
            if day in daily_likes.index:
                row = daily_likes.loc[day]
                print(f"  {day}: {row['sum']:,.0f} total likes, {row['mean']:.1f} avg, {row['count']} tweets")
        
        # Hourly patterns
        print(f"\n⏰ Hourly Patterns:")
        hourly_likes = self.df.groupby('hour')['likes'].agg(['sum', 'mean', 'count']).round(1)
        
        # Find best and worst hours
        best_hour = hourly_likes['sum'].idxmax()
        worst_hour = hourly_likes['sum'].idxmin()
        
        print(f"  Best hour: {best_hour}:00 with {hourly_likes.loc[best_hour, 'sum']:,.0f} total likes")
        print(f"  Worst hour: {worst_hour}:00 with {hourly_likes.loc[worst_hour, 'sum']:,.0f} total likes")
        
        # Top performing tweets
        print(f"\n🏆 Top 10 Most Liked Tweets:")
        top_tweets = self.df.nlargest(10, 'likes')[['created_at', 'text', 'likes', 'retweets', 'replies']]
        
        for idx, row in top_tweets.iterrows():
            date_str = row['created_at'].strftime('%Y-%m-%d %H:%M')
            text_preview = row['text'][:80] + "..." if len(row['text']) > 80 else row['text']
            print(f"  {date_str} | ❤️ {row['likes']:,} | 🔄 {row['retweets']:,} | 💬 {row['replies']:,}")
            print(f"    {text_preview}")
            print()
    
    def analyze_engagement_patterns(self):
        """Analyze engagement patterns beyond just likes."""
        print("\n" + "="*60)
        print("🔗 ENGAGEMENT PATTERNS ANALYSIS")
        print("="*60)
        
        if self.df is None or len(self.df) == 0:
            return
        
        # Engagement ratios
        print(f"📊 Engagement Metrics:")
        print(f"  Likes/Views ratio: {(self.df['likes'].sum() / self.df['views'].sum() * 100):.2f}%")
        print(f"  Retweets/Views ratio: {(self.df['retweets'].sum() / self.df['views'].sum() * 100):.2f}%")
        print(f"  Replies/Views ratio: {(self.df['replies'].sum() / self.df['views'].sum() * 100):.2f}%")
        
        # Content type analysis
        print(f"\n📝 Content Type Analysis:")
        reply_tweets = self.df[self.df['is_reply'] == True]
        original_tweets = self.df[self.df['is_reply'] == False]
        
        print(f"  Original tweets: {len(original_tweets)} ({len(original_tweets)/len(self.df)*100:.1f}%)")
        print(f"  Reply tweets: {len(reply_tweets)} ({len(reply_tweets)/len(self.df)*100:.1f}%)")
        
        if len(original_tweets) > 0:
            print(f"  Original tweet avg likes: {original_tweets['likes'].mean():.1f}")
        if len(reply_tweets) > 0:
            print(f"  Reply tweet avg likes: {reply_tweets['likes'].mean():.1f}")
        
        # Media analysis
        media_tweets = self.df[self.df['has_media'] == True]
        text_only_tweets = self.df[self.df['has_media'] == False]
        
        print(f"\n🖼️  Media Analysis:")
        print(f"  Media tweets: {len(media_tweets)} ({len(media_tweets)/len(self.df)*100:.1f}%)")
        print(f"  Text-only tweets: {len(text_only_tweets)} ({len(text_only_tweets)/len(self.df)*100:.1f}%)")
        
        if len(media_tweets) > 0:
            print(f"  Media tweet avg likes: {media_tweets['likes'].mean():.1f}")
        if len(text_only_tweets) > 0:
            print(f"  Text-only tweet avg likes: {text_only_tweets['likes'].mean():.1f}")
        
        # Automation analysis
        automated_tweets = self.df[self.df['is_automated'] == True]
        manual_tweets = self.df[self.df['is_automated'] == False]
        
        print(f"\n🤖 Automation Analysis:")
        print(f"  Automated tweets: {len(automated_tweets)} ({len(automated_tweets)/len(self.df)*100:.1f}%)")
        print(f"  Manual tweets: {len(manual_tweets)} ({len(manual_tweets)/len(self.df)*100:.1f}%)")
        
        if len(automated_tweets) > 0:
            print(f"  Automated tweet avg likes: {automated_tweets['likes'].mean():.1f}")
        if len(manual_tweets) > 0:
            print(f"  Manual tweet avg likes: {manual_tweets['likes'].mean():.1f}")
    
    def create_visualizations(self):
        """Create visualizations for the analysis."""
        print("\n🎨 Creating visualizations...")
        
        if self.df is None or len(self.df) == 0:
            return
        
        # Set up the plotting style
        plt.style.use('default')
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('@NTFabiano 2023 Twitter Engagement Analysis', fontsize=16, fontweight='bold')
        
        # 1. Daily likes over time (chronological timeline)
        ax1 = axes[0, 0]
        daily_likes = self.df.groupby('date')['likes'].sum()
        ax1.plot(daily_likes.index, daily_likes.values, linewidth=2, color='#1DA1F2', marker='o', markersize=4)
        ax1.set_title('Daily Total Likes Over Time (Chronological)', fontweight='bold')
        ax1.set_xlabel('Date')
        ax1.set_ylabel('Total Likes (Y-axis)')
        ax1.tick_params(axis='x', rotation=45)
        ax1.grid(True, alpha=0.3)
        
        # 2. Monthly likes distribution
        ax2 = axes[0, 1]
        monthly_likes = self.df.groupby('month')['likes'].sum()
        months_order = ['January', 'February', 'March', 'April', 'May', 'June', 
                       'July', 'August', 'September', 'October', 'November', 'December']
        
        # Handle missing months by filling with 0
        monthly_likes_filled = monthly_likes.reindex(months_order, fill_value=0)
        
        bars = ax2.bar(range(len(months_order)), monthly_likes_filled.values, color='#E0245E')
        ax2.set_title('Total Likes by Month', fontweight='bold')
        ax2.set_xlabel('Month')
        ax2.set_ylabel('Total Likes')
        ax2.set_xticks(range(len(months_order)))
        ax2.set_xticklabels([m[:3] for m in months_order], rotation=45)
        
        # Add value labels on bars (only for non-zero values)
        for i, bar in enumerate(bars):
            height = bar.get_height()
            if height > 0:
                ax2.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                        f'{int(height):,}', ha='center', va='bottom', fontweight='bold')
        
        # 3. Hourly engagement patterns
        ax3 = axes[1, 0]
        hourly_stats = self.df.groupby('hour')['likes'].agg(['mean', 'count']).round(1)
        
        # Create dual y-axis plot
        ax3_twin = ax3.twinx()
        
        line1 = ax3.plot(hourly_stats.index, hourly_stats['mean'], 'o-', color='#17BF63', 
                         linewidth=2, markersize=8, label='Avg Likes')
        line2 = ax3_twin.plot(hourly_stats.index, hourly_stats['count'], 's-', color='#794BC4', 
                              linewidth=2, markersize=8, label='Tweet Count')
        
        ax3.set_title('Hourly Engagement Patterns', fontweight='bold')
        ax3.set_xlabel('Hour of Day')
        ax3.set_ylabel('Average Likes', color='#17BF63')
        ax3_twin.set_ylabel('Number of Tweets', color='#794BC4')
        ax3.set_xticks(range(0, 24))
        ax3.grid(True, alpha=0.3)
        
        # Add legend
        lines = line1 + line2
        labels = [l.get_label() for l in lines]
        ax3.legend(lines, labels, loc='upper left')
        
        # 4. Day of week engagement
        ax4 = axes[1, 1]
        daily_stats = self.df.groupby('day_of_week')['likes'].agg(['mean', 'count']).round(1)
        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        daily_stats = daily_stats.reindex(days_order)
        
        x = np.arange(len(days_order))
        width = 0.35
        
        bars1 = ax4.bar(x - width/2, daily_stats['mean'], width, label='Avg Likes', color='#1DA1F2')
        bars2 = ax4.bar(x + width/2, daily_stats['count'], width, label='Tweet Count', color='#E0245E')
        
        ax4.set_title('Engagement by Day of Week', fontweight='bold')
        ax4.set_xlabel('Day of Week')
        ax4.set_ylabel('Count/Average')
        ax4.set_xticks(x)
        ax4.set_xticklabels([d[:3] for d in days_order])
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Save the plot
        output_file = os.path.join(self.data_dir, 'ntfabiano_2023_likes_analysis.png')
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"📊 Visualization saved to: {output_file}")
        
        # Create a separate chronological timeline chart
        self.create_timeline_chart()
        
        plt.show()
    
    def create_timeline_chart(self):
        """Create a dedicated chronological timeline chart with likes on Y-axis."""
        print("📈 Creating chronological timeline chart...")
        
        if self.df is None or len(self.df) == 0:
            return
        
        # Create a clean timeline chart
        plt.figure(figsize=(14, 8))
        
        # Sort by date and create timeline
        timeline_df = self.df.sort_values('created_at').copy()
        
        # Create the main timeline plot
        plt.plot(timeline_df['created_at'], timeline_df['likes'], 
                linewidth=2, color='#1DA1F2', alpha=0.7, label='Individual Tweet Likes')
        
        # Add markers for each tweet
        plt.scatter(timeline_df['created_at'], timeline_df['likes'], 
                   s=50, color='#E0245E', alpha=0.8, zorder=5)
        
        # Add rolling average line
        window_size = min(7, len(timeline_df))  # 7-day rolling average or smaller if not enough data
        if len(timeline_df) >= window_size:
            rolling_avg = timeline_df['likes'].rolling(window=window_size, center=True).mean()
            plt.plot(timeline_df['created_at'], rolling_avg, 
                    linewidth=3, color='#17BF63', alpha=0.9, 
                    label=f'{window_size}-Tweet Rolling Average')
        
        # Customize the chart
        plt.title('@NTFabiano 2023: Chronological Timeline of Tweet Likes', 
                 fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('Date (2023)', fontsize=12, fontweight='bold')
        plt.ylabel('Number of Likes (Y-axis)', fontsize=12, fontweight='bold')
        
        # Format x-axis
        plt.gca().xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%b %d'))
        plt.gca().xaxis.set_major_locator(plt.matplotlib.dates.MonthLocator(interval=1))
        plt.xticks(rotation=45)
        
        # Add grid and legend
        plt.grid(True, alpha=0.3, linestyle='--')
        plt.legend(fontsize=11)
        
        # Highlight top performing tweets
        top_tweets = timeline_df.nlargest(5, 'likes')
        for _, tweet in top_tweets.iterrows():
            plt.annotate(f"❤️ {tweet['likes']}", 
                        xy=(tweet['created_at'], tweet['likes']),
                        xytext=(10, 10), textcoords='offset points',
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7),
                        fontsize=9, fontweight='bold')
        
        # Add statistics text box
        stats_text = f"""Statistics:
Total Tweets: {len(timeline_df):,}
Total Likes: {timeline_df['likes'].sum():,}
Average Likes: {timeline_df['likes'].mean():.1f}
Peak Likes: {timeline_df['likes'].max():,}
Best Month: {timeline_df.groupby(timeline_df['created_at'].dt.month)['likes'].sum().idxmax()}"""
        
        plt.text(0.02, 0.98, stats_text, transform=plt.gca().transAxes, 
                fontsize=10, verticalalignment='top',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.8))
        
        plt.tight_layout()
        
        # Save the timeline chart
        timeline_file = os.path.join(self.data_dir, 'ntfabiano_2023_timeline_likes.png')
        plt.savefig(timeline_file, dpi=300, bbox_inches='tight')
        print(f"📊 Timeline chart saved to: {timeline_file}")
        
        plt.show()
    
    def save_analysis_report(self):
        """Save the analysis results to a JSON file."""
        print("\n💾 Saving analysis report...")
        
        if self.df is None or len(self.df) == 0:
            return
        
        # Prepare summary data
        report = {
            "analysis_date": datetime.now().isoformat(),
            "username": "NTFabiano",
            "year": 2023,
            "total_tweets": len(self.df),
            "total_likes": int(self.df['likes'].sum()),
            "total_retweets": int(self.df['retweets'].sum()),
            "total_replies": int(self.df['replies'].sum()),
            "total_views": int(self.df['views'].sum()),
            "average_likes_per_tweet": float(self.df['likes'].mean()),
            "median_likes_per_tweet": float(self.df['likes'].median()),
            "highest_likes": int(self.df['likes'].max()),
            "lowest_likes": int(self.df['likes'].min()),
            "monthly_breakdown": self.df.groupby('month')['likes'].sum().to_dict(),
            "daily_breakdown": self.df.groupby('day_of_week')['likes'].sum().to_dict(),
            "hourly_breakdown": self.df.groupby('hour')['likes'].sum().to_dict(),
            "top_performing_tweets": self.df.nlargest(10, 'likes')[['id', 'created_at', 'text', 'likes']].to_dict('records')
        }
        
        # Save report
        output_file = os.path.join(self.data_dir, 'ntfabiano_2023_likes_analysis_report.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"📋 Analysis report saved to: {output_file}")
    
    def run_full_analysis(self):
        """Run the complete analysis pipeline."""
        print("🚀 Starting @NTFabiano 2023 Likes Trend Analysis...")
        print("="*60)
        
        # Load and process data
        self.load_2023_data()
        if len(self.tweets_2023) == 0:
            print("❌ No 2023 data found. Please run the scraper first for 2023.")
            return
        
        self.parse_dates()
        self.create_dataframe()
        
        # Run analyses
        self.analyze_likes_trends()
        self.analyze_engagement_patterns()
        
        # Create visualizations and save report
        self.create_visualizations()
        self.save_analysis_report()
        
        print("\n✅ Analysis complete!")
        print(f"📁 All results saved in: {self.data_dir}")

def main():
    """Main function to run the analysis."""
    analyzer = NTFabiano2023Analyzer()
    analyzer.run_full_analysis()

if __name__ == "__main__":
    main()
