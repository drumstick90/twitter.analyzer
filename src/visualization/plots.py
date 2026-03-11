import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
import numpy as np
import pandas as pd

def fig_to_base64(fig):
    """Convert a matplotlib figure to a base64 string."""
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return img_str

def plot_growth_escalation(monthly_stats, quarterly_stats, weekly_stats, username, year):
    """
    Create visualization for growth escalation.
    """
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 16))
    fig.suptitle(f'GROWTH ESCALATION ANALYSIS @{username} - {year}\nIncreasing Intensity Pattern Over Time', 
                 fontsize=20, fontweight='bold', y=0.98)
    
    # 1. Monthly Trend
    months = range(len(monthly_stats))
    ax1.plot(months, monthly_stats['tweets_totali'], 'o-', linewidth=3, markersize=8, color='#2196F3')
    ax1.fill_between(months, monthly_stats['tweets_totali'], alpha=0.3, color='#2196F3')
    ax1.set_title('Monthly Escalation: Total Tweets', fontsize=16, fontweight='bold')
    ax1.set_xlabel('Month', fontsize=12)
    ax1.set_ylabel('Total Tweets', fontsize=12)
    ax1.set_xticks(months)
    ax1.set_xticklabels(monthly_stats['month_name'])
    ax1.grid(True, alpha=0.3)
    
    # Add trend line
    if len(months) > 1:
        z = np.polyfit(months, monthly_stats['tweets_totali'], 1)
        p = np.poly1d(z)
        ax1.plot(months, p(months), "--", color='red', alpha=0.8, linewidth=2, label=f'Trend: {z[0]:.1f}x + {z[1]:.1f}')
        ax1.legend()
    
    # 2. Quarterly Trend
    quarters = range(len(quarterly_stats))
    ax2.plot(quarters, quarterly_stats['tweets_totali'], 's-', linewidth=3, markersize=8, color='#4CAF50')
    ax2.fill_between(quarters, quarterly_stats['tweets_totali'], alpha=0.3, color='#4CAF50')
    ax2.set_title('Quarterly Escalation: Total Tweets', fontsize=16, fontweight='bold')
    ax2.set_xlabel('Quarter', fontsize=12)
    ax2.set_ylabel('Total Tweets', fontsize=12)
    ax2.set_xticks(quarters)
    ax2.set_xticklabels([f'Q{q}' for q in quarterly_stats['quarter']])
    ax2.grid(True, alpha=0.3)
    
    # Add trend line
    if len(quarters) > 1:
        z = np.polyfit(quarters, quarterly_stats['tweets_totali'], 1)
        p = np.poly1d(z)
        ax2.plot(quarters, p(quarters), "--", color='red', alpha=0.8, linewidth=2, label=f'Trend: {z[0]:.1f}x + {z[1]:.1f}')
        ax2.legend()
    
    # 3. Weekly Trend
    weeks = range(len(weekly_stats))
    ax3.plot(weeks, weekly_stats['tweets_totali'], '^-', linewidth=2, markersize=6, color='#FF9800')
    ax3.set_title('Weekly Escalation: Total Tweets', fontsize=16, fontweight='bold')
    ax3.set_xlabel('Week of Year', fontsize=12)
    ax3.set_ylabel('Total Tweets', fontsize=12)
    ax3.grid(True, alpha=0.3)
    
    # Add trend line
    if len(weeks) > 1:
        z = np.polyfit(weeks, weekly_stats['tweets_totali'], 1)
        p = np.poly1d(z)
        ax3.plot(weeks, p(weeks), "--", color='red', alpha=0.8, linewidth=2, label=f'Trend: {z[0]:.1f}x + {z[1]:.1f}')
        ax3.legend()
    
    # 4. Comparison Table
    ax4.axis('off')
    
    # Calculate comparison stats
    first_month = monthly_stats.iloc[0]
    last_month = monthly_stats.iloc[-1]
    first_quarter = quarterly_stats.iloc[0]
    last_quarter = quarterly_stats.iloc[-1]
    
    comparison_data = [
        ['METRIC', 'START OF YEAR', 'END OF YEAR', 'GROWTH'],
        ['Monthly Tweets', f"{first_month['tweets_totali']}", f"{last_month['tweets_totali']}", 
            f"{((last_month['tweets_totali'] - first_month['tweets_totali']) / first_month['tweets_totali'] * 100):+.1f}%"],
        ['Quarterly Tweets', f"{first_quarter['tweets_totali']}", f"{last_quarter['tweets_totali']}", 
            f"{((last_quarter['tweets_totali'] - first_quarter['tweets_totali']) / first_quarter['tweets_totali'] * 100):+.1f}%"],
        ['Avg Daily', f"{first_quarter['avg_daily']:.1f}", f"{last_quarter['avg_daily']:.1f}", 
            f"{((last_quarter['avg_daily'] - first_quarter['avg_daily']) / first_quarter['avg_daily'] * 100):+.1f}%"],
        ['Monthly Threads', f"{first_month['thread_count']}", f"{last_month['thread_count']}", 
            f"{((last_month['thread_count'] - first_month['thread_count']) / max(first_month['thread_count'], 1) * 100):+.1f}%"]
    ]
    
    table = ax4.table(cellText=comparison_data[1:], colLabels=comparison_data[0], 
                        cellLoc='center', loc='center', bbox=[0, 0, 1, 1])
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1, 2.5)
    
    # Table style
    for i in range(len(comparison_data)):
        for j in range(len(comparison_data[0])):
            if i == 0:  # Header
                table[(i, j)].set_facecolor('#4CAF50')
                table[(i, j)].set_text_props(weight='bold', color='white')
            elif j == 0:  # First column
                table[(i, j)].set_facecolor('#2196F3')
                table[(i, j)].set_text_props(weight='bold', color='white')
            else:
                table[(i, j)].set_facecolor('#f0f0f0')
    
    plt.tight_layout()
    return fig_to_base64(fig)

