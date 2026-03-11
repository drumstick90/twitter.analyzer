#!/usr/bin/env python3
"""
Script per stampare tutti i tweet di una data specifica.
"""

import json
import os
from datetime import datetime

def print_tweets_for_date(username, target_date):
    """
    Stampa tutti i tweet di una data specifica.
    """
    print(f"🔍 CERCO TWEET DI @{username} PER {target_date}")
    print("=" * 60)
    
    # Directory dei tweet
    tweets_dir = f"{username}_tweets_analysis"
    
    if not os.path.exists(tweets_dir):
        print(f"❌ Directory {tweets_dir} non trovata!")
        return
    
    all_tweets = []
    
    # Carica tutti i file JSON
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
                print(f"⚠️ Errore caricando {filename}: {e}")
    
    print(f"📊 Tweet totali caricati: {len(all_tweets)}")
    
    # Filtra per data
    target_tweets = []
    for tweet in all_tweets:
        # Prova diversi formati di timestamp
        timestamp = None
        for field in ['createdAt', 'created_at', 'date']:
            if field in tweet and tweet[field]:
                try:
                    # Prova formato Twitter: "Sun Aug 24 19:57:28 +0000 2025"
                    if '+' in tweet[field] and len(tweet[field].split()) >= 6:
                        timestamp = datetime.strptime(tweet[field], '%a %b %d %H:%M:%S %z %Y')
                    else:
                        # Prova formato ISO
                        timestamp = datetime.fromisoformat(tweet[field].replace('Z', '+00:00'))
                    break
                except:
                    continue
        
        if timestamp and timestamp.strftime('%Y-%m-%d') == target_date:
            target_tweets.append((timestamp, tweet))
    
    # Ordina per timestamp
    target_tweets.sort(key=lambda x: x[0])
    
    print(f"🎯 Tweet trovati per {target_date}: {len(target_tweets)}")
    print("=" * 60)
    
    if not target_tweets:
        print("❌ Nessun tweet trovato per questa data!")
        return
    
    # Stampa i tweet
    for i, (timestamp, tweet) in enumerate(target_tweets, 1):
        print(f"\n🧵 TWEET #{i}")
        print(f"⏰ {timestamp.strftime('%H:%M:%S')}")
        print(f"🆔 {tweet.get('id', 'N/A')}")
        
        # Testo del tweet
        text = tweet.get('text', tweet.get('fullText', 'Testo non disponibile'))
        print(f"📝 {text}")
        
        # Engagement
        likes = tweet.get('likeCount', tweet.get('favoriteCount', 0))
        retweets = tweet.get('retweetCount', 0)
        replies = tweet.get('replyCount', 0)
        
        if likes > 0 or retweets > 0 or replies > 0:
            print(f"📊 ❤️ {likes} | 🔄 {retweets} | 💬 {replies}")
        
        print("-" * 40)
    
    print(f"\n🎉 TOTALE: {len(target_tweets)} tweet per {target_date}")

if __name__ == "__main__":
    username = "apralky"
    target_date = "2025-06-15"
    
    print_tweets_for_date(username, target_date)
