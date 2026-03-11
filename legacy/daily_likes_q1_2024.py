#!/usr/bin/env python3
"""
Script to aggregate daily likes for Q1 2024 and create visualizations.
"""

import json
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import numpy as np

def analyze_daily_likes_q1():
    """Analyze daily likes for Q1 2024 and create visualizations."""
    
    data_dir = "NTFabiano_tweets_analysis"
    
    print("📊 ANALIZZANDO LIKES GIORNALIERI Q1 2024...")
    print("="*60)
    
    # Find all 2024 files
    files = [f for f in os.listdir(data_dir) if f.startswith("tweets_NTFabiano_2024_page_")]
    files.sort()
    
    print(f"📁 Caricando {len(files)} file 2024...")
    
    all_tweets = []
    
    # Load all tweets
    for file in files:
        file_path = os.path.join(data_dir, file)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tweets = json.load(f)
                all_tweets.extend(tweets)
        except Exception as e:
            print(f"❌ Errore caricando {file}: {e}")
    
    print(f"✅ Caricati {len(all_tweets)} tweet totali")
    
    # Parse dates and filter Q1 2024 (Jan-Mar)
    q1_tweets = []
    
    for tweet in all_tweets:
        if 'createdAt' in tweet:
            try:
                date_str = tweet['createdAt']
                parsed_date = datetime.strptime(date_str, "%a %b %d %H:%M:%S %z %Y")
                
                # Filter Q1 2024 (January 1 - March 31)
                if parsed_date.year == 2024 and parsed_date.month in [1, 2, 3]:
                    tweet_info = {
                        'id': tweet.get('id', 'N/A'),
                        'created_at': parsed_date,
                        'date': parsed_date.date(),
                        'likes': tweet.get('likeCount', 0),
                        'retweets': tweet.get('retweetCount', 0),
                        'replies': tweet.get('replyCount', 0),
                        'text': tweet.get('text', 'N/A'),
                        'source': tweet.get('source', 'N/A'),
                        'is_reply': tweet.get('isReply', False)
                    }
                    q1_tweets.append(tweet_info)
                    
            except Exception as e:
                continue
    
    print(f"📅 Tweet Q1 2024 (Gen-Mar): {len(q1_tweets)}")
    
    if not q1_tweets:
        print("❌ Nessun tweet trovato per Q1 2024")
        return
    
    # Create DataFrame
    df = pd.DataFrame(q1_tweets)
    
    # Aggregate by date
    daily_stats = df.groupby('date').agg({
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
    
    print(f"\n📊 STATISTICHE GIORNALIERE Q1 2024:")
    print("="*60)
    print(f"Giorni con tweet: {len(daily_stats)}")
    print(f"Tweet totali: {daily_stats['tweet_count'].sum()}")
    print(f"Likes totali: {daily_stats['total_likes'].sum():,}")
    print(f"Media likes per tweet: {daily_stats['avg_likes'].mean():.1f}")
    print(f"Tweet con più likes: {daily_stats['max_likes'].max():,}")
    
    # Show top 10 days by total likes
    print(f"\n🏆 TOP 10 GIORNI PER LIKES TOTALI:")
    print("-" * 60)
    top_days = daily_stats.nlargest(10, 'total_likes')
    for i, (_, day) in enumerate(top_days.iterrows(), 1):
        print(f"{i:2d}. {day['date'].strftime('%d/%m/%Y')} | "
              f"❤️ {day['total_likes']:6,} | "
              f"📝 {day['tweet_count']:2d} tweet | "
              f"📊 {day['avg_likes']:5.1f} media")
    
    # Show top 10 days by average likes
    print(f"\n📈 TOP 10 GIORNI PER MEDIA LIKES:")
    print("-" * 60)
    top_avg_days = daily_stats.nlargest(10, 'avg_likes')
    for i, (_, day) in enumerate(top_avg_days.iterrows(), 1):
        print(f"{i:2d}. {day['date'].strftime('%d/%m/%Y')} | "
              f"📊 {day['avg_likes']:6.1f} media | "
              f"❤️ {day['total_likes']:5,} totali | "
              f"📝 {day['tweet_count']:2d} tweet")
    
    # Monthly aggregation
    df['month'] = df['created_at'].dt.to_period('M')
    monthly_stats = df.groupby('month').agg({
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
    
    print(f"\n📅 STATISTICHE MENSILI Q1 2024:")
    print("-" * 60)
    for _, month in monthly_stats.iterrows():
        month_name = month['month'].strftime('%B %Y')
        print(f"{month_name:12} | "
              f"❤️ {month['total_likes']:6,} likes | "
              f"📝 {month['tweet_count']:3d} tweet | "
              f"📊 {month['avg_likes']:5.1f} media")
    
    # Create visualizations
    print(f"\n🎨 CREANDO GRAFICI...")
    create_q1_visualizations(daily_stats, monthly_stats, df)
    
    # Save detailed data
    print(f"\n💾 SALVANDO DATI...")
    
    # Save daily stats
    daily_stats.to_csv('q1_2024_daily_likes.csv', index=False)
    print(f"✅ Dati giornalieri salvati in: q1_2024_daily_likes.csv")
    
    # Save monthly stats
    monthly_stats.to_csv('q1_2024_monthly_likes.csv', index=False)
    print(f"✅ Dati mensili salvati in: q1_2024_monthly_likes.csv")
    
    # Save summary report
    create_summary_report(daily_stats, monthly_stats, df)
    
    print(f"\n🎯 ANALISI Q1 2024 COMPLETATA!")
    print("="*60)

def create_q1_visualizations(daily_stats, monthly_stats, df):
    """Create visualizations for Q1 2024 data."""
    
    # Set style
    plt.style.use('default')
    sns.set_palette("husl")
    
    # Create figure with subplots
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('@NTFabiano Q1 2024 - Analisi Likes Giornalieri', fontsize=16, fontweight='bold')
    
    # 1. Daily Total Likes Line Plot
    ax1 = axes[0, 0]
    ax1.plot(daily_stats['date'], daily_stats['total_likes'], 
             marker='o', markersize=4, linewidth=2, color='#1DA1F2')
    ax1.set_title('Likes Totali Giornalieri', fontweight='bold')
    ax1.set_xlabel('Data')
    ax1.set_ylabel('Likes Totali')
    ax1.grid(True, alpha=0.3)
    
    # Add trend line
    z = np.polyfit(range(len(daily_stats)), daily_stats['total_likes'], 1)
    p = np.poly1d(z)
    ax1.plot(daily_stats['date'], p(range(len(daily_stats))), 
             "--", alpha=0.8, color='red', label=f'Trend: {z[0]:.1f}')
    ax1.legend()
    
    # 2. Daily Average Likes Bar Plot
    ax2 = axes[0, 1]
    bars = ax2.bar(range(len(daily_stats)), daily_stats['avg_likes'], 
                   color='#17A2B8', alpha=0.7)
    ax2.set_title('Media Likes per Tweet (Giornaliera)', fontweight='bold')
    ax2.set_xlabel('Giorni')
    ax2.set_ylabel('Media Likes')
    ax2.grid(True, alpha=0.3)
    
    # Add value labels on bars
    for i, bar in enumerate(bars):
        height = bar.get_height()
        if height > 0:
            ax2.text(bar.get_x() + bar.get_width()/2., height + 1,
                    f'{height:.0f}', ha='center', va='bottom', fontsize=8)
    
    # 3. Monthly Comparison
    ax3 = axes[1, 0]
    months = [m.strftime('%b') for m in monthly_stats['month']]
    x = np.arange(len(months))
    
    bars1 = ax3.bar(x - 0.2, monthly_stats['total_likes'], 0.4, 
                    label='Likes Totali', color='#28A745')
    bars2 = ax3.bar(x + 0.2, monthly_stats['avg_likes'], 0.4, 
                    label='Media Likes', color='#FFC107')
    
    ax3.set_title('Confronto Mensile Q1 2024', fontweight='bold')
    ax3.set_xlabel('Mese')
    ax3.set_ylabel('Likes')
    ax3.set_xticks(x)
    ax3.set_xticklabels(months)
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Add value labels
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax3.text(bar.get_x() + bar.get_width()/2., height + 1,
                        f'{height:,.0f}', ha='center', va='bottom', fontsize=8)
    
    # 4. Tweet Count vs Likes Scatter
    ax4 = axes[1, 1]
    scatter = ax4.scatter(daily_stats['tweet_count'], daily_stats['total_likes'], 
                          c=daily_stats['avg_likes'], cmap='viridis', 
                          s=50, alpha=0.7)
    ax4.set_title('Tweet Count vs Likes Totali', fontweight='bold')
    ax4.set_xlabel('Numero Tweet')
    ax4.set_ylabel('Likes Totali')
    ax4.grid(True, alpha=0.3)
    
    # Add colorbar
    cbar = plt.colorbar(scatter, ax=ax4)
    cbar.set_label('Media Likes per Tweet')
    
    # Add trend line
    z = np.polyfit(daily_stats['tweet_count'], daily_stats['total_likes'], 1)
    p = np.poly1d(z)
    ax4.plot(daily_stats['tweet_count'], p(daily_stats['tweet_count']), 
             "--", alpha=0.8, color='red', label=f'Correlazione: {z[0]:.1f}')
    ax4.legend()
    
    # Adjust layout
    plt.tight_layout()
    
    # Save plot
    plt.savefig('q1_2024_daily_likes_analysis.png', dpi=300, bbox_inches='tight')
    print(f"✅ Grafico salvato in: q1_2024_daily_likes_analysis.png")
    
    # Show plot
    plt.show()

def create_summary_report(daily_stats, monthly_stats, df):
    """Create a summary report for Q1 2024."""
    
    report = {
        "period": "Q1 2024 (Gennaio - Marzo)",
        "summary": {
            "total_tweets": int(df.shape[0]),
            "total_likes": int(df['likes'].sum()),
            "total_retweets": int(df['retweets'].sum()),
            "total_replies": int(df['replies'].sum()),
            "days_with_tweets": int(daily_stats.shape[0]),
            "avg_likes_per_tweet": float(df['likes'].mean()),
            "max_likes_single_tweet": int(df['likes'].max())
        },
        "daily_stats": {
            "best_day_by_total_likes": {
                "date": daily_stats.loc[daily_stats['total_likes'].idxmax(), 'date'].strftime('%Y-%m-%d'),
                "total_likes": int(daily_stats['total_likes'].max()),
                "tweet_count": int(daily_stats.loc[daily_stats['total_likes'].idxmax(), 'tweet_count'])
            },
            "best_day_by_avg_likes": {
                "date": daily_stats.loc[daily_stats['avg_likes'].idxmax(), 'date'].strftime('%Y-%m-%d'),
                "avg_likes": float(daily_stats['avg_likes'].max()),
                "tweet_count": int(daily_stats.loc[daily_stats['avg_likes'].idxmax(), 'tweet_count'])
            }
        },
        "monthly_breakdown": []
    }
    
    # Add monthly breakdown
    for _, month in monthly_stats.iterrows():
        report["monthly_breakdown"].append({
            "month": month['month'].strftime('%B %Y'),
            "total_likes": int(month['total_likes']),
            "avg_likes": float(month['avg_likes']),
            "tweet_count": int(month['tweet_count'])
        })
    
    # Save report
    with open('q1_2024_likes_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Report salvato in: q1_2024_likes_report.json")
    
    # Print summary
    print(f"\n📋 RIEPILOGO Q1 2024:")
    print("="*60)
    print(f"📅 Periodo: {report['period']}")
    print(f"📝 Tweet totali: {report['summary']['total_tweets']:,}")
    print(f"❤️  Likes totali: {report['summary']['total_likes']:,}")
    print(f"🔄 Retweet totali: {report['summary']['total_retweets']:,}")
    print(f"💬 Reply totali: {report['summary']['total_replies']:,}")
    print(f"📊 Media likes per tweet: {report['summary']['avg_likes_per_tweet']:.1f}")
    print(f"🔥 Tweet con più likes: {report['summary']['max_likes_single_tweet']:,}")
    print(f"📅 Giorni con tweet: {report['summary']['days_with_tweets']}")

if __name__ == "__main__":
    analyze_daily_likes_q1()
