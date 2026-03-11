#!/usr/bin/env python3
"""
Script to check for duplicate tweets in the 2024 data.
"""

import json
import os
from collections import Counter
from datetime import datetime

def check_duplicates():
    """Check for duplicate tweets in the 2024 data."""
    
    data_dir = "NTFabiano_tweets_analysis"
    
    print("🔍 Checking for duplicate tweets in 2024 data...")
    
    # Find all 2024 files
    files = [f for f in os.listdir(data_dir) if f.startswith("tweets_NTFabiano_2024_page_")]
    files.sort()
    
    print(f"📁 Found {len(files)} 2024 data files")
    
    all_tweets = []
    tweet_ids = []
    duplicate_ids = []
    
    # Load all tweets
    for file in files:
        file_path = os.path.join(data_dir, file)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tweets = json.load(f)
                all_tweets.extend(tweets)
                print(f"✅ Loaded {len(tweets)} tweets from {file}")
        except Exception as e:
            print(f"❌ Error loading {file}: {e}")
    
    print(f"\n📊 Total tweets loaded: {len(all_tweets)}")
    
    # Check for duplicate IDs
    for tweet in all_tweets:
        tweet_id = tweet.get('id')
        if tweet_id:
            tweet_ids.append(tweet_id)
    
    # Find duplicate IDs
    id_counts = Counter(tweet_ids)
    duplicates = {tweet_id: count for tweet_id, count in id_counts.items() if count > 1}
    
    if duplicates:
        print(f"\n🚨 DUPLICATE TWEET IDs FOUND: {len(duplicates)}")
        print("="*60)
        for tweet_id, count in list(duplicates.items())[:10]:  # Show first 10
            print(f"Tweet ID {tweet_id}: appears {count} times")
    else:
        print(f"\n✅ No duplicate tweet IDs found")
    
    # Check for tweets posted at exactly the same time
    print(f"\n⏰ CHECKING TWEETS POSTED AT EXACTLY THE SAME TIME:")
    print("="*60)
    
    # Group tweets by exact timestamp
    timestamp_groups = {}
    for tweet in all_tweets:
        if 'createdAt' in tweet:
            timestamp = tweet['createdAt']
            if timestamp not in timestamp_groups:
                timestamp_groups[timestamp] = []
            timestamp_groups[timestamp].append(tweet)
    
    # Find timestamps with multiple tweets
    suspicious_timestamps = {ts: tweets for ts, tweets in timestamp_groups.items() if len(tweets) > 1}
    
    if suspicious_timestamps:
        print(f"🚨 Found {len(suspicious_timestamps)} timestamps with multiple tweets:")
        for timestamp, tweets in list(suspicious_timestamps.items())[:5]:  # Show first 5
            print(f"\n  📅 {timestamp} - {len(tweets)} tweets:")
            for i, tweet in enumerate(tweets[:3]):  # Show first 3 tweets
                print(f"    {i+1}. ID: {tweet.get('id', 'N/A')} | Text: {tweet.get('text', 'N/A')[:50]}...")
    else:
        print(f"✅ No tweets posted at exactly the same time")
    
    # Check the suspicious hour (12:00) specifically
    print(f"\n🔍 ANALYZING SUSPICIOUS HOUR (12:00):")
    print("="*60)
    
    hour_12_tweets = []
    for tweet in all_tweets:
        if 'createdAt' in tweet:
            try:
                # Parse the createdAt field
                date_str = tweet['createdAt']
                parsed_date = datetime.strptime(date_str, "%a %b %d %H:%M:%S %z %Y")
                if parsed_date.hour == 12:
                    hour_12_tweets.append(tweet)
            except Exception as e:
                continue
    
    print(f"📊 Tweets posted at 12:00: {len(hour_12_tweets)}")
    
    if hour_12_tweets:
        print(f"\n📅 Sample of 12:00 tweets:")
        for i, tweet in enumerate(hour_12_tweets[:10]):  # Show first 10
            date_str = tweet['createdAt']
            text = tweet.get('text', 'N/A')[:80]
            tweet_id = tweet.get('id', 'N/A')
            print(f"  {i+1}. {date_str} | ID: {tweet_id}")
            print(f"     Text: {text}...")
            print()
    
    # Check for potential JSON file duplicates
    print(f"\n📁 CHECKING FOR POTENTIAL JSON FILE DUPLICATES:")
    print("="*60)
    
    file_sizes = {}
    for file in files:
        file_path = os.path.join(data_dir, file)
        file_size = os.path.getsize(file_path)
        if file_size not in file_sizes:
            file_sizes[file_size] = []
        file_sizes[file_size].append(file)
    
    duplicate_sizes = {size: file_list for size, file_list in file_sizes.items() if len(file_list) > 1}
    
    if duplicate_sizes:
        print(f"🚨 Found {len(duplicate_sizes)} file sizes with multiple files:")
        for size, file_list in duplicate_sizes.items():
            print(f"  Size: {size} bytes - Files: {file_list}")
    else:
        print(f"✅ No duplicate file sizes found")
    
    # Summary
    print(f"\n📋 SUMMARY:")
    print("="*60)
    print(f"Total tweets loaded: {len(all_tweets)}")
    print(f"Unique tweet IDs: {len(set(tweet_ids))}")
    print(f"Duplicate tweet IDs: {len(duplicates)}")
    print(f"Tweets at 12:00: {len(hour_12_tweets)}")
    print(f"Files with same size: {len(duplicate_sizes)}")
    
    if len(duplicates) > 0 or len(duplicate_sizes) > 0:
        print(f"\n⚠️  POTENTIAL ISSUES DETECTED:")
        print(f"  • {len(duplicates)} duplicate tweet IDs")
        print(f"  • {len(duplicate_sizes)} file size duplicates")
        print(f"  • This could explain the suspicious timing patterns")
    else:
        print(f"\n✅ No obvious duplication issues found")
        print(f"  • The 854 tweets at 12:00 might be real")

if __name__ == "__main__":
    check_duplicates()
