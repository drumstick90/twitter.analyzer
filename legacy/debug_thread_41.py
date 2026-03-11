#!/usr/bin/env python3
"""
Script di debug per il thread #41 per capire perché si ferma al tweet 12
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

def debug_thread_41():
    """Debug del thread #41 per capire perché si ferma al tweet 12"""
    
    print("🐛 DEBUG THREAD #41 - ANALISI PASSO PER PASSO")
    print("=" * 60)
    
    # Conversation ID del thread #41
    target_conv_id = "1795898087241568727"
    
    # Carica i tweet del thread #41
    tweets_dir = "NTFabiano_tweets_analysis"
    thread_tweets = []
    
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
                        if isinstance(tweet, dict) and tweet.get('conversationId') == target_conv_id:
                            thread_tweets.append(tweet)
            except Exception as e:
                print(f"❌ Errore caricando {filename}: {e}")
    
    # Filtra solo tweet di NTFabiano
    ntfabiano_tweets = [t for t in thread_tweets if 
                       t.get('author', {}).get('userName', '').lower() == 'ntfabiano']
    
    # Ordina per tempo
    ntfabiano_tweets.sort(key=lambda t: parse_ts(t.get('createdAt') or t.get('created_at')) or datetime.min)
    
    print(f"🔍 Tweet trovati per conversationId: {len(thread_tweets)}")
    print(f"👤 Tweet di NTFabiano: {len(ntfabiano_tweets)}")
    print()
    
    # Debug della logica passo per passo
    print("🧵 DEBUG LOGICA THREAD IDENTIFICATION:")
    print("-" * 40)
    
    current_thread = [ntfabiano_tweets[0]]
    print(f"✅ Tweet 1 (root): {ntfabiano_tweets[0].get('id')} - {ntfabiano_tweets[0].get('text', '')[:50]}...")
    
    # Analizza i primi 13 tweet per capire la struttura completa
    for i in range(1, min(13, len(ntfabiano_tweets))):
        prev_tweet = ntfabiano_tweets[i-1]
        curr_tweet = ntfabiano_tweets[i]
        
        # Calcola gap temporale
        prev_time = parse_ts(prev_tweet.get('createdAt') or prev_tweet.get('created_at'))
        curr_time = parse_ts(curr_tweet.get('createdAt') or curr_tweet.get('created_at'))
        
        if not prev_time or not curr_time:
            print(f"⚠️ Tweet {i+1}: Timestamp non valido")
            continue
        
        time_diff_seconds = (curr_time - prev_time).total_seconds()
        time_diff_minutes = time_diff_seconds / 60
        
        # Verifica se è risposta al precedente
        is_reply_to_prev = curr_tweet.get('inReplyToId') == prev_tweet.get('id')
        
        print(f"\n🔍 Tweet {i+1}: {curr_tweet.get('id')}")
        print(f"   ⏰ Gap: {time_diff_seconds:.0f}s ({time_diff_minutes:.1f} min)")
        print(f"   📝 Testo: {curr_tweet.get('text', '')[:50]}...")
        print(f"   🔗 ReplyTo: {curr_tweet.get('inReplyToId')}")
        print(f"   🎯 Prev ID: {prev_tweet.get('id')}")
        print(f"   ✅ Gap ≤ 2 min: {time_diff_minutes <= 2}")
        print(f"   ✅ Risposta al prev: {is_reply_to_prev}")
        
        # Mostra sempre il tweet, indipendentemente dai criteri
        if time_diff_minutes <= 2 and is_reply_to_prev:
            current_thread.append(curr_tweet)
            print(f"   🧵 INCLUSO nel thread (lunghezza: {len(current_thread)})")
        else:
            print(f"   ❌ NON incluso nel thread")
            if time_diff_minutes > 2:
                print(f"      💡 Motivo: Gap troppo grande ({time_diff_minutes:.1f} min > 2 min)")
            if not is_reply_to_prev:
                print(f"      💡 Motivo: Non è risposta al precedente")
                print(f"      🔍 ReplyTo punta a: {curr_tweet.get('inReplyToId')}")
                print(f"      🎯 Ma dovrebbe puntare a: {prev_tweet.get('id')}")
        
        # Continua sempre per vedere tutti i tweet 1-13
        print(f"      📊 Continua analisi...")
    
    print(f"\n📊 RISULTATO FINALE:")
    print(f"   🧵 Thread identificato: {len(current_thread)} tweet")
    print(f"   📝 Tweet totali disponibili: {len(ntfabiano_tweets)}")
    
    if len(current_thread) < len(ntfabiano_tweets):
        print(f"   ❌ PROBLEMA: Thread si ferma al tweet {len(current_thread)} invece di continuare!")
        print(f"   🔍 Tweet esclusi: {len(ntfabiano_tweets) - len(current_thread)}")
        
        # Mostra i tweet esclusi
        excluded_tweets = [t for t in ntfabiano_tweets if t not in current_thread]
        for i, tweet in enumerate(excluded_tweets[:5]):  # Solo i primi 5
            ts = parse_ts(tweet.get('createdAt') or tweet.get('created_at'))
            ts_str = ts.strftime('%H:%M:%S') if ts else 'N/A'
            print(f"      Tweet {len(current_thread) + i + 1}: [{ts_str}] {tweet.get('text', '')[:50]}...")

if __name__ == "__main__":
    debug_thread_41()
