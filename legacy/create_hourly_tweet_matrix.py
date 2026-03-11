#!/usr/bin/env python3
"""
Script per creare una matrice oraria dei tweet per qualsiasi utente e anno.
Crea un CSV con tutti i giorni dell'anno e 24 colonne per le ore (00:00-23:00).
Ogni cella contiene il numero di tweet in quell'ora specifica.

USAGE:
    python3.11 create_hourly_tweet_matrix.py <username> <year> [input_dir]

ESEMPIO:
    python3.11 create_hourly_tweet_matrix.py NTFabiano 2024 NTFabiano_tweets_analysis
"""

import pandas as pd
import json
import glob
import argparse
from datetime import datetime, timedelta
import re
from typing import Dict, List, Tuple
import os

class HourlyTweetMatrixCreator:
    """
    Classe per creare matrici orarie dei tweet per qualsiasi utente e anno.
    """
    
    def __init__(self, username: str, year: int, input_dir: str = None):
        self.username = username
        self.year = year
        self.input_dir = input_dir or f"{username}_tweets_analysis"
        self.output_filename = f"{username}_{year}_hourly_matrix.csv"
        
        # Validazioni
        if not os.path.exists(self.input_dir):
            raise FileNotFoundError(f"Directory {self.input_dir} non trovata!")
        
        print(f"🚀 CREAZIONE MATRICE ORARIA PER @{username} - {year}")
        print(f"📁 Directory input: {self.input_dir}")
        print(f"📁 File output: {self.output_filename}")
        print("=" * 70)
    
    def parse_twitter_date(self, date_str: str) -> datetime:
        """
        Parsa le date Twitter in formato datetime.
        Gestisce tutti i formati comuni.
        """
        if not date_str or pd.isna(date_str):
            return None
        
        # Formati comuni per le date Twitter
        formats = [
            '%Y-%m-%dT%H:%M:%S+00:00',
            '%Y-%m-%dT%H:%M:%S.%f+00:00',
            '%Y-%m-%dT%H:%M:%S.%fZ',
            '%Y-%m-%dT%H:%M:%SZ',
            '%a %b %d %H:%M:%S %z %Y',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d'
        ]
        
        for fmt in formats:
            try:
                if fmt == '%a %b %d %H:%M:%S %z %Y':
                    # Rimuovi il timezone per parsing più semplice
                    date_clean = re.sub(r'\+0000', '+00:00', date_str)
                    return datetime.strptime(date_clean, fmt)
                else:
                    return datetime.strptime(date_str, fmt)
            except:
                continue
        
        print(f"⚠️ Impossibile parsare data: {date_str}")
        return None
    
    def create_calendar_base(self) -> pd.DataFrame:
        """
        Crea il calendario base con tutti i giorni dell'anno.
        """
        print("📅 Creazione calendario base...")
        
        # Crea range di date per tutto l'anno
        start_date = datetime(self.year, 1, 1)
        
        # Determina se è anno bisestile
        if self.year % 4 == 0 and (self.year % 100 != 0 or self.year % 400 == 0):
            end_date = datetime(self.year, 12, 31)
            total_days = 366
            print(f"   🎯 {self.year} è un anno bisestile ({total_days} giorni)")
        else:
            end_date = datetime(self.year, 12, 31)
            total_days = 365
            print(f"   🎯 {self.year} è un anno normale ({total_days} giorni)")
        
        # Lista per raccogliere tutte le date
        all_dates = []
        current_date = start_date
        
        while current_date <= end_date:
            # Formato ISO per compatibilità
            iso_format = current_date.strftime('%Y-%m-%dT00:00:00+00:00')
            date_short = current_date.strftime('%Y-%m-%d')
            
            # Informazioni aggiuntive utili
            day_of_week = current_date.strftime('%A')
            day_of_year = current_date.timetuple().tm_yday
            month_name = current_date.strftime('%B')
            quarter = (current_date.month - 1) // 3 + 1
            
            all_dates.append({
                'date_iso': iso_format,
                'date_short': date_short,
                'day_of_week': day_of_week,
                'day_of_year': day_of_year,
                'month': current_date.month,
                'month_name': month_name,
                'quarter': quarter,
                'year': self.year,
                'is_weekend': current_date.weekday() >= 5,
                'is_month_start': current_date.day == 1,
                'is_month_end': (current_date + timedelta(days=1)).month != current_date.month
            })
            
            current_date += timedelta(days=1)
        
        calendar_df = pd.DataFrame(all_dates)
        print(f"   ✅ Calendario creato: {len(calendar_df)} giorni")
        
        return calendar_df
    
    def load_tweets_data(self) -> List[Dict]:
        """
        Carica tutti i tweet dai file JSON per l'anno specificato.
        """
        print("📊 Caricamento dati tweet...")
        
        # Pattern per i file dell'anno specifico
        pattern = f"{self.input_dir}/tweets_{self.username}_{self.year}_*.json"
        json_files = glob.glob(pattern)
        
        if not json_files:
            print(f"   ⚠️ Nessun file trovato per {self.username} nel {self.year}")
            return []
        
        print(f"   📁 File trovati: {len(json_files)}")
        
        all_tweets = []
        total_tweets = 0
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Filtra solo tweet dell'anno specificato
                    year_tweets = []
                    for tweet in data:
                        tweet_date = self.parse_twitter_date(
                            tweet.get('createdAt') or tweet.get('created_at')
                        )
                        
                        if tweet_date and tweet_date.year == self.year:
                            year_tweets.append(tweet)
                    
                    all_tweets.extend(year_tweets)
                    total_tweets += len(year_tweets)
                    
                    print(f"   ✅ {os.path.basename(json_file)}: {len(year_tweets)} tweet")
                    
            except Exception as e:
                print(f"   ❌ Errore caricamento {json_file}: {e}")
        
        print(f"   📊 Tweet totali caricati: {total_tweets}")
        return all_tweets
    
    def create_hourly_columns(self, calendar_df: pd.DataFrame, tweets: List[Dict]) -> pd.DataFrame:
        """
        Crea le 24 colonne orarie e popola con i conteggi dei tweet.
        """
        print("⏰ Creazione colonne orarie...")
        
        # Inizializza le 24 colonne orarie con 0
        for hour in range(24):
            hour_col = f"hour_{hour:02d}"
            calendar_df[hour_col] = 0
        
        # Inizializza anche colonne aggregate
        calendar_df['tweets_totali'] = 0
        calendar_df['has_activity'] = False
        
        # Crea dizionario per mappare date a ore
        date_hour_counts = {}
        
        # Popola il dizionario con i tweet
        for tweet in tweets:
            tweet_date = self.parse_twitter_date(
                tweet.get('createdAt') or tweet.get('created_at')
            )
            
            if tweet_date:
                date_key = tweet_date.strftime('%Y-%m-%d')
                hour = tweet_date.hour
                
                if date_key not in date_hour_counts:
                    date_hour_counts[date_key] = {i: 0 for i in range(24)}
                
                date_hour_counts[date_key][hour] += 1
        
        # Popola il DataFrame
        populated_rows = 0
        for idx, row in calendar_df.iterrows():
            date_key = row['date_short']
            
            if date_key in date_hour_counts:
                hour_counts = date_hour_counts[date_key]
                
                # Popola le 24 colonne orarie
                for hour in range(24):
                    hour_col = f"hour_{hour:02d}"
                    calendar_df.loc[idx, hour_col] = hour_counts[hour]
                
                # Calcola totali
                total_tweets = sum(hour_counts.values())
                calendar_df.loc[idx, 'tweets_totali'] = total_tweets
                calendar_df.loc[idx, 'has_activity'] = total_tweets > 0
                
                populated_rows += 1
        
        print(f"   ✅ Colonne orarie popolate: {populated_rows} giorni con dati")
        
        # Aggiungi statistiche orarie
        self.add_hourly_statistics(calendar_df)
        
        return calendar_df
    
    def add_hourly_statistics(self, df: pd.DataFrame):
        """
        Aggiunge statistiche aggregate per le ore.
        """
        print("📊 Aggiunta statistiche orarie...")
        
        # Ore più attive
        hour_columns = [f"hour_{hour:02d}" for hour in range(24)]
        hourly_totals = df[hour_columns].sum()
        
        # Trova le ore più attive
        top_hours = hourly_totals.nlargest(5)
        
        print(f"   🏆 TOP 5 ORE PIÙ ATTIVE:")
        for hour, count in top_hours.items():
            hour_num = int(hour.split('_')[1])
            print(f"      {hour_num:02d}:00 - {count} tweet")
        
        # Aggiungi colonne aggregate
        df['peak_hour'] = df[hour_columns].idxmax(axis=1).str.replace('hour_', '')
        df['peak_hour_count'] = df[hour_columns].max(axis=1)
        df['active_hours'] = (df[hour_columns] > 0).sum(axis=1)
        
        print(f"   ✅ Statistiche orarie aggiunte")
    
    def save_results(self, df: pd.DataFrame):
        """
        Salva i risultati in CSV e mostra statistiche finali.
        """
        print("💾 Salvataggio risultati...")
        
        # Salva CSV
        df.to_csv(self.output_filename, index=False, encoding='utf-8')
        print(f"   ✅ CSV salvato: {self.output_filename}")
        
        # Statistiche finali
        print(f"\n📈 STATISTICHE FINALI:")
        print(f"   📅 Giorni totali: {len(df)}")
        print(f"   🎯 Giorni con attività: {df['has_activity'].sum()}")
        print(f"   📊 Tweet totali: {df['tweets_totali'].sum():,}")
        print(f"   ⏰ Ore più attive: {df['peak_hour'].mode().iloc[0]}:00")
        print(f"   📊 Media tweet/giorno attivo: {df[df['has_activity']]['tweets_totali'].mean():.1f}")
        
        # Mostra prime righe
        print(f"\n📋 PRIME 5 RIGHE (con colonne orarie):")
        display_cols = ['date_short', 'day_of_week', 'tweets_totali', 'peak_hour', 'peak_hour_count'] + [f"hour_{hour:02d}" for hour in range(24)]
        print(df[display_cols].head().to_string())
    
    def run(self):
        """
        Esegue l'intero processo di creazione della matrice oraria.
        """
        try:
            # 1. Crea calendario base
            calendar_df = self.create_calendar_base()
            
            # 2. Carica dati tweet
            tweets = self.load_tweets_data()
            
            if not tweets:
                print("❌ Nessun tweet trovato. Creazione calendario base senza dati.")
                self.save_results(calendar_df)
                return
            
            # 3. Crea colonne orarie
            final_df = self.create_hourly_columns(calendar_df, tweets)
            
            # 4. Salva risultati
            self.save_results(final_df)
            
            print(f"\n🎉 MATRICE ORARIA COMPLETATA PER @{self.username} - {self.year}!")
            
        except Exception as e:
            print(f"❌ Errore durante l'esecuzione: {e}")
            raise

