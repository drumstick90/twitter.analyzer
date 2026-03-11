#!/usr/bin/env python3
"""
Script to show suspicious rapid-fire tweets with detailed timing analysis.
"""

import json
import os
from datetime import datetime
from collections import defaultdict

def show_suspicious_tweets():
    """Show tweets posted in rapid succession with detailed analysis."""
    
    data_dir = "NTFabiano_tweets_analysis"
    
    print("🔍 ANALIZZANDO TWEET SOSPETTI CON TIMING RAPIDO...")
    print("="*80)
    
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
    
    # Parse dates and find rapid-fire patterns
    rapid_fire_groups = defaultdict(list)
    
    for tweet in all_tweets:
        if 'createdAt' in tweet:
            try:
                date_str = tweet['createdAt']
                parsed_date = datetime.strptime(date_str, "%a %b %d %H:%M:%S %z %Y")
                
                # Create a key for tweets posted within the same minute
                minute_key = parsed_date.strftime('%Y-%m-%d %H:%M')
                
                tweet_info = {
                    'id': tweet.get('id', 'N/A'),
                    'created_at': parsed_date,
                    'text': tweet.get('text', 'N/A'),
                    'likes': tweet.get('likeCount', 0),
                    'retweets': tweet.get('retweetCount', 0),
                    'replies': tweet.get('replyCount', 0),
                    'source': tweet.get('source', 'N/A'),
                    'is_reply': tweet.get('isReply', False)
                }
                
                rapid_fire_groups[minute_key].append(tweet_info)
                
            except Exception as e:
                continue
    
    # Find minutes with multiple tweets
    suspicious_minutes = {minute: tweets for minute, tweets in rapid_fire_groups.items() if len(tweets) > 1}
    
    print(f"\n🚨 TROVATI {len(suspicious_minutes)} MINUTI CON MULTIPLI TWEET:")
    print("="*80)
    
    # Sort by number of tweets (most suspicious first)
    sorted_minutes = sorted(suspicious_minutes.items(), key=lambda x: len(x[1]), reverse=True)
    
    # Show top 20 most suspicious minutes
    for i, (minute, tweets) in enumerate(sorted_minutes[:20]):
        print(f"\n🔥 MINUTO {i+1}: {minute} - {len(tweets)} TWEET IN 1 MINUTO!")
        print("-" * 60)
        
        # Sort tweets by second within the minute
        tweets.sort(key=lambda x: x['created_at'].second)
        
        for j, tweet in enumerate(tweets):
            time_str = tweet['created_at'].strftime('%H:%M:%S')
            text_preview = tweet['text'][:100] + "..." if len(tweet['text']) > 100 else tweet['text']
            
            print(f"  {j+1:2d}. {time_str} | ❤️ {tweet['likes']:4d} | 🔄 {tweet['retweets']:3d} | 💬 {tweet['replies']:2d}")
            print(f"      ID: {tweet['id']}")
            print(f"      Text: {text_preview}")
            print(f"      Source: {tweet['source']} | Reply: {tweet['is_reply']}")
            print()
    
    # Show statistics
    print(f"\n📊 STATISTICHE PATTERN SOSPETTI:")
    print("="*80)
    
    total_suspicious_tweets = sum(len(tweets) for tweets in suspicious_minutes.values())
    max_tweets_per_minute = max(len(tweets) for tweets in suspicious_minutes.values())
    
    print(f"📈 Tweet totali in minuti sospetti: {total_suspicious_tweets}")
    print(f"🔥 Massimo tweet per minuto: {max_tweets_per_minute}")
    print(f"⏰ Minuti con pattern sospetti: {len(suspicious_minutes)}")
    
    # Analyze specific patterns
    print(f"\n🔍 ANALISI PATTERN SPECIFICI:")
    print("="*80)
    
    # Find the most extreme case
    most_extreme = max(suspicious_minutes.items(), key=lambda x: len(x[1]))
    extreme_minute, extreme_tweets = most_extreme
    
    print(f"🚨 CASO PIÙ ESTREMO: {extreme_minute} - {len(extreme_tweets)} TWEET!")
    print(f"📅 Data: {extreme_tweets[0]['created_at'].strftime('%d %B %Y')}")
    print(f"⏰ Ora: {extreme_tweets[0]['created_at'].strftime('%H:%M')}")
    
    # Show timing between tweets
    print(f"\n⏱️  INTERVALLI TRA TWEET:")
    for i in range(len(extreme_tweets) - 1):
        current = extreme_tweets[i]['created_at']
        next_tweet = extreme_tweets[i + 1]['created_at']
        time_diff = (next_tweet - current).total_seconds()
        
        print(f"  Tweet {i+1} → Tweet {i+2}: {time_diff:.1f} secondi")
    
    # Check if this is a thread
    print(f"\n🧵 È UN THREAD?")
    reply_count = sum(1 for tweet in extreme_tweets if tweet['is_reply'])
    print(f"  Tweet reply: {reply_count}/{len(extreme_tweets)}")
    
    if reply_count > 0:
        print(f"  ⚠️  Potrebbe essere un thread coordinato!")
    else:
        print(f"  📝 Tutti tweet originali - pattern molto sospetto!")
    
    # Show content analysis
    print(f"\n📝 ANALISI CONTENUTO:")
    print("="*80)
    
    # Check for common patterns in text
    texts = [tweet['text'].lower() for tweet in extreme_tweets]
    
    # Look for common words/phrases
    all_words = []
    for text in texts:
        words = text.split()
        all_words.extend(words)
    
    from collections import Counter
    word_counts = Counter(all_words)
    common_words = word_counts.most_common(10)
    
    print(f"🔤 Parole più comuni in questi tweet:")
    for word, count in common_words:
        if len(word) > 3:  # Skip short words
            print(f"  '{word}': {count} volte")
    
    # Check for links
    link_count = sum(1 for text in texts if 'http' in text or 't.co' in text)
    print(f"\n🔗 Tweet con link: {link_count}/{len(extreme_tweets)}")
    
    if link_count > len(extreme_tweets) * 0.8:  # 80% have links
        print(f"  📊 Alta percentuale di link - potrebbe essere un thread di condivisione!")
    
    print(f"\n💡 CONCLUSIONE:")
    print("="*80)
    
    if max_tweets_per_minute > 10:
        print(f"🚨 COMPORTAMENTO MOLTO SOSPETTO: {max_tweets_per_minute} tweet in 1 minuto!")
        print(f"   • Probabilmente automatizzato")
        print(f"   • Potrebbe essere un thread coordinato")
        print(f"   • Timing troppo perfetto per essere umano")
    elif max_tweets_per_minute > 5:
        print(f"⚠️  COMPORTAMENTO SOSPETTO: {max_tweets_per_minute} tweet in 1 minuto")
        print(f"   • Potrebbe essere parzialmente automatizzato")
        print(f"   • Thread coordinato o scheduling")
    else:
        print(f"✅ COMPORTAMENTO NORMALE: massimo {max_tweets_per_minute} tweet per minuto")

if __name__ == "__main__":
    show_suspicious_tweets()
