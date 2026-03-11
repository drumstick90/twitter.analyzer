#!/usr/bin/env python3
"""
Script per analizzare il pattern di crescita di @NTFabiano nel tempo.
Verifica se ha iniziato piano e poi ha aumentato l'intensità.

USAGE:
    python3.11 analyze_growth_escalation.py NTFabiano 2024
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime
import argparse
import os

class GrowthEscalationAnalyzer:
    """
    Classe per analizzare il pattern di escalation della crescita.
    """
    
    def __init__(self, username: str, year: int):
        self.username = username
        self.year = year
        self.calendar_file = f"calendar_2024_comparative_ntfabiano_vs_md_pier.csv"
        self.output_filename = f"{username}_{year}_growth_escalation_analysis.png"
        
        # Validazioni
        if not os.path.exists(self.calendar_file):
            raise FileNotFoundError(f"File {self.calendar_file} non trovato!")
        
        print(f"📈 ANALISI ESCALATION CRESCITA @{username} - {year}")
        print(f"📁 File calendario: {self.calendar_file}")
        print(f"📁 File output: {self.output_filename}")
        print("=" * 70)
    
    def load_and_analyze_data(self):
        """
        Carica e analizza i dati per verificare il pattern di escalation.
        """
        print("📊 Caricamento e analisi dati escalation...")
        
        # Carica calendario con attività
        calendar_df = pd.read_csv(self.calendar_file)
        print(f"   ✅ Calendario caricato: {len(calendar_df)} giorni")
        
        # Filtra solo dati NTFabiano attivi
        ntfabiano_df = calendar_df[calendar_df['has_activity'] == True].copy()
        print(f"   🎯 Giorni attivi NTFabiano: {len(ntfabiano_df)}")
        
        # Aggiungi colonne temporali
        ntfabiano_df['date'] = pd.to_datetime(ntfabiano_df['date_short'])
        ntfabiano_df['month'] = ntfabiano_df['date'].dt.month
        ntfabiano_df['week_of_year'] = ntfabiano_df['date'].dt.isocalendar().week
        ntfabiano_df['quarter'] = ntfabiano_df['date'].dt.quarter
        
        return ntfabiano_df
    
    def analyze_monthly_escalation(self, df: pd.DataFrame):
        """
        Analizza l'escalation mensile dell'attività.
        """
        print("📅 Analisi escalation mensile...")
        
        # Raggruppa per mese
        monthly_stats = df.groupby('month').agg({
            'tweets_singoli': 'sum',
            'thread_count': 'sum',
            'thread_tweets_total': 'sum',
            'tweets_totali': 'sum'
        }).reset_index()
        
        # Aggiungi nome mese
        month_names = ['Gen', 'Feb', 'Mar', 'Apr', 'Mag', 'Giu', 
                      'Lug', 'Ago', 'Set', 'Ott', 'Nov', 'Dic']
        monthly_stats['month_name'] = monthly_stats['month'].apply(lambda x: month_names[x-1])
        
        # Calcola trend di crescita
        monthly_stats['growth_rate'] = monthly_stats['tweets_totali'].pct_change() * 100
        
        print(f"   📊 ATTIVITÀ MENSILE:")
        for _, month in monthly_stats.iterrows():
            month_name = month['month_name']
            total = month['tweets_totali']
            singles = month['tweets_singoli']
            threads = month['thread_count']
            growth = month['growth_rate']
            
            if pd.isna(growth):
                growth_str = "N/A"
            else:
                growth_str = f"{growth:+.1f}%"
            
            print(f"      {month_name}: {total:3d} tweet ({singles:3d} singoli, {threads:2d} thread) - {growth_str}")
        
        return monthly_stats
    
    def analyze_quarterly_escalation(self, df: pd.DataFrame):
        """
        Analizza l'escalation trimestrale dell'attività.
        """
        print("📊 Analisi escalation trimestrale...")
        
        # Raggruppa per trimestre
        quarterly_stats = df.groupby('quarter').agg({
            'tweets_singoli': 'sum',
            'thread_count': 'sum',
            'thread_tweets_total': 'sum',
            'tweets_totali': 'sum'
        }).reset_index()
        
        # Calcola trend di crescita
        quarterly_stats['growth_rate'] = quarterly_stats['tweets_totali'].pct_change() * 100
        quarterly_stats['avg_daily'] = quarterly_stats['tweets_totali'] / [90, 91, 92, 92][:len(quarterly_stats)]
        
        print(f"   📈 ATTIVITÀ TRIMESTRALE:")
        for _, quarter in quarterly_stats.iterrows():
            q = quarter['quarter']
            total = quarter['tweets_totali']
            singles = quarter['tweets_singoli']
            threads = quarter['thread_count']
            growth = quarter['growth_rate']
            avg_daily = quarter['avg_daily']
            
            if pd.isna(growth):
                growth_str = "N/A"
            else:
                growth_str = f"{growth:+.1f}%"
            
            print(f"      Q{q}: {total:4.0f} tweet ({singles:4.0f} singoli, {threads:2.0f} thread) - {growth_str} - {avg_daily:.1f}/giorno")
        
        return quarterly_stats
    
    def analyze_weekly_escalation(self, df: pd.DataFrame):
        """
        Analizza l'escalation settimanale dell'attività.
        """
        print("📅 Analisi escalation settimanale...")
        
        # Raggruppa per settimana
        weekly_stats = df.groupby('week_of_year').agg({
            'tweets_singoli': 'sum',
            'thread_count': 'sum',
            'thread_tweets_total': 'sum',
            'tweets_totali': 'sum'
        }).reset_index()
        
        # Calcola trend di crescita
        weekly_stats['growth_rate'] = weekly_stats['tweets_totali'].pct_change() * 100
        
        # Trova settimane chiave
        first_week = weekly_stats.iloc[0]
        last_week = weekly_stats.iloc[-1]
        peak_week = weekly_stats.loc[weekly_stats['tweets_totali'].idxmax()]
        
        print(f"   🎯 SETTIMANE CHIAVE:")
        print(f"      Prima settimana: {first_week['tweets_totali']} tweet")
        print(f"      Ultima settimana: {last_week['tweets_totali']} tweet")
        print(f"      Settimana picco: {peak_week['tweets_totali']} tweet (settimana {peak_week['week_of_year']})")
        
        # Calcola escalation totale
        total_growth = ((last_week['tweets_totali'] - first_week['tweets_totali']) / first_week['tweets_totali']) * 100
        print(f"      Escalation totale: {total_growth:+.1f}%")
        
        return weekly_stats
    
    def create_escalation_visualization(self, monthly_stats: pd.DataFrame, quarterly_stats: pd.DataFrame, weekly_stats: pd.DataFrame):
        """
        Crea visualizzazione dell'escalation della crescita.
        """
        print("🎨 Creazione visualizzazione escalation...")
        
        # Crea figura con subplot
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 16))
        fig.suptitle(f'ANALISI ESCALATION CRESCITA @{self.username} - {self.year}\nPattern di Intensità Crescente nel Tempo', 
                     fontsize=20, fontweight='bold', y=0.98)
        
        # 1. Trend mensile
        months = range(len(monthly_stats))
        ax1.plot(months, monthly_stats['tweets_totali'], 'o-', linewidth=3, markersize=8, color='#2196F3')
        ax1.fill_between(months, monthly_stats['tweets_totali'], alpha=0.3, color='#2196F3')
        ax1.set_title('Escalation Mensile: Tweet Totali', fontsize=16, fontweight='bold')
        ax1.set_xlabel('Mese', fontsize=12)
        ax1.set_ylabel('Tweet Totali', fontsize=12)
        ax1.set_xticks(months)
        ax1.set_xticklabels(monthly_stats['month_name'])
        ax1.grid(True, alpha=0.3)
        
        # Aggiungi trend line
        z = np.polyfit(months, monthly_stats['tweets_totali'], 1)
        p = np.poly1d(z)
        ax1.plot(months, p(months), "--", color='red', alpha=0.8, linewidth=2, label=f'Trend: {z[0]:.1f}x + {z[1]:.1f}')
        ax1.legend()
        
        # 2. Trend trimestrale
        quarters = range(len(quarterly_stats))
        ax2.plot(quarters, quarterly_stats['tweets_totali'], 's-', linewidth=3, markersize=8, color='#4CAF50')
        ax2.fill_between(quarters, quarterly_stats['tweets_totali'], alpha=0.3, color='#4CAF50')
        ax2.set_title('Escalation Trimestrale: Tweet Totali', fontsize=16, fontweight='bold')
        ax2.set_xlabel('Trimestre', fontsize=12)
        ax2.set_ylabel('Tweet Totali', fontsize=12)
        ax2.set_xticks(quarters)
        ax2.set_xticklabels([f'Q{q}' for q in quarterly_stats['quarter']])
        ax2.grid(True, alpha=0.3)
        
        # Aggiungi trend line
        z = np.polyfit(quarters, quarterly_stats['tweets_totali'], 1)
        p = np.poly1d(z)
        ax2.plot(quarters, p(quarters), "--", color='red', alpha=0.8, linewidth=2, label=f'Trend: {z[0]:.1f}x + {z[1]:.1f}')
        ax2.legend()
        
        # 3. Trend settimanale
        weeks = range(len(weekly_stats))
        ax3.plot(weeks, weekly_stats['tweets_totali'], '^-', linewidth=2, markersize=6, color='#FF9800')
        ax3.set_title('Escalation Settimanale: Tweet Totali', fontsize=16, fontweight='bold')
        ax3.set_xlabel('Settimana dell\'Anno', fontsize=12)
        ax3.set_ylabel('Tweet Totali', fontsize=12)
        ax3.grid(True, alpha=0.3)
        
        # Aggiungi trend line
        z = np.polyfit(weeks, weekly_stats['tweets_totali'], 1)
        p = np.poly1d(z)
        ax3.plot(weeks, p(weeks), "--", color='red', alpha=0.8, linewidth=2, label=f'Trend: {z[0]:.1f}x + {z[1]:.1f}')
        ax3.legend()
        
        # 4. Confronto inizio vs fine anno
        ax4.axis('off')
        
        # Calcola statistiche confronto
        first_month = monthly_stats.iloc[0]
        last_month = monthly_stats.iloc[-1]
        first_quarter = quarterly_stats.iloc[0]
        last_quarter = quarterly_stats.iloc[-1]
        
        comparison_data = [
            ['METRICA', 'INIZIO ANNO', 'FINE ANNO', 'CRESCITA'],
            ['Tweet Mensili', f"{first_month['tweets_totali']}", f"{last_month['tweets_totali']}", 
             f"{((last_month['tweets_totali'] - first_month['tweets_totali']) / first_month['tweets_totali'] * 100):+.1f}%"],
            ['Tweet Trimestrali', f"{first_quarter['tweets_totali']}", f"{last_quarter['tweets_totali']}", 
             f"{((last_quarter['tweets_totali'] - first_quarter['tweets_totali']) / first_quarter['tweets_totali'] * 100):+.1f}%"],
            ['Media Giornaliera', f"{first_quarter['avg_daily']:.1f}", f"{last_quarter['avg_daily']:.1f}", 
             f"{((last_quarter['avg_daily'] - first_quarter['avg_daily']) / first_quarter['avg_daily'] * 100):+.1f}%"],
            ['Thread Mensili', f"{first_month['thread_count']}", f"{last_month['thread_count']}", 
             f"{((last_month['thread_count'] - first_month['thread_count']) / max(first_month['thread_count'], 1) * 100):+.1f}%"]
        ]
        
        table = ax4.table(cellText=comparison_data[1:], colLabels=comparison_data[0], 
                         cellLoc='center', loc='center', bbox=[0, 0, 1, 1])
        table.auto_set_font_size(False)
        table.set_fontsize(11)
        table.scale(1, 2.5)
        
        # Stile tabella
        for i in range(len(comparison_data)):
            for j in range(len(comparison_data[0])):
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
        print(f"   ✅ Visualizzazione escalation salvata: {self.output_filename}")
        
        return fig
    
    def generate_escalation_strategy(self, monthly_stats: pd.DataFrame, quarterly_stats: pd.DataFrame):
        """
        Genera strategia di escalation basata sui dati.
        """
        print("\n🚀 STRATEGIA ESCALATION RACCOMANDATA:")
        print("=" * 60)
        
        # Calcola trend di crescita
        first_month = monthly_stats.iloc[0]['tweets_totali']
        last_month = monthly_stats.iloc[-1]['tweets_totali']
        monthly_growth = ((last_month - first_month) / first_month) * 100
        
        first_quarter = quarterly_stats.iloc[0]['tweets_totali']
        last_quarter = quarterly_stats.iloc[-1]['tweets_totali']
        quarterly_growth = ((last_quarter - first_quarter) / first_quarter) * 100
        
        print(f"📈 PATTERN ESCALATION IDENTIFICATO:")
        print(f"   • Crescita mensile: {monthly_growth:+.1f}%")
        print(f"   • Crescita trimestrale: {quarterly_growth:+.1f}%")
        print()
        
        print(f"💡 STRATEGIA ESCALATION GRADUALE:")
        print(f"   • INIZIO ANNO: {first_month} tweet/mese (intensità bassa)")
        print(f"   • FINE ANNO: {last_month} tweet/mese (intensità alta)")
        print(f"   • AUMENTO GRADUALE: +{monthly_growth/12:.1f}% ogni mese")
        print()
        
        print(f"🎯 RACCOMANDAZIONI PER REPLICARE:")
        print(f"   • Inizia con {first_month//30:.0f} tweet/giorno")
        print(f"   • Aumenta gradualmente ogni mese")
        print(f"   • Raggiungi {last_month//30:.0f} tweet/giorno a fine anno")
        print(f"   • Mantieni il trend di crescita costante")
        print(f"   • Non fare tutto subito - escalation graduale è la chiave!")
    
    def run(self):
        """
        Esegue l'analisi completa dell'escalation della crescita.
        """
        try:
            # 1. Carica e analizza dati
            df = self.load_and_analyze_data()
            
            # 2. Analizza escalation mensile
            monthly_stats = self.analyze_monthly_escalation(df)
            
            # 3. Analizza escalation trimestrale
            quarterly_stats = self.analyze_quarterly_escalation(df)
            
            # 4. Analizza escalation settimanale
            weekly_stats = self.analyze_weekly_escalation(df)
            
            # 5. Crea visualizzazione
            self.create_escalation_visualization(monthly_stats, quarterly_stats, weekly_stats)
            
            # 6. Genera strategia escalation
            self.generate_escalation_strategy(monthly_stats, quarterly_stats)
            
            print(f"\n🎉 ANALISI ESCALATION CRESCITA COMPLETATA PER @{self.username} - {self.year}!")
            print(f"📁 File creato: {self.output_filename}")
            
        except Exception as e:
            print(f"❌ Errore durante l'analisi: {e}")
            raise

def main():
    """
    Funzione principale.
    """
    parser = argparse.ArgumentParser(
        description="Analizza il pattern di escalation della crescita nel tempo.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
ESEMPI:
    python3.11 analyze_growth_escalation.py NTFabiano 2024
        """
    )
    
    parser.add_argument("username", help="Username Twitter (es. NTFabiano)")
    parser.add_argument("year", type=int, help="Anno da analizzare (es. 2024)")
    
    args = parser.parse_args()
    
    try:
        # Crea e esegui l'analyzer
        analyzer = GrowthEscalationAnalyzer(args.username, args.year)
        analyzer.run()
        
    except Exception as e:
        print(f"❌ Errore fatale: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
