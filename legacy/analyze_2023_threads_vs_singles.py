#!/usr/bin/env python3
"""
Analisi Thread vs Post Singoli per @NTFabiano 2023
Esclude retweet, identifica thread, conta e associa likes
"""

import json
import os
import glob
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict

class ThreadAnalyzer2023:
    def __init__(self):
        self.data_dir = "NTFabiano_tweets_analysis"
        self.tweets_2023 = []
        self.threads = []
        self.single_posts = []
        
    def load_2023_data(self):
        """Carica solo i dati del 2023"""
        print("🔄 Caricamento dati 2023...")
        
        # Cerca tutti i file 2023
        pattern = os.path.join(self.data_dir, "tweets_NTFabiano_2023_page_*.json")
        files = glob.glob(pattern)
        
        if not files:
            print("❌ Nessun file 2023 trovato!")
            return False
            
        print(f"📁 Trovati {len(files)} file 2023")
        
        for file_path in sorted(files):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                if 'tweets' in data:
                    tweets = data['tweets']
                elif 'data' in data and 'tweets' in data['data']:
                    tweets = data['data']['tweets']
                else:
                    tweets = data
                    
                # Filtra solo tweet originali (esclude retweet)
                original_tweets = []
                for tweet in tweets:
                    # Controlla se è un retweet
                    if isinstance(tweet, dict):
                        # Esclude retweet basandosi su vari indicatori
                        is_retweet = (
                            tweet.get('retweetedTweet') or 
                            tweet.get('retweeted') or
                            tweet.get('source', '').lower().find('retweet') != -1 or
                            tweet.get('text', '').startswith('RT @') or
                            tweet.get('text', '').startswith('RT:')
                        )
                        
                        if not is_retweet:
                            original_tweets.append(tweet)
                
                self.tweets_2023.extend(original_tweets)
                print(f"✅ {file_path}: {len(original_tweets)} tweet originali")
                
            except Exception as e:
                print(f"❌ Errore nel file {file_path}: {e}")
                
        print(f"📊 Totale tweet 2023 (esclusi retweet): {len(self.tweets_2023)}")
        return True
    
    def identify_threads(self, max_gap_minutes=10):
        """Identifica thread basandosi su timing e contenuto"""
        print("🧵 Identificazione thread...")
        
        if not self.tweets_2023:
            print("❌ Nessun tweet da analizzare!")
            return
            
        # Ordina per data
        sorted_tweets = sorted(self.tweets_2023, key=lambda x: x.get('createdAt', ''))
        
        current_thread = []
        all_threads = []
        
        for i, tweet in enumerate(sorted_tweets):
            if not tweet.get('createdAt'):
                continue
                
            # Parsing del formato data Twitter: "Mon Dec 18 00:38:05 +0000 2023"
            try:
                tweet_time = datetime.strptime(tweet['createdAt'], '%a %b %d %H:%M:%S %z %Y')
            except:
                try:
                    # Fallback per altri formati
                    tweet_time = datetime.strptime(tweet['createdAt'], '%Y-%m-%dT%H:%M:%S.%fZ')
                except:
                    try:
                        tweet_time = datetime.strptime(tweet['createdAt'], '%Y-%m-%dT%H:%M:%S.%f+00:00')
                    except:
                        print(f"⚠️ Impossibile parsare data: {tweet['createdAt']}")
                        continue
            
            if not current_thread:
                current_thread = [tweet]
                continue
                
            # Controlla se questo tweet appartiene al thread corrente
            try:
                last_tweet_time = datetime.strptime(current_thread[-1]['createdAt'], '%a %b %d %H:%M:%S %z %Y')
            except:
                try:
                    last_tweet_time = datetime.strptime(current_thread[-1]['createdAt'], '%Y-%m-%dT%H:%M:%S.%fZ')
                except:
                    try:
                        last_tweet_time = datetime.strptime(current_thread[-1]['createdAt'], '%Y-%m-%dT%H:%M:%S.%f+00:00')
                    except:
                        print(f"⚠️ Impossibile parsare data ultimo tweet: {current_thread[-1]['createdAt']}")
                        continue
            
            time_diff = (tweet_time - last_tweet_time).total_seconds() / 60
            
            # Controlla indicatori di thread
            is_thread_continuation = (
                time_diff <= max_gap_minutes or
                self.has_thread_indicators(tweet) or
                self.is_reply_to_thread(tweet, current_thread)
            )
            
            if is_thread_continuation:
                current_thread.append(tweet)
            else:
                # Thread terminato, salvalo
                if len(current_thread) > 1:
                    all_threads.append(current_thread)
                elif len(current_thread) == 1:
                    self.single_posts.append(current_thread[0])
                
                # Inizia nuovo thread
                current_thread = [tweet]
        
        # Gestisci l'ultimo thread
        if len(current_thread) > 1:
            all_threads.append(current_thread)
        elif len(current_thread) == 1:
            self.single_posts.append(current_thread[0])
        
        self.threads = all_threads
        
        print(f"🧵 Thread identificati: {len(self.threads)}")
        print(f"📝 Post singoli: {len(self.single_posts)}")
        
        # Mostra statistiche thread
        if self.threads:
            thread_lengths = [len(thread) for thread in self.threads]
            print(f"📏 Lunghezza thread: min={min(thread_lengths)}, max={max(thread_lengths)}, media={sum(thread_lengths)/len(thread_lengths):.1f}")
    
    def has_thread_indicators(self, tweet):
        """Controlla se il tweet ha indicatori di thread"""
        text = tweet.get('text', '').lower()
        thread_indicators = [
            '🧵', 'thread', '1/', '2/', '3/', '4/', '5/', '6/', '7/', '8/', '9/', '10/',
            'continua', 'segue', 'parte', 'capitolo', 'punto', 'step'
        ]
        
        return any(indicator in text for indicator in thread_indicators)
    
    def is_reply_to_thread(self, tweet, current_thread):
        """Controlla se il tweet è una risposta al thread corrente"""
        if not current_thread:
            return False
            
        # Controlla se è una risposta al primo tweet del thread
        first_tweet_id = current_thread[0].get('id')
        if tweet.get('inReplyToTweetId') == first_tweet_id:
            return True
            
        # Controlla se è una risposta a qualsiasi tweet del thread
        thread_ids = [t.get('id') for t in current_thread]
        return tweet.get('inReplyToTweetId') in thread_ids
    
    def analyze_engagement(self):
        """Analizza engagement per thread vs post singoli"""
        print("📊 Analisi engagement...")
        
        # Analisi thread
        thread_stats = []
        for i, thread in enumerate(self.threads):
            total_likes = sum(t.get('likeCount', 0) for t in thread)
            total_retweets = sum(t.get('retweetCount', 0) for t in thread)
            total_replies = sum(t.get('replyCount', 0) for t in thread)
            total_engagement = total_likes + total_retweets + total_replies
            
            thread_stats.append({
                'thread_id': i + 1,
                'tweet_count': len(thread),
                'total_likes': total_likes,
                'total_retweets': total_retweets,
                'total_replies': total_replies,
                'total_engagement': total_engagement,
                'avg_likes_per_tweet': total_likes / len(thread),
                'avg_engagement_per_tweet': total_engagement / len(thread),
                'first_tweet_time': thread[0].get('createdAt'),
                'last_tweet_time': thread[-1].get('createdAt')
            })
        
        # Analisi post singoli
        single_post_stats = []
        for tweet in self.single_posts:
            single_post_stats.append({
                'tweet_id': tweet.get('id'),
                'likes': tweet.get('likeCount', 0),
                'retweets': tweet.get('retweetCount', 0),
                'replies': tweet.get('replyCount', 0),
                'total_engagement': tweet.get('likeCount', 0) + tweet.get('retweetCount', 0) + tweet.get('replyCount', 0),
                'created_at': tweet.get('createdAt'),
                'text': tweet.get('text', '')[:100] + '...' if len(tweet.get('text', '')) > 100 else tweet.get('text', '')
            })
        
        # Statistiche comparative
        if thread_stats:
            avg_thread_likes = sum(t['total_likes'] for t in thread_stats) / len(thread_stats)
            avg_thread_engagement = sum(t['total_engagement'] for t in thread_stats) / len(thread_stats)
            print(f"🧵 Thread - Media likes: {avg_thread_likes:.0f}, Media engagement: {avg_thread_engagement:.0f}")
        
        if single_post_stats:
            avg_single_likes = sum(t['likes'] for t in single_post_stats) / len(single_post_stats)
            avg_single_engagement = sum(t['total_engagement'] for t in single_post_stats) / len(single_post_stats)
            print(f"📝 Post singoli - Media likes: {avg_single_likes:.0f}, Media engagement: {avg_single_engagement:.0f}")
        
        # Salva risultati
        self.save_analysis_results(thread_stats, single_post_stats)
        
        return thread_stats, single_post_stats
    
    def save_analysis_results(self, thread_stats, single_post_stats):
        """Salva i risultati dell'analisi"""
        # Salva statistiche thread
        if thread_stats:
            df_threads = pd.DataFrame(thread_stats)
            df_threads.to_csv('thread_analysis_2023.csv', index=False)
            print(f"💾 Statistiche thread salvate in thread_analysis_2023.csv")
        
        # Salva statistiche post singoli
        if single_post_stats:
            df_singles = pd.DataFrame(single_post_stats)
            df_singles.to_csv('single_posts_2023.csv', index=False)
            print(f"💾 Statistiche post singoli salvate in single_posts_2023.csv")
        
        # Salva report JSON
        report = {
            'analysis_date': datetime.now().isoformat(),
            'year': 2023,
            'total_original_tweets': len(self.tweets_2023),
            'threads_count': len(self.threads),
            'single_posts_count': len(self.single_posts),
            'summary': {
                'threads': {
                    'count': len(self.threads),
                    'total_tweets': sum(len(t) for t in self.threads),
                    'avg_likes_per_thread': sum(t['total_likes'] for t in thread_stats) / len(thread_stats) if thread_stats else 0,
                    'avg_engagement_per_thread': sum(t['total_engagement'] for t in thread_stats) / len(thread_stats) if thread_stats else 0
                },
                'single_posts': {
                    'count': len(self.single_posts),
                    'avg_likes': sum(t['likes'] for t in single_post_stats) / len(single_post_stats) if single_post_stats else 0,
                    'avg_engagement': sum(t['total_engagement'] for t in single_post_stats) / len(single_post_stats) if single_post_stats else 0
                }
            }
        }
        
        with open('thread_vs_singles_2023_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Report completo salvato in thread_vs_singles_2023_report.json")
    
    def create_visualizations(self, thread_stats, single_post_stats):
        """Crea visualizzazioni comparative"""
        print("📈 Creazione visualizzazioni...")
        
        plt.style.use('default')
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('@NTFabiano 2023: Thread vs Post Singoli - Analisi Engagement', fontsize=16, fontweight='bold')
        
        # 1. Confronto likes thread vs singoli
        if thread_stats and single_post_stats:
            thread_likes = [t['total_likes'] for t in thread_stats]
            single_likes = [t['likes'] for t in single_post_stats]
            
            ax1 = axes[0, 0]
            ax1.boxplot([thread_likes, single_likes], labels=['Thread', 'Post Singoli'])
            ax1.set_title('Distribuzione Likes: Thread vs Post Singoli')
            ax1.set_ylabel('Numero di Likes')
            ax1.grid(True, alpha=0.3)
        
        # 2. Engagement totale per thread
        if thread_stats:
            ax2 = axes[0, 1]
            thread_ids = [f"T{i+1}" for i in range(len(thread_stats))]
            engagement_values = [t['total_engagement'] for t in thread_stats]
            
            bars = ax2.bar(thread_ids, engagement_values, color='skyblue', alpha=0.7)
            ax2.set_title('Engagement Totale per Thread')
            ax2.set_ylabel('Engagement Totale (Likes + RT + Replies)')
            ax2.tick_params(axis='x', rotation=45)
            ax2.grid(True, alpha=0.3)
            
            # Aggiungi valori sopra le barre
            for bar, value in zip(bars, engagement_values):
                if value > 0:
                    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(engagement_values)*0.01, 
                            f'{value:.0f}', ha='center', va='bottom', fontsize=8)
        
        # 3. Likes vs Lunghezza Thread
        if thread_stats:
            ax3 = axes[1, 0]
            lengths = [t['tweet_count'] for t in thread_stats]
            likes = [t['total_likes'] for t in thread_stats]
            
            ax3.scatter(lengths, likes, alpha=0.7, s=100, color='orange')
            ax3.set_xlabel('Numero di Tweet nel Thread')
            ax3.set_ylabel('Likes Totali del Thread')
            ax3.set_title('Likes vs Lunghezza Thread')
            ax3.grid(True, alpha=0.3)
        
        # 4. Distribuzione engagement post singoli
        if single_post_stats:
            ax4 = axes[1, 1]
            engagement_values = [t['total_engagement'] for t in single_post_stats]
            
            ax4.hist(engagement_values, bins=20, alpha=0.7, color='lightgreen', edgecolor='black')
            ax4.set_xlabel('Engagement Totale')
            ax4.set_ylabel('Frequenza')
            ax4.set_title('Distribuzione Engagement Post Singoli')
            ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('thread_vs_singles_2023_analysis.png', dpi=300, bbox_inches='tight')
        print(f"📊 Visualizzazioni salvate in thread_vs_singles_2023_analysis.png")
        plt.show()
    
    def run_analysis(self):
        """Esegue l'analisi completa"""
        print("🚀 Avvio analisi Thread vs Post Singoli 2023")
        print("=" * 60)
        
        # 1. Carica dati
        if not self.load_2023_data():
            return
        
        # 2. Identifica thread
        self.identify_threads()
        
        # 3. Analizza engagement
        thread_stats, single_post_stats = self.analyze_engagement()
        
        # 4. Crea visualizzazioni
        self.create_visualizations(thread_stats, single_post_stats)
        
        # 5. Riepilogo finale
        print("\n" + "=" * 60)
        print("📋 RIEPILOGO FINALE 2023")
        print("=" * 60)
        print(f"🧵 Thread identificati: {len(self.threads)}")
        print(f"📝 Post singoli: {len(self.single_posts)}")
        print(f"📊 Tweet totali analizzati: {len(self.tweets_2023)}")
        
        if thread_stats and single_post_stats:
            avg_thread_likes = sum(t['total_likes'] for t in thread_stats) / len(thread_stats)
            avg_single_likes = sum(t['likes'] for t in single_post_stats) / len(single_post_stats)
            print(f"🔥 Media likes per thread: {avg_thread_likes:.0f}")
            print(f"🔥 Media likes per post singolo: {avg_single_likes:.0f}")
            
            if avg_thread_likes > avg_single_likes:
                print(f"✅ I thread performano meglio dei post singoli!")
            else:
                print(f"📝 I post singoli performano meglio dei thread")

if __name__ == "__main__":
    analyzer = ThreadAnalyzer2023()
    analyzer.run_analysis()