def main():
    """
    Funzione principale per parsing argomenti e esecuzione.
    """
    parser = argparse.ArgumentParser(
        description="Crea matrice oraria dei tweet per qualsiasi utente e anno.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
ESEMPI:
    python3.11 create_hourly_tweet_matrix.py NTFabiano 2024
    python3.11 create_hourly_tweet_matrix.py md_pier 2024 md_pier_tweets_analysis
    python3.11 create_hourly_tweet_matrix.py username 2025 custom_directory
        """
    )
    
    parser.add_argument("username", help="Username Twitter (es. NTFabiano)")
    parser.add_argument("year", type=int, help="Anno da analizzare (es. 2024)")
    parser.add_argument("input_dir", nargs='?', 
                       help="Directory input (default: username_tweets_analysis)")
    
    args = parser.parse_args()
    
    # Validazioni
    if args.year < 2006:
        print("❌ Errore: Twitter è stato fondato nel 2006!")
        return
    
    if args.year > 2030:
        print("❌ Errore: Anno troppo nel futuro!")
        return
    
    try:
        # Crea e esegui l'analizzatore
        creator = HourlyTweetMatrixCreator(args.username, args.year, args.input_dir)
        creator.run()
        
    except Exception as e:
        print(f"❌ Errore fatale: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
