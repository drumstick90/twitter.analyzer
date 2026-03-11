#!/usr/bin/env python3
"""
Script di test per la nuova logica dei thread:
1. Stesso utente
2. Risposta a se stesso  
3. Gap < 30 secondi
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

def is_valid_thread_tweet(tweet: Dict, all_user_tweets: List[Dict], username: str = 'ntfabiano') -> bool:
    """
    Verifica se un tweet fa parte di un thread valido
    
    Criteri:
    1. Stesso utente
    2. Risposta a se stesso (inReplyToId punta a suo tweet precedente)
    3. Gap < 30 secondi
    """
    
    # 1. Stesso utente (già verificato nel chiamante)
    
    # 2. Risposta a se stesso
    reply_to_id = tweet.get('inReplyToId')
    if not reply_to_id:
        return False  # Non è una risposta
    
    # Trova il tweet a cui risponde
    replied_tweet = next((t for t in all_user_tweets if t.get('id') == reply_to_id), None)
    if not replied_tweet:
        return False  # Tweet non trovato
    
    # Verifica che sia dello stesso utente
    replied_username = replied_tweet.get('author', {}).get('userName', '').lower()
    if replied_username != username.lower():
        return False  # Risponde a terzi
    
    # 3. Gap < 30 secondi
    tweet_time = parse_ts(tweet.get('createdAt') or tweet.get('created_at'))
    replied_time = parse_ts(replied_tweet.get('createdAt') or replied_tweet.get('created_at'))
    
    if not tweet_time or not replied_time:
        return False
    
    gap_seconds = (tweet_time - replied_time).total_seconds()
    return gap_seconds < 30  # Gap < 30 secondi

def test_new_thread_logic():
    """Testa la nuova logica sui thread del 2024"""
    
    print("🧪 TEST NUOVA LOGICA THREAD")
    print("=" * 50)
    print("Criteri: stesso utente + risposta a se stesso + gap < 30s")
    print()
    
    # Carica tutti i tweet del 2024
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
    
    # Raggruppa per conversationId
    by_conv = {}
    for tweet in all_tweets:
        conv_id = tweet.get('conversationId')
        if conv_id:
            by_conv.setdefault(conv_id, []).append(tweet)
    
    print(f"🔍 Conversation trovate: {len(by_conv)}")
    print()
    
    # Testa la nuova logica su alcuni thread
    test_threads = list(by_conv.items())[:5]  # Primi 5 thread
    
    for conv_id, group in test_threads:
        # Filtra solo tweet di NTFabiano
        ntfabiano_tweets = [t for t in group if 
                           t.get('author', {}).get('userName', '').lower() == 'ntfabiano']
        
        if len(ntfabiano_tweets) < 2:
            continue
        
        print(f"🧵 THREAD: {conv_id}")
        print(f"   📝 Tweet totali: {len(group)}")
        print(f"   👤 Tweet NTFabiano: {len(ntfabiano_tweets)}")
        
        # Ordina per tempo
        ntfabiano_tweets.sort(key=lambda t: parse_ts(t.get('createdAt') or t.get('created_at')) or datetime.min)
        
        # Applica la nuova logica
        valid_thread_tweets = []
        for tweet in ntfabiano_tweets:
            if is_valid_thread_tweet(tweet, ntfabiano_tweets):
                valid_thread_tweets.append(tweet)
        
        print(f"   ✅ Tweet thread validi: {len(valid_thread_tweets)}")
        
        # Mostra dettagli dei primi tweet
        for i, tweet in enumerate(valid_thread_tweets[:3]):
            ts = parse_ts(tweet.get('createdAt') or tweet.get('created_at'))
            ts_str = ts.strftime('%H:%M:%S') if ts else 'N/A'
            reply_to = tweet.get('inReplyToId') or 'None'
            text = tweet.get('text', '')[:50] + '...' if len(tweet.get('text', '')) > 50 else tweet.get('text', '')
            
            print(f"      {i+1}. [{ts_str}] ReplyTo: {reply_to} | {text}")
        
        print()
    
    # Test specifico sul thread #41
    print("🎯 TEST SPECIFICO THREAD #41:")
    print("-" * 30)
    
    target_conv_id = "1795898087241568727"
    if target_conv_id in by_conv:
        thread_41 = by_conv[target_conv_id]
        ntfabiano_41 = [t for t in thread_41 if 
                        t.get('author', {}).get('userName', '').lower() == 'ntfabiano']
        
        print(f"Tweet totali: {len(thread_41)}")
        print(f"Tweet NTFabiano: {len(ntfabiano_41)}")
        
        # Ordina per tempo
        ntfabiano_41.sort(key=lambda t: parse_ts(t.get('createdAt') or t.get('created_at')) or datetime.min)
        
        # Applica nuova logica
        valid_41 = []
        for tweet in ntfabiano_41:
            if is_valid_thread_tweet(tweet, ntfabiano_41):
                valid_41.append(tweet)
        
        print(f"Tweet thread validi: {len(valid_41)}")
        
        # Mostra tutti i tweet validi
        for i, tweet in enumerate(valid_41):
            ts = parse_ts(tweet.get('createdAt') or tweet.get('created_at'))
            ts_str = ts.strftime('%H:%M:%S') if ts else 'N/A'
            reply_to = tweet.get('inReplyToId') or 'None'
            text = tweet.get('text', '')[:60] + '...' if len(tweet.get('text', '')) > 60 else tweet.get('text', '')
            
            print(f"  {i+1:2d}. [{ts_str}] ReplyTo: {reply_to} | {text}")

if __name__ == "__main__":
    test_new_thread_logic()
