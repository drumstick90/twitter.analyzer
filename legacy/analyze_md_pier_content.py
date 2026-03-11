#!/usr/bin/env python3
"""
Script per analizzare i tweet di @md_pier anno per anno e identificare contenuti inappropriati.
Analizza il testo dei tweet per parole chiave e pattern sospetti.

USAGE:
    python3.11 analyze_md_pier_content.py
"""

import pandas as pd
import json
import os
import re
from datetime import datetime
import argparse

class MDPierContentAnalyzer:
    """
    Classe per analizzare il contenuto dei tweet di @md_pier.
    """
    
    def __init__(self):
        self.md_pier_dir = "md_pier_tweets_analysis"
        self.output_filename = "md_pier_inappropriate_content_analysis.csv"
        
        # Validazioni
        if not os.path.exists(self.md_pier_dir):
            raise FileNotFoundError(f"Directory {self.md_pier_dir} non trovata!")
        
        print(f"🔍 ANALISI CONTENUTO @md_pier")
        print(f"📁 Directory: {self.md_pier_dir}")
        print(f"📁 File output: {self.output_filename}")
        print("=" * 70)
        
        # Parole chiave per contenuti inappropriati
        self.inappropriate_keywords = [
            # Linguaggio offensivo
            'merda', 'cazzo', 'stronzo', 'bastardo', 'puttana', 'troia',
            'vaffanculo', 'fanculo', 'coglione', 'idiota', 'cretino',
            'imbecille', 'stupido', 'cretino', 'scemo', 'cretino',
            
            # Contenuti sessuali espliciti
            'porno', 'pornografia', 'sesso', 'fuck', 'shit', 'bitch',
            'dick', 'pussy', 'cock', 'vagina', 'penis', 'ass',
            
            # Violenza
            'uccidere', 'ammazzare', 'sparare', 'coltello', 'pistola',
            'bomba', 'esplosivo', 'terrorismo', 'violenza', 'aggressione',
            
            # Discriminazione
            'razzista', 'nazi', 'hitler', 'fascista', 'omofobo',
            'antisemita', 'islamofobo', 'xenofobo', 'misogino',
            
            # Droghe illegali
            'cocaina', 'eroina', 'metanfetamina', 'lsd', 'ecstasy',
            'marijuana', 'cannabis', 'hashish', 'droga', 'spaccio',
            
            # Minacce
            'minaccia', 'ricatto', 'estorsione', 'vendetta', 'vendicare',
            'distruggere', 'rovinare', 'danneggiare', 'attaccare',
            
            # Contenuti illegali
            'hacker', 'pirateria', 'download illegale', 'contrabbando',
            'evasione fiscale', 'corruzione', 'tangente', 'bustarella'
        ]
        
        # Pattern regex per contenuti sospetti
        self.suspicious_patterns = [
            r'\b\w*[fF][uU][cC][kK]\w*\b',  # Parole con "fuck"
            r'\b\w*[sS][hH][iI][tT]\w*\b',  # Parole con "shit"
            r'\b\w*[bB][iI][tT][cC][hH]\w*\b',  # Parole con "bitch"
            r'[0-9]{3,}',  # Numeri lunghi (possibili numeri di telefono, carte)
            r'https?://[^\s]+',  # URL sospetti
            r'@\w+',  # Menzioni multiple
            r'#\w+',  # Hashtag multipli
            r'[A-Z]{3,}',  # Testo tutto maiuscolo
            r'[!]{2,}',  # Punti esclamativi multipli
            r'[?]{2,}',  # Punti interrogativi multipli
        ]
    
    def load_tweets_by_year(self):
        """
        Carica i tweet di @md_pier organizzati per anno.
        """
        print("📊 Caricamento tweet per anno...")
        
        tweets_by_year = {}
        
        # Cerca file JSON per anno
        for filename in os.listdir(self.md_pier_dir):
            if filename.startswith('tweets_md_pier_') and filename.endswith('.json'):
                # Estrai anno dal nome file
                year_match = re.search(r'tweets_md_pier_(\d{4})', filename)
                if year_match:
                    year = int(year_match.group(1))
                    filepath = os.path.join(self.md_pier_dir, filename)
                    
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            tweets = json.load(f)
                        
                        tweets_by_year[year] = tweets
                        print(f"   ✅ {year}: {len(tweets)} tweet caricati")
                        
                    except Exception as e:
                        print(f"   ❌ Errore caricamento {filename}: {e}")
        
        return tweets_by_year
    
    def analyze_tweet_content(self, tweet):
        """
        Analizza il contenuto di un singolo tweet per identificare contenuti inappropriati.
        """
        inappropriate_flags = []
        suspicious_flags = []
        
        # Estrai testo del tweet
        text = tweet.get('text', '').lower()
        if not text:
            return [], []
        
        # Controlla parole chiave inappropriate
        for keyword in self.inappropriate_keywords:
            if keyword.lower() in text:
                inappropriate_flags.append(f"Keyword: {keyword}")
        
        # Controlla pattern sospetti
        for pattern in self.suspicious_patterns:
            matches = re.findall(pattern, tweet.get('text', ''))
            if matches:
                suspicious_flags.append(f"Pattern: {pattern} -> {matches[:3]}")  # Primi 3 match
        
        # Controlli aggiuntivi
        if len(text) > 500:  # Tweet molto lunghi
            suspicious_flags.append("Tweet molto lungo")
        
        if text.count('@') > 5:  # Troppe menzioni
            suspicious_flags.append("Troppe menzioni")
        
        if text.count('#') > 10:  # Troppi hashtag
            suspicious_flags.append("Troppi hashtag")
        
        if text.isupper() and len(text) > 20:  # Testo tutto maiuscolo
            suspicious_flags.append("Testo tutto maiuscolo")
        
        if text.count('!') > 5:  # Troppi punti esclamativi
            suspicious_flags.append("Troppi punti esclamativi")
        
        return inappropriate_flags, suspicious_flags
    
    def analyze_year_content(self, year: int, tweets: list):
        """
        Analizza il contenuto di tutti i tweet di un anno specifico.
        """
        print(f"\n📅 ANALISI ANNO {year}:")
        print("=" * 50)
        
        inappropriate_tweets = []
        suspicious_tweets = []
        
        for i, tweet in enumerate(tweets):
            inappropriate_flags, suspicious_flags = self.analyze_tweet_content(tweet)
            
            if inappropriate_flags or suspicious_flags:
                tweet_info = {
                    'year': year,
                    'tweet_id': tweet.get('id', f'unknown_{i}'),
                    'created_at': tweet.get('createdAt', 'unknown'),
                    'text': tweet.get('text', '')[:200] + '...' if len(tweet.get('text', '')) > 200 else tweet.get('text', ''),
                    'inappropriate_flags': '; '.join(inappropriate_flags),
                    'suspicious_flags': '; '.join(suspicious_flags),
                    'likes': tweet.get('likeCount', 0),
                    'retweets': tweet.get('retweetCount', 0),
                    'replies': tweet.get('replyCount', 0),
                    'severity': 'HIGH' if inappropriate_flags else 'MEDIUM'
                }
                
                if inappropriate_flags:
                    inappropriate_tweets.append(tweet_info)
                    print(f"   🔴 TWEET INAPPROPRIATO #{i+1}:")
                    print(f"      ID: {tweet_info['tweet_id']}")
                    print(f"      Data: {tweet_info['created_at']}")
                    print(f"      Testo: {tweet_info['text'][:100]}...")
                    print(f"      Flag: {tweet_info['inappropriate_flags']}")
                    print()
                
                elif suspicious_flags:
                    suspicious_tweets.append(tweet_info)
                    print(f"   🟡 TWEET SOSPETTO #{i+1}:")
                    print(f"      ID: {tweet_info['tweet_id']}")
                    print(f"      Data: {tweet_info['created_at']}")
                    print(f"      Testo: {tweet_info['text'][:100]}...")
                    print(f"      Flag: {tweet_info['suspicious_flags']}")
                    print()
        
        # Statistiche anno
        total_tweets = len(tweets)
        inappropriate_count = len(inappropriate_tweets)
        suspicious_count = len(suspicious_tweets)
        
        print(f"📊 STATISTICHE {year}:")
        print(f"   Tweet totali: {total_tweets}")
        print(f"   Tweet inappropriati: {inappropriate_count} ({inappropriate_count/total_tweets*100:.1f}%)")
        print(f"   Tweet sospetti: {suspicious_count} ({suspicious_count/total_tweets*100:.1f}%)")
        
        return inappropriate_tweets, suspicious_tweets
    
    def save_analysis_results(self, all_inappropriate: list, all_suspicious: list):
        """
        Salva i risultati dell'analisi in CSV.
        """
        print("\n💾 Salvataggio risultati...")
        
        # Combina tutti i risultati
        all_results = all_inappropriate + all_suspicious
        
        if all_results:
            # Crea DataFrame
            df = pd.DataFrame(all_results)
            
            # Ordina per anno e severità
            df = df.sort_values(['year', 'severity'], ascending=[True, False])
            
            # Salva CSV
            df.to_csv(self.output_filename, index=False, encoding='utf-8')
            print(f"   ✅ Risultati salvati in: {self.output_filename}")
            
            # Mostra riepilogo
            print(f"\n📋 RIEPILOGO TOTALE:")
            print(f"   Tweet inappropriati totali: {len(all_inappropriate)}")
            print(f"   Tweet sospetti totali: {len(all_suspicious)}")
            print(f"   Tweet problematici totali: {len(all_results)}")
            
            # Raggruppa per anno
            year_summary = df.groupby('year').agg({
                'tweet_id': 'count',
                'severity': lambda x: (x == 'HIGH').sum()
            }).rename(columns={'tweet_id': 'total_problematic', 'severity': 'high_severity'})
            
            print(f"\n📅 DISTRIBUZIONE PER ANNO:")
            for year, row in year_summary.iterrows():
                print(f"   {year}: {row['total_problematic']} problematici ({row['high_severity']} alta severità)")
        
        else:
            print("   ✅ Nessun tweet problematico trovato!")
    
    def run(self):
        """
        Esegue l'analisi completa del contenuto.
        """
        try:
            # 1. Carica tweet per anno
            tweets_by_year = self.load_tweets_by_year()
            
            if not tweets_by_year:
                print("❌ Nessun tweet trovato!")
                return
            
            # 2. Analizza ogni anno
            all_inappropriate = []
            all_suspicious = []
            
            for year in sorted(tweets_by_year.keys()):
                tweets = tweets_by_year[year]
                inappropriate, suspicious = self.analyze_year_content(year, tweets)
                
                all_inappropriate.extend(inappropriate)
                all_suspicious.extend(suspicious)
            
            # 3. Salva risultati
            self.save_analysis_results(all_inappropriate, all_suspicious)
            
            print(f"\n🎉 ANALISI CONTENUTO COMPLETATA PER @md_pier!")
            
        except Exception as e:
            print(f"❌ Errore durante l'analisi: {e}")
            raise

def main():
    """
    Funzione principale.
    """
    try:
        # Crea e esegui l'analyzer
        analyzer = MDPierContentAnalyzer()
        analyzer.run()
        
    except Exception as e:
        print(f"❌ Errore fatale: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