def plot_hourly_heatmap(df, username, year):
    """
    Create hourly heatmap visualization.
    """
    hour_cols = [f'hour_{hour:02d}' for hour in range(24)]
    heatmap_data = df[hour_cols].values
    
    fig, ax = plt.subplots(figsize=(20, 12))
    
    im = sns.heatmap(heatmap_data.T, 
                     cmap='YlOrRd', 
                     cbar_kws={'label': 'Number of Tweets'},
                     ax=ax)
    
    ax.set_title(f'Hourly Activity Heatmap @{username} - {year}', 
                 fontsize=18, fontweight='bold', pad=20)
    ax.set_xlabel('Day of Year', fontsize=14)
    ax.set_ylabel('Hour of Day', fontsize=14)
    
    y_ticks = range(24)
    y_labels = [f'{hour:02d}:00' for hour in y_ticks]
    ax.set_yticks(y_ticks)
    ax.set_yticklabels(y_labels)
    
    # X-axis labels (approximate)
    if 'date_short' in df.columns:
        x_ticks = np.linspace(0, len(df)-1, 12, dtype=int)
        x_labels = [df.iloc[i]['date_short'] for i in x_ticks]
        ax.set_xticks(x_ticks)
        ax.set_xticklabels(x_labels, rotation=45, ha='right')
    
    plt.tight_layout()
    return fig_to_base64(fig)

def plot_likes_analysis(daily_stats, monthly_stats, username):
    """
    Create visualization for likes analysis.
    """
    plt.style.use('default')
    sns.set_palette("husl")
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle(f'@{username} - Daily Likes Analysis', fontsize=16, fontweight='bold')
    
    # 1. Daily Total Likes Line Plot
    ax1 = axes[0, 0]
    ax1.plot(daily_stats['date'], daily_stats['total_likes'], 
             marker='o', markersize=4, linewidth=2, color='#1DA1F2')
    ax1.set_title('Daily Total Likes', fontweight='bold')
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Total Likes')
    ax1.grid(True, alpha=0.3)
    
    # Add trend line
    if len(daily_stats) > 1:
        z = np.polyfit(range(len(daily_stats)), daily_stats['total_likes'], 1)
        p = np.poly1d(z)
        ax1.plot(daily_stats['date'], p(range(len(daily_stats))), 
                 "--", alpha=0.8, color='red', label=f'Trend: {z[0]:.1f}')
        ax1.legend()
    
    # 2. Daily Average Likes Bar Plot
    ax2 = axes[0, 1]
    bars = ax2.bar(range(len(daily_stats)), daily_stats['avg_likes'], 
                   color='#17A2B8', alpha=0.7)
    ax2.set_title('Average Likes per Tweet (Daily)', fontweight='bold')
    ax2.set_xlabel('Days')
    ax2.set_ylabel('Average Likes')
    ax2.grid(True, alpha=0.3)
    
    # 3. Monthly Comparison
    ax3 = axes[1, 0]
    months = [m.strftime('%b') for m in monthly_stats['month']]
    x = np.arange(len(months))
    
    if len(x) > 0:
        bars1 = ax3.bar(x - 0.2, monthly_stats['total_likes'], 0.4, 
                        label='Total Likes', color='#28A745')
        bars2 = ax3.bar(x + 0.2, monthly_stats['avg_likes'], 0.4, 
                        label='Avg Likes', color='#FFC107')
        
        ax3.set_title('Monthly Comparison', fontweight='bold')
        ax3.set_xlabel('Month')
        ax3.set_ylabel('Likes')
        ax3.set_xticks(x)
        ax3.set_xticklabels(months)
        ax3.legend()
        ax3.grid(True, alpha=0.3)
    
    # 4. Tweet Count vs Likes Scatter
    ax4 = axes[1, 1]
    scatter = ax4.scatter(daily_stats['tweet_count'], daily_stats['total_likes'], 
                          c=daily_stats['avg_likes'], cmap='viridis', 
                          s=50, alpha=0.7)
    ax4.set_title('Tweet Count vs Total Likes', fontweight='bold')
    ax4.set_xlabel('Number of Tweets')
    ax4.set_ylabel('Total Likes')
    ax4.grid(True, alpha=0.3)
    
    # Add colorbar
    cbar = plt.colorbar(scatter, ax=ax4)
    cbar.set_label('Avg Likes per Tweet')
    
    plt.tight_layout()
    return fig_to_base64(fig)
