#!/usr/bin/env python3
"""
Script to plot likes progression over time for all tweets.
Creates line charts showing how likes evolved over time.
"""

import json
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import numpy as np

def load_all_tweets(username):
    """
    Load all tweets from JSON files.
    """
    print(f"🔍 Loading all tweets for @{username}...")
    
    tweets_dir = f"{username}_tweets_analysis"
    if not os.path.exists(tweets_dir):
        print(f"❌ Directory {tweets_dir} not found!")
        return []
    
    all_tweets = []
    
    # Load all JSON files
    for filename in os.listdir(tweets_dir):
        if filename.startswith(f'tweets_{username}_') and filename.endswith('.json'):
            filepath = os.path.join(tweets_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        tweets = data
                    else:
                        tweets = []
                    
                    for tweet in tweets:
                        if isinstance(tweet, dict):
                            all_tweets.append(tweet)
            except Exception as e:
                print(f"⚠️ Error loading {filename}: {e}")
    
    print(f"📊 Total tweets loaded: {len(all_tweets)}")
    return all_tweets

def parse_tweet_data(tweets):
    """
    Parse tweet data and extract relevant information.
    """
    print("📝 Parsing tweet data...")
    
    parsed_data = []
    
    for tweet in tweets:
        try:
            # Parse timestamp
            timestamp = None
            for field in ['createdAt', 'created_at', 'date']:
                if field in tweet and tweet[field]:
                    try:
                        # Try Twitter format: "Sun Aug 24 19:57:28 +0000 2025"
                        if '+' in tweet[field] and len(tweet[field].split()) >= 6:
                            timestamp = datetime.strptime(tweet[field], '%a %b %d %H:%M:%S %z %Y')
                        else:
                            # Try ISO format
                            timestamp = datetime.fromisoformat(tweet[field].replace('Z', '+00:00'))
                        break
                    except:
                        continue
            
            if timestamp:
                # Extract likes
                likes = tweet.get('likeCount', tweet.get('favoriteCount', 0))
                retweets = tweet.get('retweetCount', 0)
                replies = tweet.get('replyCount', 0)
                quote_count = tweet.get('quoteCount', 0)
                
                # Calculate total engagement
                total_engagement = likes + retweets + replies + quote_count
                
                parsed_data.append({
                    'timestamp': timestamp,
                    'date': timestamp.date(),
                    'datetime': timestamp,
                    'likes': likes,
                    'retweets': retweets,
                    'replies': replies,
                    'quotes': quote_count,
                    'total_engagement': total_engagement,
                    'tweet_id': tweet.get('id', ''),
                    'text': tweet.get('text', tweet.get('fullText', ''))[:100] + '...' if tweet.get('text') else ''
                })
        
        except Exception as e:
            print(f"⚠️ Error parsing tweet: {e}")
            continue
    
    print(f"✅ Successfully parsed {len(parsed_data)} tweets")
    return parsed_data

def create_likes_progression_charts(data, username):
    """
    Create comprehensive charts showing likes progression over time.
    """
    print("📈 Creating likes progression charts...")
    
    # Convert to DataFrame
    df = pd.DataFrame(data)
    df = df.sort_values('datetime')
    
    # Focus on first 14 days of data
    first_date = df['datetime'].min()
    last_date = first_date + pd.Timedelta(days=14)
    df = df[df['datetime'] <= last_date].copy()
    
    print(f"📅 Focusing on first 14 days:")
    print(f"   First tweet: {first_date.strftime('%Y-%m-%d %H:%M')}")
    print(f"   Last tweet in range: {last_date.strftime('%Y-%m-%d %H:%M')}")
    print(f"   Tweets in range: {len(df)}")
    print(f"   Date range: {first_date.strftime('%Y-%m-%d')} to {last_date.strftime('%Y-%m-%d')}")
    
    # Create figure with multiple subplots
    fig, axes = plt.subplots(2, 2, figsize=(20, 16))
    fig.suptitle(f'Likes Progression Analysis for @{username} - First 14 Days', fontsize=20, fontweight='bold')
    
    # 1. Main likes progression over time
    ax1 = axes[0, 0]
    ax1.plot(df['datetime'], df['likes'], marker='o', markersize=2, alpha=0.7, linewidth=1)
    ax1.set_title('Likes Progression Over Time', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Date', fontsize=12)
    ax1.set_ylabel('Number of Likes', fontsize=12)
    ax1.grid(True, alpha=0.3)
    
    # Add trend line
    z = np.polyfit(range(len(df)), df['likes'], 1)
    p = np.poly1d(z)
    ax1.plot(df['datetime'], p(range(len(df))), "--", alpha=0.8, color='red', linewidth=2)
    
    # 2. Daily average likes
    ax2 = axes[0, 1]
    daily_avg = df.groupby('date')['likes'].mean()
    ax2.plot(daily_avg.index, daily_avg.values, marker='o', markersize=4, linewidth=2, color='green')
    ax2.set_title('Daily Average Likes', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Date', fontsize=12)
    ax2.set_ylabel('Average Likes per Day', fontsize=12)
    ax2.grid(True, alpha=0.3)
    
    # 3. Likes distribution histogram
    ax3 = axes[1, 0]
    ax3.hist(df['likes'], bins=50, alpha=0.7, edgecolor='black', color='skyblue')
    ax3.set_title('Distribution of Likes', fontsize=14, fontweight='bold')
    ax3.set_xlabel('Number of Likes', fontsize=12)
    ax3.set_ylabel('Frequency', fontsize=12)
    ax3.grid(True, alpha=0.3)
    
    # Add statistics
    mean_likes = df['likes'].mean()
    median_likes = df['likes'].median()
    ax3.axvline(mean_likes, color='red', linestyle='--', label=f'Mean: {mean_likes:.1f}')
    ax3.axvline(median_likes, color='orange', linestyle='--', label=f'Median: {median_likes:.1f}')
    ax3.legend()
    
    # 4. Engagement correlation
    ax4 = axes[1, 1]
    ax4.scatter(df['likes'], df['total_engagement'], alpha=0.6, s=20)
    ax4.set_title('Likes vs Total Engagement', fontsize=14, fontweight='bold')
    ax4.set_xlabel('Likes', fontsize=12)
    ax4.set_ylabel('Total Engagement', fontsize=12)
    ax4.grid(True, alpha=0.3)
    
    # Add trend line
    z_eng = np.polyfit(df['likes'], df['total_engagement'], 1)
    p_eng = np.poly1d(z_eng)
    ax4.plot(df['likes'], p_eng(df['likes']), "--", alpha=0.8, color='red', linewidth=2)
    
    plt.tight_layout()
    
    # Save the chart
    output_filename = f"{username}_likes_progression_analysis.png"
    plt.savefig(output_filename, dpi=300, bbox_inches='tight')
    print(f"✅ Chart saved: {output_filename}")
    
    return fig

def create_detailed_timeline_chart(data, username):
    """
    Create a detailed timeline chart with annotations.
    """
    print("📅 Creating detailed timeline chart...")
    
    df = pd.DataFrame(data)
    df = df.sort_values('datetime')
    
    # Focus on first 14 days of data (same as main chart)
    first_date = df['datetime'].min()
    last_date = first_date + pd.Timedelta(days=14)
    df = df[df['datetime'] <= last_date].copy()
    
    print(f"📅 Timeline chart - focusing on first 14 days:")
    print(f"   Tweets in range: {len(df)}")
    
    # Create figure
    fig, ax = plt.subplots(figsize=(24, 12))
    
    # Plot likes over time
    ax.plot(df['datetime'], df['likes'], marker='o', markersize=3, alpha=0.8, linewidth=1.5, color='blue')
    
    # Highlight top tweets
    top_tweets = df.nlargest(10, 'likes')
    ax.scatter(top_tweets['datetime'], top_tweets['likes'], 
               color='red', s=100, alpha=0.8, zorder=5, label='Top 10 Tweets')
    
    # Add annotations for top tweets
    for idx, row in top_tweets.iterrows():
        ax.annotate(f"{row['likes']} likes", 
                   xy=(row['datetime'], row['likes']),
                   xytext=(10, 10), textcoords='offset points',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7),
                   fontsize=8, ha='left')
    
    # Add trend line
    z = np.polyfit(range(len(df)), df['likes'], 1)
    p = np.poly1d(z)
    ax.plot(df['datetime'], p(range(len(df))), "--", alpha=0.8, color='red', linewidth=3, label='Trend Line')
    
    # Customize chart
    ax.set_title(f'Detailed Likes Timeline for @{username} - First 14 Days', fontsize=18, fontweight='bold', pad=20)
    ax.set_xlabel('Date', fontsize=14)
    ax.set_ylabel('Number of Likes', fontsize=14)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=12)
    
    # Rotate x-axis labels
    plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
    
    plt.tight_layout()
    
    # Save the chart
    output_filename = f"{username}_detailed_likes_timeline.png"
    plt.savefig(output_filename, dpi=300, bbox_inches='tight')
    print(f"✅ Detailed timeline saved: {output_filename}")
    
    return fig

def print_statistics(data):
    """
    Print comprehensive statistics about likes.
    """
    print("\n📊 LIKES STATISTICS")
    print("=" * 50)
    
    likes_list = [tweet['likes'] for tweet in data]
    
    print(f"Total tweets analyzed: {len(data)}")
    print(f"Total likes received: {sum(likes_list):,}")
    print(f"Average likes per tweet: {np.mean(likes_list):.2f}")
    print(f"Median likes per tweet: {np.median(likes_list):.2f}")
    print(f"Standard deviation: {np.std(likes_list):.2f}")
    print(f"Minimum likes: {min(likes_list)}")
    print(f"Maximum likes: {max(likes_list)}")
    
    # Top tweets
    top_tweets = sorted(data, key=lambda x: x['likes'], reverse=True)[:10]
    print(f"\n🏆 TOP 10 TWEETS BY LIKES:")
    print("-" * 50)
    
    for i, tweet in enumerate(top_tweets, 1):
        print(f"{i:2d}. {tweet['likes']:3d} likes - {tweet['datetime'].strftime('%Y-%m-%d %H:%M')}")
        print(f"    {tweet['text']}")
        print()

def main():
    """
    Main function to create likes progression analysis.
    """
    username = "apralky"
    
    print(f"🚀 LIKES PROGRESSION ANALYSIS FOR @{username}")
    print("=" * 60)
    
    try:
        # 1. Load all tweets
        tweets = load_all_tweets(username)
        if not tweets:
            print("❌ No tweets found!")
            return
        
        # 2. Parse tweet data
        data = parse_tweet_data(tweets)
        if not data:
            print("❌ No data parsed!")
            return
        
        # 3. Create charts
        create_likes_progression_charts(data, username)
        create_detailed_timeline_chart(data, username)
        
        # 4. Print statistics
        print_statistics(data)
        
        print(f"\n🎉 ANALYSIS COMPLETED FOR @{username}!")
        print("📁 Files created:")
        print(f"   📈 {username}_likes_progression_analysis.png")
        print(f"   📅 {username}_detailed_likes_timeline.png")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        raise

if __name__ == "__main__":
    main()
