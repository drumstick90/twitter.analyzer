#!/usr/bin/env python3
"""
Script per analizzare e stampare il contenuto dettagliato dei thread identificati
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any

def parse_ts(ts_str: str) -> datetime:
    """Parsa timestamp in vari formati"""
    if not ts_str:
        return None
    
    formats = [
        '%Y-%m-%dT%H:%M:%S.%fZ',
        '%Y-%m-%dT%H:%M:%S.%f+00:00',
        '%Y-%m-%dT%H:%M:%S+00:00',
        '%a %b %d %H:%M:%S %z %Y'
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(ts_str, fmt)
        except:
            continue
    
    print(f"⚠️ Impossibile parsare timestamp: {ts_str}")
    return None

def analyze_threads_detailed():
    """Analizza e stampa i dettagli dei thread identificati"""
    
    print("🔍 ANALISI DETTAGLIATA DEI THREAD 2024 IDENTIFICATI")
    print("=" * 60)
    
    # Carica i dati dei thread
    thread_data = []
    with open('thread_analysis.csv', 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines[1:]:  # Skip header
            parts = line.strip().split(',')
            if len(parts) >= 15:
                thread_data.append({
                    'thread_id': parts[0],
                    'conversation_id': parts[1],
                    'tweet_count': int(parts[2]),
                    'total_likes': int(parts[3]),
                    'total_retweets': int(parts[4]),
                    'total_replies': int(parts[5]),
                    'total_engagement': int(parts[6]),
                    'first_tweet_time': parts[13],
                    'last_tweet_time': parts[14],
                    'root_text': parts[15] if len(parts) > 15 else ''
                })
    
    # Carica i tweet originali per analisi dettagliata
    tweets_dir = "NTFabiano_tweets_analysis"
    all_tweets = []
    
    for filename in os.listdir(tweets_dir):
        if filename.startswith('tweets_NTFabiano_2024_') and filename.endswith('.json'):
            filepath = os.path.join(tweets_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        tweets = data
                    elif isinstance(data, dict):
                        tweets = data.get('tweets') or data.get('data', {}).get('tweets') or []
                    else:
                        tweets = []
                    
                    for tweet in tweets:
                        if isinstance(tweet, dict) and tweet.get('conversationId'):
                            all_tweets.append(tweet)
            except Exception as e:
                print(f"❌ Errore caricando {filename}: {e}")
    
    print(f"📊 Tweet totali caricati: {len(all_tweets)}")
    print()
    
    # Analizza ogni thread
    for thread_info in thread_data:
        conv_id = thread_info['conversation_id']
        print(f"🧵 THREAD #{thread_info['thread_id']}")
        print(f"🆔 Conversation ID: {conv_id}")
        print(f"📅 Periodo: {thread_info['first_tweet_time']} → {thread_info['last_tweet_time']}")
        print(f"📊 Engagement: {thread_info['total_likes']} likes, {thread_info['total_retweets']} RT, {thread_info['total_replies']} replies")
        print(f"📝 Testo root: {thread_info['root_text'][:100]}...")
        print("-" * 40)
        
        # Trova i tweet di questo thread
        thread_tweets = [t for t in all_tweets if t.get('conversationId') == conv_id]
        
        # Filtra solo tweet di NTFabiano
        ntfabiano_tweets = [t for t in thread_tweets if 
                           t.get('author', {}).get('userName', '').lower() == 'ntfabiano']
        
        # Ordina per tempo
        ntfabiano_tweets.sort(key=lambda t: parse_ts(t.get('createdAt') or t.get('created_at')) or datetime.min)
        
        print(f"🔍 Tweet trovati per conversationId: {len(thread_tweets)}")
        print(f"👤 Tweet di NTFabiano: {len(ntfabiano_tweets)}")
        print()
        
        # Analizza ogni tweet del thread
        for i, tweet in enumerate(ntfabiano_tweets):
            ts = parse_ts(tweet.get('createdAt') or tweet.get('created_at'))
            ts_str = ts.strftime('%Y-%m-%d %H:%M:%S') if ts else 'N/A'
            
            # Calcola gap dal tweet precedente
            if i > 0:
                prev_ts = parse_ts(ntfabiano_tweets[i-1].get('createdAt') or ntfabiano_tweets[i-1].get('created_at'))
                if prev_ts and ts:
                    gap_seconds = (ts - prev_ts).total_seconds()
                    gap_str = f" (+{gap_seconds:.0f}s)"
                else:
                    gap_str = " (gap N/A)"
            else:
                gap_str = " (root)"
            
            # Verifica se è risposta al precedente
            if i > 0:
                prev_id = ntfabiano_tweets[i-1].get('id')
                is_reply = tweet.get('inReplyToId') == prev_id
                reply_str = " ✅" if is_reply else " ❌"
            else:
                reply_str = " (root)"
            
            text = tweet.get('text', '')[:80] + '...' if len(tweet.get('text', '')) > 80 else tweet.get('text', '')
            
            print(f"  {i+1:2d}. [{ts_str}]{gap_str}{reply_str}")
            print(f"      ID: {tweet.get('id')}")
            print(f"      ReplyTo: {tweet.get('inReplyToId') or 'None'}")
            print(f"      Likes: {tweet.get('likeCount', 0)} | RT: {tweet.get('retweetCount', 0)} | Replies: {tweet.get('replyCount', 0)}")
            print(f"      Testo: {text}")
            print()
        
        print("=" * 60)
        print()

if __name__ == "__main__":
    analyze_threads_detailed()
