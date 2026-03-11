#!/usr/bin/env python3
"""
Script per creare heatmap comprehensive solo per i thread.
Combina i dati della matrice oraria con quelli dei thread.

USAGE:
    python3.11 create_thread_heatmap.py <username> <year>

ESEMPIO:
    python3.11 create_thread_heatmap.py NTFabiano 2024
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime
import argparse
import os

class ThreadHeatmapCreator:
    """
    Classe per creare heatmap comprehensive solo per i thread.
    """
    
    def __init__(self, username: str, year: int):
        self.username = username
        self.year = year
        self.input_filename = f"{username}_{year}_hourly_matrix.csv"
        self.thread_filename = "thread_analysis.csv"
        self.output_filename = f"{username}_{year}_thread_heatmap_comprehensive.png"
        
        # Validazioni
        if not os.path.exists(self.input_filename):
            raise FileNotFoundError(f"File {self.input_filename} non trovato!")
        if not os.path.exists(self.thread_filename):
            raise FileNotFoundError(f"File {self.thread_filename} non trovato!")
        
        print(f"🧵 CREAZIONE HEATMAP THREAD PER @{username} - {year}")
        print(f"📁 File input: {self.input_filename}")
        print(f"📁 File thread: {self.thread_filename}")
        print(f"📁 File output: {self.output_filename}")
        print("=" * 70)
    
    def load_and_combine_data(self) -> pd.DataFrame:
        """
        Carica i dati della matrice oraria e li combina con i dati dei thread.
        """
        print("📊 Caricamento e combinazione dati...")
        
        # Carica matrice oraria
        hourly_df = pd.read_csv(self.input_filename)
        print(f"   ✅ Matrice oraria caricata: {len(hourly_df)} giorni")
        
        # Carica dati thread
        threads_df = pd.read_csv(self.thread_filename)
        print(f"   ✅ Dati thread caricati: {len(threads_df)} thread")
        
        # Combina i dati
        combined_df = hourly_df.copy()
        
        # Aggiungi colonne thread
        combined_df['thread_count'] = 0
        combined_df['thread_tweets_total'] = 0
        
        # Popola le colonne thread
        for _, thread in threads_df.iterrows():
            first_time = pd.to_datetime(thread.get('first_tweet_time'))
            if first_time and first_time.year == self.year:
                date_key = first_time.strftime('%Y-%m-%d')
                mask = combined_df['date_short'] == date_key
                
                if mask.any():
                    combined_df.loc[mask, 'thread_count'] += 1
                    combined_df.loc[mask, 'thread_tweets_total'] += thread.get('tweet_count', 0)
        
        # Filtra solo giorni con thread
        thread_days = combined_df[combined_df['thread_count'] > 0].copy()
        print(f"   🧵 Giorni con thread: {len(thread_days)}")
        
        # Mostra statistiche thread
        total_threads = thread_days['thread_count'].sum()
        total_thread_tweets = thread_days['thread_tweets_total'].sum()
        print(f"   📊 Thread totali: {total_threads}")
        print(f"   📝 Tweet nei thread: {total_thread_tweets}")
        
        return combined_df, thread_days
    
    def create_thread_hourly_matrix(self, thread_days: pd.DataFrame):
        """
        Crea matrice oraria solo per i thread.
        """
        print("⏰ Creazione matrice oraria thread...")
        
        # Crea DataFrame vuoto per i thread
        thread_matrix = pd.DataFrame()
        
        # Per ogni giorno con thread, calcola l'attività oraria dei thread
        for idx, row in thread_days.iterrows():
            date_key = row['date_short']
            thread_count = row['thread_count']
            thread_tweets_total = row['thread_tweets_total']
            
            # Trova i thread di questo giorno nel file thread_analysis.csv
            thread_details = self.get_thread_details_for_date(date_key)
            
            if thread_details:
                # Distribuisci i tweet dei thread nelle ore
                hourly_distribution = self.distribute_thread_tweets_hourly(thread_details)
                
                # Aggiungi alla matrice
                day_data = {
                    'date_short': date_key,
                    'day_of_week': row['day_of_week'],
                    'month': row['month'],
                    'thread_count': thread_count,
                    'thread_tweets_total': thread_tweets_total
                }
                
                # Aggiungi le 24 colonne orarie
                for hour in range(24):
                    day_data[f'hour_{hour:02d}'] = hourly_distribution.get(hour, 0)
                
                thread_matrix = pd.concat([thread_matrix, pd.DataFrame([day_data])], ignore_index=True)
        
        print(f"   ✅ Matrice thread creata: {len(thread_matrix)} giorni")
        return thread_matrix
    
    def get_thread_details_for_date(self, date_key: str) -> list:
        """
        Recupera i dettagli dei thread per una data specifica.
        """
        try:
            # Carica il file thread_analysis.csv
            if os.path.exists(self.thread_filename):
                threads_df = pd.read_csv(self.thread_filename)
                
                # Filtra thread per data
                date_threads = []
                for _, thread in threads_df.iterrows():
                    first_time = pd.to_datetime(thread.get('first_tweet_time'))
                    if first_time and first_time.strftime('%Y-%m-%d') == date_key:
                        date_threads.append(thread)
                
                return date_threads
        except Exception as e:
            print(f"   ⚠️ Errore caricamento thread per {date_key}: {e}")
        
        return []
    
    def distribute_thread_tweets_hourly(self, thread_details: list) -> dict:
        """
        Distribuisce i tweet dei thread nelle ore del giorno.
        """
        hourly_distribution = {hour: 0 for hour in range(24)}
        
        for thread in thread_details:
            tweet_count = thread.get('tweet_count', 0)
            first_time = pd.to_datetime(thread.get('first_tweet_time'))
            
            if first_time and tweet_count > 0:
                # Distribuisci i tweet nelle ore successive
                hour = first_time.hour
                
                # Distribuisci i tweet del thread nelle ore successive
                for i in range(min(tweet_count, 24)):  # Max 24 ore
                    current_hour = (hour + i) % 24
                    hourly_distribution[current_hour] += 1
        
        return hourly_distribution
    
    def create_comprehensive_thread_heatmap(self, df: pd.DataFrame, thread_matrix: pd.DataFrame):
        """
        Crea heatmap comprehensive per i thread.
        """
        print("🎯 Creazione heatmap comprehensive thread...")
        
        # Crea figura grande
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(24, 20))
        fig.suptitle(f'ANALISI COMPLETA THREAD @{self.username} - {self.year}', 
                     fontsize=24, fontweight='bold', y=0.98)
        
        # 1. Heatmap thread principale (giorni vs ore)
        hour_cols = [f'hour_{hour:02d}' for hour in range(24)]
        
        if not thread_matrix.empty:
            heatmap_data = thread_matrix[hour_cols].values
            
            im1 = sns.heatmap(heatmap_data.T, 
                              cmap='YlOrRd', 
                              cbar_kws={'label': 'Tweet Thread per Ora'},
                              ax=ax1,
                              cbar=True)
            
            ax1.set_title('Heatmap Thread: Giorni vs Ore (Solo Thread)', 
                          fontsize=18, fontweight='bold', pad=20)
            ax1.set_xlabel('Giorni con Thread', fontsize=14)
            ax1.set_ylabel('Ore del Giorno (00:00-23:00)', fontsize=14)
            
            # Personalizza assi
            y_ticks = range(24)
            y_labels = [f'{hour:02d}:00' for hour in y_ticks]
            ax1.set_yticks(y_ticks)
            ax1.set_yticklabels(y_labels)
            
            if len(thread_matrix) > 0:
                x_ticks = np.linspace(0, len(thread_matrix)-1, min(10, len(thread_matrix)), dtype=int)
                x_labels = [thread_matrix.iloc[i]['date_short'] for i in x_ticks]
                ax1.set_xticks(x_ticks)
                ax1.set_xticklabels(x_labels, rotation=45, ha='right')
        else:
            ax1.text(0.5, 0.5, 'Nessun thread trovato', ha='center', va='center', 
                     transform=ax1.transAxes, fontsize=16)
            ax1.set_title('Nessun Thread Trovato', fontsize=18, fontweight='bold')
        
        # 2. Heatmap thread mensile
        if not thread_matrix.empty:
            monthly_thread_data = thread_matrix.groupby('month').agg({
                f'hour_{hour:02d}': 'sum' for hour in range(24)
            }).reset_index()
            
            monthly_heatmap = monthly_thread_data[hour_cols].values
            
            im2 = sns.heatmap(monthly_heatmap.T, 
                              cmap='YlOrRd', 
                              cbar_kws={'label': 'Tweet Thread Totali per Mese'},
                              ax=ax2,
                              annot=True, 
                              fmt='.0f',
                              cbar=True)
            
            ax2.set_title('Heatmap Thread Mensile: Mesi vs Ore', 
                          fontsize=18, fontweight='bold', pad=20)
            ax2.set_xlabel('Mese', fontsize=14)
            ax2.set_ylabel('Ora del Giorno', fontsize=14)
            
            # Personalizza assi
            month_names = ['Gen', 'Feb', 'Mar', 'Apr', 'Mag', 'Giu', 
                          'Lug', 'Ago', 'Set', 'Ott', 'Nov', 'Dic']
            ax2.set_xticks(range(len(month_names)))
            ax2.set_xticklabels(month_names)
            
            ax2.set_yticks(y_ticks)
            ax2.set_yticklabels(y_labels)
        else:
            ax2.text(0.5, 0.5, 'Nessun thread trovato', ha='center', va='center', 
                     transform=ax2.transAxes, fontsize=16)
            ax2.set_title('Nessun Thread Trovato', fontsize=18, fontweight='bold')
        
        # 3. Statistiche thread aggregate
        ax3.axis('off')
        
        if not thread_matrix.empty:
            # Crea tabella con statistiche thread
            stats_data = [
                ['Metrica Thread', 'Valore', 'Dettagli'],
                ['Giorni con Thread', f'{len(thread_matrix)}', f'Su {len(df)} totali'],
                ['Thread Totali', f'{thread_matrix["thread_count"].sum():,}', ''],
                ['Tweet nei Thread', f'{thread_matrix["thread_tweets_total"].sum():,}', ''],
                ['Thread per Giorno', f'{thread_matrix["thread_count"].mean():.2f}', 'Media'],
                ['Tweet Thread per Giorno', f'{thread_matrix["thread_tweets_total"].mean():.2f}', 'Media'],
                ['Giorno più Thread', f'{thread_matrix.loc[thread_matrix["thread_count"].idxmax(), "date_short"]}', 
                 f'{thread_matrix["thread_count"].max()} thread'],
                ['Ora più Thread', f'{thread_matrix[hour_cols].sum().idxmax().replace("hour_", "")}:00', 
                 f'{thread_matrix[hour_cols].sum().max()} tweet']
            ]
            
            table = ax3.table(cellText=stats_data[1:], colLabels=stats_data[0], 
                             cellLoc='center', loc='center', bbox=[0, 0, 1, 1])
            table.auto_set_font_size(False)
            table.set_fontsize(12)
            table.scale(1, 2)
            
            # Stile tabella
            for i in range(len(stats_data)):
                for j in range(len(stats_data[0])):
                    if i == 0:  # Header
                        table[(i, j)].set_facecolor('#4CAF50')
                        table[(i, j)].set_text_props(weight='bold', color='white')
                    elif j == 0:  # Prima colonna
                        table[(i, j)].set_facecolor('#2196F3')
                        table[(i, j)].set_text_props(weight='bold', color='white')
                    else:
                        table[(i, j)].set_facecolor('#f0f0f0')
        else:
            ax3.text(0.5, 0.5, 'Nessun thread trovato per le statistiche', 
                     ha='center', va='center', transform=ax3.transAxes, fontsize=16)
        
        plt.tight_layout()
        
        # Salva
        plt.savefig(self.output_filename, dpi=300, bbox_inches='tight')
        print(f"   ✅ Heatmap thread comprehensive salvato: {self.output_filename}")
        
        return fig
    
    def run(self):
        """
        Esegue la creazione del heatmap thread comprehensive.
        """
        try:
            # 1. Carica e combina dati
            df, thread_days = self.load_and_combine_data()
            
            # 2. Crea matrice oraria thread
            thread_matrix = self.create_thread_hourly_matrix(thread_days)
            
            # 3. Crea heatmap comprehensive
            self.create_comprehensive_thread_heatmap(df, thread_matrix)
            
            print(f"\n🎉 HEATMAP THREAD COMPREHENSIVE COMPLETATO PER @{self.username} - {self.year}!")
            print(f"📁 File creato: {self.output_filename}")
            
            # Statistiche finali
            if not thread_days.empty:
                print(f"\n📊 STATISTICHE FINALI THREAD:")
                print(f"   🧵 Giorni con thread: {len(thread_days)}")
                print(f"   📝 Thread totali: {thread_days['thread_count'].sum():,}")
                print(f"   🎯 Tweet nei thread: {thread_days['thread_tweets_total'].sum():,}")
                print(f"   📈 Media thread/giorno: {thread_days['thread_count'].mean():.2f}")
            
        except Exception as e:
            print(f"❌ Errore durante la creazione: {e}")
            raise

def main():
    """
    Funzione principale.
    """
    parser = argparse.ArgumentParser(
        description="Crea heatmap comprehensive solo per i thread.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
ESEMPI:
    python3.11 create_thread_heatmap.py NTFabiano 2024
    python3.11 create_thread_heatmap.py md_pier 2024
        """
    )
    
    parser.add_argument("username", help="Username Twitter (es. NTFabiano)")
    parser.add_argument("year", type=int, help="Anno da analizzare (es. 2024)")
    
    args = parser.parse_args()
    
    try:
        # Crea e esegui il creator
        creator = ThreadHeatmapCreator(args.username, args.year)
        creator.run()
        
    except Exception as e:
        print(f"❌ Errore fatale: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
