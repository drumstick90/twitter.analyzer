#!/usr/bin/env python3
"""
Flexible exporter to dump all scraped tweets from a directory into
- a readable text file, and
- a CSV for analysis.

Works with folders like "<username>_tweets_analysis" created by the scrapers.
You can pass the input directory explicitly or just provide the username.
"""

import json
import os
import argparse
from datetime import datetime

def derive_username_from_dir(input_dir: str) -> str | None:
    base = os.path.basename(os.path.normpath(input_dir))
    suffix = "_tweets_analysis"
    if base.endswith(suffix):
        return base[:-len(suffix)]
    return None

def export_tweets_to_text(input_dir: str, username: str) -> str | None:
    """
    Export all tweets from input_dir to a simple text file.
    """
    print(f"📝 Exporting all tweets for @{username} to text file...")
    tweets_dir = input_dir
    if not os.path.isdir(tweets_dir):
        print(f"❌ Directory {tweets_dir} non trovata!")
        return None
    
    all_tweets = []
    
    # Carica tutti i file JSON
    for filename in os.listdir(tweets_dir):
        if not filename.endswith('.json'):
            continue
        # If username is known, filter by its prefix; otherwise accept all tweets_*.json
        if username and filename.startswith(f'tweets_{username}_') or (not username and filename.startswith('tweets_')):
            filepath = os.path.join(tweets_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        all_tweets.extend(data)
                    elif isinstance(data, dict):
                        if 'tweets' in data and isinstance(data['tweets'], list):
                            all_tweets.extend(data['tweets'])
                        elif 'data' in data and isinstance(data['data'], dict) and isinstance(data['data'].get('tweets'), list):
                            all_tweets.extend(data['data']['tweets'])
            except Exception as e:
                print(f"⚠️ Error loading {filename}: {e}")
    
    print(f"✅ Loaded {len(all_tweets)} tweets")
    
    # Ordina per data
    def parse_twitter_date(date_str):
        try:
            return datetime.strptime(date_str, '%a %b %d %H:%M:%S %z %Y')
        except:
            return datetime.min
    
    all_tweets.sort(key=lambda x: parse_twitter_date(x.get('createdAt', '')))
    
    # Esporta in file di testo
    output_file = f"{username}_all_tweets.txt"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"ALL TWEETS BY @{username}\n")
        f.write("=" * 60 + "\n\n")
        
        for i, tweet in enumerate(all_tweets, 1):
            # Estrai data
            created_at = tweet.get('createdAt', 'Unknown date')
            
            # Estrai testo
            text = tweet.get('text', tweet.get('fullText', 'No text'))
            
            # Estrai metriche
            likes = tweet.get('likeCount', 0)
            retweets = tweet.get('retweetCount', 0)
            replies = tweet.get('replyCount', 0)
            
            # Scrivi nel file
            f.write(f"Tweet #{i:04d} - {created_at}\n")
            f.write(f"❤️ {likes} | 🔄 {retweets} | 💬 {replies}\n")
            f.write(f"{text}\n")
            f.write("-" * 80 + "\n\n")
    
    print(f"✅ All tweets exported to: {output_file}")
    print(f"📊 Total tweets: {len(all_tweets)}")
    
    return output_file

def export_tweets_to_csv(input_dir: str, username: str) -> str | None:
    """
    Export all tweets from input_dir to CSV format.
    """
    print(f"📊 Exporting all tweets for @{username} to CSV...")
    tweets_dir = input_dir
    if not os.path.isdir(tweets_dir):
        print(f"❌ Directory {tweets_dir} non trovata!")
        return None
    
    all_tweets = []
    
    # Carica tutti i file JSON
    for filename in os.listdir(tweets_dir):
        if not filename.endswith('.json'):
            continue
        if username and filename.startswith(f'tweets_{username}_') or (not username and filename.startswith('tweets_')):
            filepath = os.path.join(tweets_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        all_tweets.extend(data)
                    elif isinstance(data, dict):
                        if 'tweets' in data and isinstance(data['tweets'], list):
                            all_tweets.extend(data['tweets'])
                        elif 'data' in data and isinstance(data['data'], dict) and isinstance(data['data'].get('tweets'), list):
                            all_tweets.extend(data['data']['tweets'])
            except Exception as e:
                print(f"⚠️ Error loading {filename}: {e}")
    
    # Ordina per data
    def parse_twitter_date(date_str):
        try:
            return datetime.strptime(date_str, '%a %b %d %H:%M:%S %z %Y')
        except:
            return datetime.min
    
    all_tweets.sort(key=lambda x: parse_twitter_date(x.get('createdAt', '')))
    
    # Esporta in CSV
    output_file = f"{username}_all_tweets.csv"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        # Header
        f.write("Tweet Number,Date,Text,Likes,Retweets,Replies,Quotes\n")
        
        for i, tweet in enumerate(all_tweets, 1):
            created_at = tweet.get('createdAt', 'Unknown date')
            text = tweet.get('text', tweet.get('fullText', 'No text')).replace('"', '""')
            likes = tweet.get('likeCount', 0)
            retweets = tweet.get('retweetCount', 0)
            replies = tweet.get('replyCount', 0)
            quotes = tweet.get('quoteCount', 0)
            
            # CSV format with quotes around text
            f.write(f'{i},"{created_at}","{text}",{likes},{retweets},{replies},{quotes}\n')
    
    print(f"✅ All tweets exported to CSV: {output_file}")
    return output_file

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Export all scraped tweets from a directory into text and CSV",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python export_all_tweets.py -u turintrader
  python export_all_tweets.py --input-dir turintrader_tweets_analysis
  python export_all_tweets.py -u md_pier --input-dir md_pier_tweets_analysis
        """
    )

    parser.add_argument(
        '-u', '--username',
        help='Twitter username (used for file filtering and output names)'
    )
    parser.add_argument(
        '-d', '--input-dir',
        help='Input directory containing tweets_*.json files (defaults to <username>_tweets_analysis)'
    )

    args = parser.parse_args()

    input_dir = args.input_dir
    username = args.username

    if not input_dir:
        if username:
            input_dir = f"{username}_tweets_analysis"
        else:
            print("❌ ERROR: Provide --input-dir or --username so I can locate tweets.")
            print("Examples:")
            print("  python export_all_tweets.py -u turintrader")
            print("  python export_all_tweets.py --input-dir turintrader_tweets_analysis")
            raise SystemExit(1)

    # Derive username from directory name if missing
    if not username:
        username = derive_username_from_dir(input_dir) or os.path.basename(os.path.normpath(input_dir))

    print(f"🚀 EXPORTING ALL TWEETS FOR @{username}")
    print("=" * 60)

    text_file = export_tweets_to_text(input_dir, username)
    csv_file = export_tweets_to_csv(input_dir, username)

    print(f"\n🎉 Export completed!")
    if text_file:
        print(f"📖 Readable text file: {text_file}")
    if csv_file:
        print(f"📊 CSV file for analysis: {csv_file}")
    if text_file:
        print(f"\n💡 Tip: Open {text_file} in any text editor to read all tweets!")



