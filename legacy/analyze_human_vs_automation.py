#!/usr/bin/env python3
"""
Script per analizzare se l'attività di @NTFabiano è umana o automatizzata.
Analizza pattern temporali, frequenza, e altri indicatori di automazione.

USAGE:
    python3.11 analyze_human_vs_automation.py NTFabiano 2024
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime, timedelta
import argparse
import os

class HumanVsAutomationAnalyzer:
    """
    Classe per analizzare se l'attività è umana o automatizzata.
    """
    
    def __init__(self, username: str, year: int):
        self.username = username
        self.year = year
        self.thread_file = "thread_analysis.csv"
        self.output_filename = f"{username}_{year}_human_vs_automation_analysis.png"
        
        # Validazioni
        if not os.path.exists(self.thread_file):
            raise FileNotFoundError(f"File {self.thread_file} non trovato!")
        
        print(f"🤖 ANALISI UMANO vs AUTOMAZIONE @{username} - {year}")
        print(f"📁 File thread: {self.thread_file}")
        print(f"📁 File output: {self.output_filename}")
        print("=" * 70)
    
    def load_and_analyze_data(self):
        """
        Carica e analizza i dati per identificare pattern di automazione.
        """
        print("📊 Caricamento e analisi dati automazione...")
        
        # Carica dati thread
        threads_df = pd.read_csv(self.thread_file)
        print(f"   ✅ Thread caricati: {len(threads_df)} thread")
        
        # Filtra solo thread del 2024
        threads_df['first_tweet_time'] = pd.to_datetime(threads_df['first_tweet_time'])
        threads_2024 = threads_df[threads_df['first_tweet_time'].dt.year == self.year].copy()
        print(f"   🎯 Thread 2024: {len(threads_2024)}")
        
        return threads_2024
    
    def analyze_timing_patterns(self, df: pd.DataFrame):
        """
        Analizza i pattern temporali per identificare automazione.
        """
        print("⏰ Analisi pattern temporali...")
        
        # Estrai ore e minuti
        df['hour'] = df['first_tweet_time'].dt.hour
        df['minute'] = df['first_tweet_time'].dt.minute
        df['day_of_week'] = df['first_tweet_time'].dt.dayofweek
        df['is_weekend'] = df['day_of_week'].isin([5, 6])  # Sabato, Domenica
        
        # Analizza distribuzione oraria
        hourly_distribution = df['hour'].value_counts().sort_index()
        print(f"   📊 DISTRIBUZIONE ORARIA:")
        for hour in range(24):
            count = hourly_distribution.get(hour, 0)
            percentage = (count / len(df)) * 100
            print(f"      {hour:02d}:00 - {count:2d} thread ({percentage:5.1f}%)")
        
        # Trova ore picco
        peak_hour = hourly_distribution.idxmax()
        peak_count = hourly_distribution.max()
        print(f"   🎯 ORA PICCO: {peak_hour:02d}:00 con {peak_count} thread")
        
        # Analizza distribuzione settimanale
        weekday_distribution = df['day_of_week'].value_counts().sort_index()
        weekday_names = ['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom']
        print(f"   📅 DISTRIBUZIONE SETTIMANALE:")
        for day in range(7):
            count = weekday_distribution.get(day, 0)
            percentage = (count / len(df)) * 100
            print(f"      {weekday_names[day]}: {count:2d} thread ({percentage:5.1f}%)")
        
        # Analizza weekend vs giorni lavorativi
        weekend_threads = df[df['is_weekend']]['tweet_count'].sum()
        weekday_threads = df[~df['is_weekend']]['tweet_count'].sum()
        total_threads = df['tweet_count'].sum()
        
        print(f"   🏠 WEEKEND vs GIORNI LAVORATIVI:")
        print(f"      Weekend: {weekend_threads} tweet ({weekend_threads/total_threads*100:.1f}%)")
        print(f"      Lavorativi: {weekday_threads} tweet ({weekday_threads/total_threads*100:.1f}%)")
        
        return df, hourly_distribution, weekday_distribution
    
    def analyze_rapid_fire_patterns(self, df: pd.DataFrame):
        """
        Analizza pattern di "rapid-fire" che suggeriscono automazione.
        """
        print("🚀 Analisi pattern rapid-fire...")
        
        # Ordina per tempo
        df_sorted = df.sort_values('first_tweet_time').reset_index(drop=True)
        
        # Calcola gap tra thread consecutivi
        df_sorted['next_thread_time'] = df_sorted['first_tweet_time'].shift(-1)
        df_sorted['time_gap'] = df_sorted['next_thread_time'] - df_sorted['first_tweet_time']
        df_sorted['gap_minutes'] = df_sorted['time_gap'].dt.total_seconds() / 60
        
        # Identifica thread rapid-fire (gap < 30 minuti)
        rapid_fire = df_sorted[df_sorted['gap_minutes'] < 30]
        very_rapid = df_sorted[df_sorted['gap_minutes'] < 10]
        
        print(f"   ⚡ PATTERN RAPID-FIRE:")
        print(f"      Thread con gap < 30 min: {len(rapid_fire)} ({len(rapid_fire)/len(df)*100:.1f}%)")
        print(f"      Thread con gap < 10 min: {len(very_rapid)} ({len(very_rapid)/len(df)*100:.1f}%)")
        
        if len(rapid_fire) > 0:
            print(f"      Gap medio rapid-fire: {rapid_fire['gap_minutes'].mean():.1f} minuti")
            print(f"      Gap minimo: {rapid_fire['gap_minutes'].min():.1f} minuti")
        
        # Trova sequenze sospette
        suspicious_sequences = []
        for i in range(len(df_sorted) - 1):
            gap = df_sorted.iloc[i]['gap_minutes']
            if gap < 30:
                start_time = df_sorted.iloc[i]['first_tweet_time']
                end_time = df_sorted.iloc[i+1]['first_tweet_time']
                suspicious_sequences.append({
                    'start': start_time,
                    'end': end_time,
                    'gap_minutes': gap
                })
        
        print(f"      Sequenze sospette trovate: {len(suspicious_sequences)}")
        
        return df_sorted, rapid_fire, suspicious_sequences
    
    def analyze_content_patterns(self, df: pd.DataFrame):
        """
        Analizza pattern nei contenuti che suggeriscono automazione.
        """
        print("📝 Analisi pattern contenuti...")
        
        # Analizza lunghezza thread
        thread_lengths = df['tweet_count'].value_counts().sort_index()
        print(f"   📏 LUNGHEZZA THREAD:")
        for length, count in thread_lengths.head(10).items():
            percentage = (count / len(df)) * 100
            print(f"      {length:2d} tweet: {count:2d} thread ({percentage:5.1f}%)")
        
        # Trova thread molto lunghi
        long_threads = df[df['tweet_count'] > 20]
        if len(long_threads) > 0:
            print(f"   🧵 THREAD MOLTO LUNGHI (>20 tweet): {len(long_threads)}")
            for _, thread in long_threads.iterrows():
                print(f"      {thread['first_tweet_time'].strftime('%Y-%m-%d %H:%M')}: {thread['tweet_count']} tweet")
        
        # Analizza consistenza lunghezza
        avg_length = df['tweet_count'].mean()
        std_length = df['tweet_count'].std()
        print(f"   📊 STATISTICHE LUNGHEZZA:")
        print(f"      Media: {avg_length:.1f} tweet")
        print(f"      Deviazione standard: {std_length:.1f}")
        print(f"      Coefficiente variazione: {std_length/avg_length:.2f}")
        
        return df
    
    def create_automation_visualization(self, df: pd.DataFrame, hourly_dist: pd.Series, weekday_dist: pd.Series, rapid_fire: pd.DataFrame):
        """
        Crea visualizzazione per analisi umano vs automazione.
        """
        print("🎨 Creazione visualizzazione automazione...")
        
        # Crea figura con subplot
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 16))
        fig.suptitle(f'ANALISI UMANO vs AUTOMAZIONE @{self.username} - {self.year}\nPattern Temporali e Comportamentali', 
                     fontsize=20, fontweight='bold', y=0.98)
        
        # 1. Distribuzione oraria
        hours = range(24)
        counts = [hourly_dist.get(hour, 0) for hour in hours]
        
        bars = ax1.bar(hours, counts, color='#2196F3', alpha=0.7)
        ax1.set_title('Distribuzione Oraria Thread', fontsize=16, fontweight='bold')
        ax1.set_xlabel('Ora del Giorno', fontsize=12)
        ax1.set_ylabel('Numero Thread', fontsize=12)
        ax1.set_xticks(hours)
        ax1.set_xticklabels([f'{hour:02d}:00' for hour in hours])
        ax1.grid(True, alpha=0.3)
        
        # Evidenzia ore picco
        peak_hour = hourly_dist.idxmax()
        peak_count = hourly_dist.max()
        bars[peak_hour].set_color('#FF5722')
        ax1.text(peak_hour, peak_count + 1, f'PICCO\n{peak_count}', 
                ha='center', va='bottom', fontweight='bold', color='#FF5722')
        
        # 2. Distribuzione settimanale
        weekdays = range(7)
        weekday_counts = [weekday_dist.get(day, 0) for day in weekdays]
        weekday_names = ['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom']
        
        bars = ax2.bar(weekdays, weekday_counts, color='#4CAF50', alpha=0.7)
        ax2.set_title('Distribuzione Settimanale Thread', fontsize=16, fontweight='bold')
        ax2.set_xlabel('Giorno della Settimana', fontsize=12)
        ax2.set_ylabel('Numero Thread', fontsize=12)
        ax2.set_xticks(weekdays)
        ax2.set_xticklabels(weekday_names)
        ax2.grid(True, alpha=0.3)
        
        # Evidenzia giorni picco
        peak_day = weekday_dist.idxmax()
        peak_count = weekday_dist.max()
        bars[peak_day].set_color('#FF9800')
        ax2.text(peak_day, peak_count + 1, f'PICCO\n{peak_count}', 
                ha='center', va='bottom', fontweight='bold', color='#FF9800')
        
        # 3. Pattern rapid-fire
        if len(rapid_fire) > 0:
            gaps = rapid_fire['gap_minutes']
            ax3.hist(gaps, bins=20, color='#FF5722', alpha=0.7, edgecolor='black')
            ax3.set_title('Distribuzione Gap Rapid-Fire (< 30 min)', fontsize=16, fontweight='bold')
            ax3.set_xlabel('Gap in Minuti', fontsize=12)
            ax3.set_ylabel('Frequenza', fontsize=12)
            ax3.grid(True, alpha=0.3)
            
            # Aggiungi statistiche
            mean_gap = gaps.mean()
            ax3.axvline(mean_gap, color='red', linestyle='--', linewidth=2, 
                        label=f'Media: {mean_gap:.1f} min')
            ax3.legend()
        else:
            ax3.text(0.5, 0.5, 'Nessun pattern rapid-fire trovato', 
                     ha='center', va='center', transform=ax3.transAxes, fontsize=16)
            ax3.set_title('Pattern Rapid-Fire', fontsize=16, fontweight='bold')
        
        # 4. Tabella indicatori automazione
        ax4.axis('off')
        
        # Calcola indicatori
        total_threads = len(df)
        rapid_fire_pct = len(rapid_fire) / total_threads * 100 if len(rapid_fire) > 0 else 0
        very_rapid_pct = len(rapid_fire[rapid_fire['gap_minutes'] < 10]) / total_threads * 100 if len(rapid_fire) > 0 else 0
        
        # Analizza consistenza oraria
        peak_hour_pct = (hourly_dist.max() / total_threads) * 100
        weekend_pct = (df[df['is_weekend']]['tweet_count'].sum() / df['tweet_count'].sum()) * 100
        
        automation_data = [
            ['INDICATORE', 'VALORE', 'INTERPRETAZIONE'],
            ['Thread Totali', f'{total_threads}', ''],
            ['Rapid-Fire (<30min)', f'{rapid_fire_pct:.1f}%', 'Alto = Sospetto'],
            ['Molto Rapid (<10min)', f'{very_rapid_pct:.1f}%', 'Alto = Molto Sospetto'],
            ['Concentrazione Oraria', f'{peak_hour_pct:.1f}%', 'Alto = Sospetto'],
            ['Attività Weekend', f'{weekend_pct:.1f}%', 'Basso = Umano'],
            ['Gap Medio', f'{df["gap_minutes"].mean():.1f} min', 'Basso = Sospetto']
        ]
        
        table = ax4.table(cellText=automation_data[1:], colLabels=automation_data[0], 
                         cellLoc='center', loc='center', bbox=[0, 0, 1, 1])
        table.auto_set_font_size(False)
        table.set_fontsize(11)
        table.scale(1, 2.5)
        
        # Stile tabella
        for i in range(len(automation_data)):
            for j in range(len(automation_data[0])):
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
        print(f"   ✅ Visualizzazione automazione salvata: {self.output_filename}")
        
        return fig
    
    def generate_automation_assessment(self, df: pd.DataFrame, rapid_fire: pd.DataFrame, hourly_dist: pd.Series):
        """
        Genera valutazione finale se l'attività è umana o automatizzata.
        """
        print("\n🤖 VALUTAZIONE UMANO vs AUTOMAZIONE:")
        print("=" * 60)
        
        # Calcola indicatori chiave
        total_threads = len(df)
        rapid_fire_pct = len(rapid_fire) / total_threads * 100 if len(rapid_fire) > 0 else 0
        very_rapid_pct = len(rapid_fire[rapid_fire['gap_minutes'] < 10]) / total_threads * 100 if len(rapid_fire) > 0 else 0
        
        # Concentrazione oraria
        peak_hour_pct = (hourly_dist.max() / total_threads) * 100
        
        # Attività weekend
        weekend_pct = (df[df['is_weekend']]['tweet_count'].sum() / df['tweet_count'].sum()) * 100
        
        # Gap medio
        avg_gap = df['gap_minutes'].mean() if 'gap_minutes' in df.columns else 0
        
        print(f"📊 INDICATORI CHIAVE:")
        print(f"   • Rapid-fire (<30min): {rapid_fire_pct:.1f}%")
        print(f"   • Molto rapid (<10min): {very_rapid_pct:.1f}%")
        print(f"   • Concentrazione oraria: {peak_hour_pct:.1f}%")
        print(f"   • Attività weekend: {weekend_pct:.1f}%")
        print(f"   • Gap medio: {avg_gap:.1f} minuti")
        print()
        
        # Calcola score automazione (0-100)
        automation_score = 0
        
        if rapid_fire_pct > 20:
            automation_score += 25
        elif rapid_fire_pct > 10:
            automation_score += 15
        elif rapid_fire_pct > 5:
            automation_score += 10
        
        if very_rapid_pct > 10:
            automation_score += 25
        elif very_rapid_pct > 5:
            automation_score += 15
        elif very_rapid_pct > 1:
            automation_score += 10
        
        if peak_hour_pct > 30:
            automation_score += 20
        elif peak_hour_pct > 20:
            automation_score += 15
        elif peak_hour_pct > 10:
            automation_score += 10
        
        if weekend_pct < 10:
            automation_score += 15
        elif weekend_pct < 20:
            automation_score += 10
        
        if avg_gap < 60:
            automation_score += 15
        elif avg_gap < 120:
            automation_score += 10
        
        print(f"🎯 SCORE AUTOMAZIONE: {automation_score}/100")
        print()
        
        if automation_score >= 80:
            print(f"🔴 ALTA PROBABILITÀ AUTOMAZIONE:")
            print(f"   • Pattern molto sospetti")
            print(f"   • Frequenza rapid-fire alta")
            print(f"   • Concentrazione temporale forte")
            print(f"   • Probabilmente bot o scheduling")
        elif automation_score >= 60:
            print(f"🟡 MODERATA PROBABILITÀ AUTOMAZIONE:")
            print(f"   • Alcuni pattern sospetti")
            print(f"   • Possibile mix umano/automazione")
            print(f"   • Scheduling parziale")
        elif automation_score >= 40:
            print(f"🟢 BASSA PROBABILITÀ AUTOMAZIONE:")
            print(f"   • Pattern principalmente umani")
            print(f"   • Possibile scheduling leggero")
            print(f"   • Attività naturale")
        else:
            print(f"🟢 PROBABILMENTE ATTIVITÀ UMANA:")
            print(f"   • Pattern naturali")
            print(f"   • Nessun segnale di automazione")
            print(f"   • Comportamento organico")
        
        print()
        print(f"💡 CONCLUSIONE:")
        if automation_score >= 60:
            print(f"   @{self.username} probabilmente usa automazione/scheduling per i thread.")
            print(f"   La frequenza e i pattern temporali suggeriscono bot o programmazione.")
        else:
            print(f"   @{self.username} probabilmente è principalmente umano.")
            print(f"   I pattern suggeriscono attività organica con possibile scheduling leggero.")
    
    def run(self):
        """
        Esegue l'analisi completa umano vs automazione.
        """
        try:
            # 1. Carica e analizza dati
            df = self.load_and_analyze_data()
            
            # 2. Analizza pattern temporali
            df, hourly_dist, weekday_dist = self.analyze_timing_patterns(df)
            
            # 3. Analizza pattern rapid-fire
            df, rapid_fire, suspicious_sequences = self.analyze_rapid_fire_patterns(df)
            
            # 4. Analizza pattern contenuti
            df = self.analyze_content_patterns(df)
            
            # 5. Crea visualizzazione
            self.create_automation_visualization(df, hourly_dist, weekday_dist, rapid_fire)
            
            # 6. Genera valutazione finale
            self.generate_automation_assessment(df, rapid_fire, hourly_dist)
            
            print(f"\n🎉 ANALISI UMANO vs AUTOMAZIONE COMPLETATA PER @{self.username} - {self.year}!")
            print(f"📁 File creato: {self.output_filename}")
            
        except Exception as e:
            print(f"❌ Errore durante l'analisi: {e}")
            raise

def main():
    """
    Funzione principale.
    """
    parser = argparse.ArgumentParser(
        description="Analizza se l'attività è umana o automatizzata.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
ESEMPI:
    python3.11 analyze_human_vs_automation.py NTFabiano 2024
        """
    )
    
    parser.add_argument("username", help="Username Twitter (es. NTFabiano)")
    parser.add_argument("year", type=int, help="Anno da analizzare (es. 2024)")
    
    args = parser.parse_args()
    
    try:
        # Crea e esegui l'analyzer
        analyzer = HumanVsAutomationAnalyzer(args.username, args.year)
        analyzer.run()
        
    except Exception as e:
        print(f"❌ Errore fatale: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
