#!/usr/bin/env python3
"""
Debug finale del thread #41 per capire perché non identifica tutti i 13 tweet
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

def is_valid_thread_tweet_final(tweet: Dict, all_user_tweets: List[Dict], username: str = 'ntfabiano') -> bool:
    """
    Verifica se un tweet fa parte di un thread valido (LOGICA FINALE)
    
    Criteri:
    1. Stesso utente (già verificato nel chiamante)
    2. Risposta a se stesso (inReplyToId punta a suo tweet precedente)
    3. Gap < 30 secondi
    """
    
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

def debug_thread_41_final():
    """Debug finale del thread #41"""
    
    print("🔍 DEBUG FINALE THREAD #41 - VERIFICA 13 TWEET")
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
    
    print(f"🔍 Tweet totali per conversationId: {len(thread_tweets)}")
    print(f"👤 Tweet di NTFabiano: {len(ntfabiano_tweets)}")
    print()
    
    # Analizza ogni tweet con la logica finale
    print("🧵 ANALISI TWEET CON LOGICA FINALE:")
    print("-" * 40)
    
    valid_thread_tweets = []
    
    for i, tweet in enumerate(ntfabiano_tweets):
        ts = parse_ts(tweet.get('createdAt') or tweet.get('created_at'))
        ts_str = ts.strftime('%H:%M:%S') if ts else 'N/A'
        reply_to = tweet.get('inReplyToId') or 'None'
        text = tweet.get('text', '')[:60] + '...' if len(tweet.get('text', '')) > 60 else tweet.get('text', '')
        
        # Applica la logica finale
        is_valid = is_valid_thread_tweet_final(tweet, ntfabiano_tweets)
        
        if is_valid:
            valid_thread_tweets.append(tweet)
            status = "✅ VALIDO"
        else:
            status = "❌ NON VALIDO"
        
        print(f"  {i+1:2d}. [{ts_str}] {status}")
        print(f"      ID: {tweet.get('id')}")
        print(f"      ReplyTo: {reply_to}")
        print(f"      Testo: {text}")
        
        # Se non è valido, mostra il motivo
        if not is_valid:
            reply_to_id = tweet.get('inReplyToId')
            if reply_to_id:
                replied_tweet = next((t for t in ntfabiano_tweets if t.get('id') == reply_to_id), None)
                if replied_tweet:
                    replied_username = replied_tweet.get('author', {}).get('userName', '').lower()
                    if replied_username != 'ntfabiano':
                        print(f"      💡 Motivo: Risponde a terzi ({replied_username})")
                    else:
                        # Verifica gap temporale
                        replied_time = parse_ts(replied_tweet.get('createdAt') or replied_tweet.get('created_at'))
                        if ts and replied_time:
                            gap_seconds = (ts - replied_time).total_seconds()
                            if gap_seconds >= 30:
                                print(f"      💡 Motivo: Gap troppo grande ({gap_seconds:.0f}s >= 30s)")
                            else:
                                print(f"      💡 Motivo: Sconosciuto (gap: {gap_seconds:.0f}s)")
                        else:
                            print(f"      💡 Motivo: Timestamp non valido")
                else:
                    print(f"      💡 Motivo: Tweet risposto non trovato")
            else:
                print(f"      💡 Motivo: Non è una risposta")
        
        print()
    
    print("📊 RISULTATO FINALE:")
    print(f"   🧵 Tweet thread validi: {len(valid_thread_tweets)}")
    print(f"   📝 Tweet totali disponibili: {len(ntfabiano_tweets)}")
    
    if len(valid_thread_tweets) != 13:
        print(f"   ❌ PROBLEMA: Dovrebbero essere 13, ma sono {len(valid_thread_tweets)}!")
        print(f"   🔍 Tweet mancanti: {len(ntfabiano_tweets) - len(valid_thread_tweets)}")
    else:
        print(f"   ✅ PERFETTO: 13 tweet identificati correttamente!")

if __name__ == "__main__":
    debug_thread_41_final()
