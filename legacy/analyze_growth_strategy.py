#!/usr/bin/env python3
"""
Script per analizzare la strategia di crescita di @NTFabiano e calcolare
quanti tweet singoli e thread fare per settimana per replicare la sua crescita.

USAGE:
    python3.11 analyze_growth_strategy.py NTFabiano 2024
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime, timedelta
import argparse
import os

class GrowthStrategyAnalyzer:
    """
    Classe per analizzare la strategia di crescita e calcolare le metriche settimanali.
    """
    
    def __init__(self, username: str, year: int):
        self.username = username
        self.year = year
        self.calendar_file = f"calendar_2024_comparative_ntfabiano_vs_md_pier.csv"
        self.thread_file = "thread_analysis.csv"
        self.output_filename = f"{username}_{year}_growth_strategy_analysis.png"
        
        # Validazioni
        if not os.path.exists(self.calendar_file):
            raise FileNotFoundError(f"File {self.calendar_file} non trovato!")
        if not os.path.exists(self.thread_file):
            raise FileNotFoundError(f"File {self.thread_file} non trovato!")
        
        print(f"🚀 ANALISI STRATEGIA CRESCITA @{username} - {year}")
        print(f"📁 File calendario: {self.calendar_file}")
        print(f"📁 File thread: {self.thread_file}")
        print(f"📁 File output: {self.output_filename}")
        print("=" * 80)
    
    def load_and_analyze_data(self):
        """
        Carica e analizza tutti i dati per calcolare la strategia.
        """
        print("📊 Caricamento e analisi dati...")
        
        # Carica calendario con attività
        calendar_df = pd.read_csv(self.calendar_file)
        print(f"   ✅ Calendario caricato: {len(calendar_df)} giorni")
        
        # Carica dati thread
        threads_df = pd.read_csv(self.thread_file)
        print(f"   ✅ Thread caricati: {len(threads_df)} thread")
        
        # Filtra solo dati NTFabiano
        ntfabiano_df = calendar_df[calendar_df['has_activity'] == True].copy()
        print(f"   🎯 Giorni attivi NTFabiano: {len(ntfabiano_df)}")
        
        # Aggiungi colonne settimanali
        ntfabiano_df['date'] = pd.to_datetime(ntfabiano_df['date_short'])
        ntfabiano_df['week_number'] = ntfabiano_df['date'].dt.isocalendar().week
        ntfabiano_df['week_start'] = ntfabiano_df['date'].dt.to_period('W').dt.start_time
        
        return ntfabiano_df, threads_df
    
    def calculate_weekly_metrics(self, ntfabiano_df: pd.DataFrame):
        """
        Calcola le metriche settimanali per la strategia.
        """
        print("📈 Calcolo metriche settimanali...")
        
        # Raggruppa per settimana
        weekly_stats = ntfabiano_df.groupby(['week_number', 'week_start']).agg({
            'tweets_singoli': 'sum',
            'thread_count': 'sum',
            'thread_tweets_total': 'sum',
            'tweets_totali': 'sum'
        }).reset_index()
        
        # Calcola metriche aggiuntive
        weekly_stats['thread_tweets_avg'] = weekly_stats['thread_tweets_total'] / weekly_stats['thread_count'].replace(0, 1)
        weekly_stats['engagement_ratio'] = weekly_stats['thread_tweets_total'] / weekly_stats['tweets_singoli'].replace(0, 1)
        
        # Calcola medie e deviazioni standard
        avg_singles = weekly_stats['tweets_singoli'].mean()
        avg_threads = weekly_stats['thread_count'].mean()
        avg_thread_tweets = weekly_stats['thread_tweets_total'].mean()
        
        std_singles = weekly_stats['tweets_singoli'].std()
        std_threads = weekly_stats['thread_count'].std()
        std_thread_tweets = weekly_stats['thread_tweets_total'].std()
        
        print(f"   📊 MEDIE SETTIMANALI:")
        print(f"      🎯 Tweet singoli: {avg_singles:.1f} ± {std_singles:.1f}")
        print(f"      🧵 Thread: {avg_threads:.1f} ± {std_threads:.1f}")
        print(f"      📝 Tweet nei thread: {avg_thread_tweets:.1f} ± {std_thread_tweets:.1f}")
        
        return weekly_stats, {
            'avg_singles': avg_singles,
            'avg_threads': avg_threads,
            'avg_thread_tweets': avg_thread_tweets,
            'std_singles': std_singles,
            'std_threads': std_threads,
            'std_thread_tweets': std_thread_tweets
        }
    
    def analyze_optimal_strategy(self, weekly_stats: pd.DataFrame, metrics: dict):
        """
        Analizza la strategia ottimale basata sui dati.
        """
        print("🎯 Analisi strategia ottimale...")
        
        # Trova le settimane migliori (più engagement)
        best_weeks = weekly_stats.nlargest(5, 'engagement_ratio')
        worst_weeks = weekly_stats.nsmallest(5, 'engagement_ratio')
        
        print(f"   🏆 TOP 5 SETTIMANE (miglior engagement):")
        for _, week in best_weeks.iterrows():
            week_start = week['week_start'].strftime('%Y-%m-%d')
            engagement = week['engagement_ratio']
            singles = week['tweets_singoli']
            threads = week['thread_count']
            print(f"      📅 {week_start}: {singles} singoli, {threads} thread (ratio: {engagement:.2f})")
        
        print(f"   📉 TOP 5 SETTIMANE (peggior engagement):")
        for _, week in worst_weeks.iterrows():
            week_start = week['week_start'].strftime('%Y-%m-%d')
            engagement = week['engagement_ratio']
            singles = week['tweets_singoli']
            threads = week['thread_count']
            print(f"      📅 {week_start}: {singles} singoli, {threads} thread (ratio: {engagement:.2f})")
        
        # Calcola strategia raccomandata
        recommended_singles = int(metrics['avg_singles'])
        recommended_threads = int(metrics['avg_threads'])
        
        print(f"\n   💡 STRATEGIA RACCOMANDATA PER SETTIMANA:")
        print(f"      🎯 Tweet singoli: {recommended_singles}")
        print(f"      🧵 Thread: {recommended_threads}")
        print(f"      📝 Tweet totali: {recommended_singles + recommended_threads}")
        
        return best_weeks, worst_weeks, {
            'recommended_singles': recommended_singles,
            'recommended_threads': recommended_threads
        }
    
    def create_strategy_visualization(self, weekly_stats: pd.DataFrame, metrics: dict, strategy: dict):
        """
        Crea visualizzazione della strategia di crescita.
        """
        print("🎨 Creazione visualizzazione strategia...")
        
        # Crea figura con subplot
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 16))
        fig.suptitle(f'STRATEGIA CRESCITA @{self.username} - {self.year}\nAnalisi Settimanale e Raccomandazioni', 
                     fontsize=20, fontweight='bold', y=0.98)
        
        # 1. Trend settimanale tweet singoli vs thread
        weeks = range(len(weekly_stats))
        ax1.plot(weeks, weekly_stats['tweets_singoli'], 'o-', label='Tweet Singoli', linewidth=2, markersize=6)
        ax1.plot(weeks, weekly_stats['thread_count'], 's-', label='Thread', linewidth=2, markersize=6)
        ax1.axhline(y=metrics['avg_singles'], color='blue', linestyle='--', alpha=0.7, label=f'Media Singoli: {metrics["avg_singles"]:.1f}')
        ax1.axhline(y=metrics['avg_threads'], color='orange', linestyle='--', alpha=0.7, label=f'Media Thread: {metrics["avg_threads"]:.1f}')
        ax1.set_title('Trend Settimanale: Tweet Singoli vs Thread', fontsize=16, fontweight='bold')
        ax1.set_xlabel('Settimana', fontsize=12)
        ax1.set_ylabel('Numero', fontsize=12)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. Distribuzione settimanale
        ax2.bar(weeks, weekly_stats['tweets_singoli'], alpha=0.7, label='Tweet Singoli', color='skyblue')
        ax2.bar(weeks, weekly_stats['thread_count'], alpha=0.7, label='Thread', color='orange', bottom=weekly_stats['tweets_singoli'])
        ax2.set_title('Distribuzione Settimanale: Tweet Singoli + Thread', fontsize=16, fontweight='bold')
        ax2.set_xlabel('Settimana', fontsize=12)
        ax2.set_ylabel('Numero Totale', fontsize=12)
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 3. Scatter plot: singoli vs thread per settimana
        ax3.scatter(weekly_stats['tweets_singoli'], weekly_stats['thread_count'], 
                    s=100, alpha=0.7, c=weekly_stats['week_number'], cmap='viridis')
        ax3.axhline(y=strategy['recommended_threads'], color='red', linestyle='--', alpha=0.7, 
                    label=f'Target Thread: {strategy["recommended_threads"]}')
        ax3.axvline(x=strategy['recommended_singles'], color='red', linestyle='--', alpha=0.7, 
                    label=f'Target Singoli: {strategy["recommended_singles"]}')
        ax3.set_title('Correlazione: Tweet Singoli vs Thread per Settimana', fontsize=16, fontweight='bold')
        ax3.set_xlabel('Tweet Singoli', fontsize=12)
        ax3.set_ylabel('Thread', fontsize=12)
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # 4. Tabella strategia raccomandata
        ax4.axis('off')
        
        strategy_data = [
            ['METRICA', 'VALORE TARGET', 'FREQUENZA'],
            ['🎯 Tweet Singoli', f'{strategy["recommended_singles"]}', 'Per Settimana'],
            ['🧵 Thread', f'{strategy["recommended_threads"]}', 'Per Settimana'],
            ['📝 Tweet Totali', f'{strategy["recommended_singles"] + strategy["recommended_threads"]}', 'Per Settimana'],
            ['📊 Tweet Singoli', f'{strategy["recommended_singles"] * 52}', 'Per Anno'],
            ['🧵 Thread', f'{strategy["recommended_threads"] * 52}', 'Per Anno'],
            ['📈 Frequenza Singoli', f'{strategy["recommended_singles"] / 7:.1f}', 'Per Giorno'],
            ['🧵 Frequenza Thread', f'{strategy["recommended_threads"] / 7:.1f}', 'Per Giorno']
        ]
        
        table = ax4.table(cellText=strategy_data[1:], colLabels=strategy_data[0], 
                         cellLoc='center', loc='center', bbox=[0, 0, 1, 1])
        table.auto_set_font_size(False)
        table.set_fontsize(11)
        table.scale(1, 2.5)
        
        # Stile tabella
        for i in range(len(strategy_data)):
            for j in range(len(strategy_data[0])):
                if i == 0:  # Header
                    table[(i, j)].set_facecolor('#4CAF50')
                    table[(i, j)].set_text_props(weight='bold', color='white')
                elif j == 0:  # Prima colonna
                    table[(i, j)].set_facecolor('#2196F3')
                    table[(i, j)].set_text_props(weight='bold', color='white')
                else:
                    table[(i, j)].set_facecolor('#f0f0f0')
        
        plt.tight_layout()
        
        # Salva
        plt.savefig(self.output_filename, dpi=300, bbox_inches='tight')
        print(f"   ✅ Visualizzazione strategia salvata: {self.output_filename}")
        
        return fig
    
    def generate_weekly_schedule(self, strategy: dict):
        """
        Genera un calendario settimanale raccomandato.
        """
        print("\n📅 CALENDARIO SETTIMANALE RACCOMANDATO:")
        print("=" * 60)
        
        recommended_singles = strategy['recommended_singles']
        recommended_threads = strategy['recommended_threads']
        
        # Distribuisci i tweet nella settimana
        days = ['Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì', 'Sabato', 'Domenica']
        
        # Calcola distribuzione giornaliera
        singles_per_day = recommended_singles // 7
        threads_per_day = recommended_threads // 7
        
        # Distribuisci il resto
        singles_remainder = recommended_singles % 7
        threads_remainder = recommended_threads % 7
        
        print(f"🎯 TARGET SETTIMANALE:")
        print(f"   Tweet singoli: {recommended_singles}")
        print(f"   Thread: {recommended_threads}")
        print(f"   Totale: {recommended_singles + recommended_threads}")
        print()
        
        print(f"📅 DISTRIBUZIONE GIORNALIERA:")
        for i, day in enumerate(days):
            day_singles = singles_per_day + (1 if i < singles_remainder else 0)
            day_threads = threads_per_day + (1 if i < threads_remainder else 0)
            total = day_singles + day_threads
            
            print(f"   {day:10s}: {day_singles:2d} singoli + {day_threads:2d} thread = {total:2d} totali")
        
        print()
        print(f"💡 CONSIGLI STRATEGICI:")
        print(f"   • Mantieni {recommended_singles} tweet singoli/settimana per engagement costante")
        print(f"   • Crea {recommended_threads} thread/settimana per contenuti approfonditi")
        print(f"   • Distribuisci uniformemente nella settimana")
        print(f"   • Thread nei giorni lavorativi, singoli nei weekend")
        print(f"   • Monitora l'engagement ratio settimanalmente")
    
    def run(self):
        """
        Esegue l'analisi completa della strategia di crescita.
        """
        try:
            # 1. Carica e analizza dati
            ntfabiano_df, threads_df = self.load_and_analyze_data()
            
            # 2. Calcola metriche settimanali
            weekly_stats, metrics = self.calculate_weekly_metrics(ntfabiano_df)
            
            # 3. Analizza strategia ottimale
            best_weeks, worst_weeks, strategy = self.analyze_optimal_strategy(weekly_stats, metrics)
            
            # 4. Crea visualizzazione
            self.create_strategy_visualization(weekly_stats, metrics, strategy)
            
            # 5. Genera calendario settimanale
            self.generate_weekly_schedule(strategy)
            
            print(f"\n🎉 ANALISI STRATEGIA CRESCITA COMPLETATA PER @{self.username} - {self.year}!")
            print(f"📁 File creato: {self.output_filename}")
            
        except Exception as e:
            print(f"❌ Errore durante l'analisi: {e}")
            raise

def main():
    """
    Funzione principale.
    """
    parser = argparse.ArgumentParser(
        description="Analizza la strategia di crescita e calcola le metriche settimanali.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
ESEMPI:
    python3.11 analyze_growth_strategy.py NTFabiano 2024
    python3.11 analyze_growth_strategy.py md_pier 2024
        """
    )
    
    parser.add_argument("username", help="Username Twitter (es. NTFabiano)")
    parser.add_argument("year", type=int, help="Anno da analizzare (es. 2024)")
    
    args = parser.parse_args()
    
    try:
        # Crea e esegui l'analyzer
        analyzer = GrowthStrategyAnalyzer(args.username, args.year)
        analyzer.run()
        
    except Exception as e:
        print(f"❌ Errore fatale: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
