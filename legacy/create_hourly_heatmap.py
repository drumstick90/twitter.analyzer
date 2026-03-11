#!/usr/bin/env python3
"""
Script per creare heatmap dalla matrice oraria dei tweet.
Genera visualizzazioni multiple e interattive dei pattern temporali.

USAGE:
    python3.11 create_hourly_heatmap.py <username> <year>

ESEMPIO:
    python3.11 create_hourly_heatmap.py NTFabiano 2024
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime
import argparse
import os

class HourlyHeatmapCreator:
    """
    Classe per creare heatmap dalla matrice oraria dei tweet.
    """
    
    def __init__(self, username: str, year: int):
        self.username = username
        self.year = year
        self.input_filename = f"{username}_{year}_hourly_matrix.csv"
        self.output_prefix = f"{username}_{year}_hourly_heatmap"
        
        # Validazioni
        if not os.path.exists(self.input_filename):
            raise FileNotFoundError(f"File {self.input_filename} non trovato!")
        
        print(f"🎨 CREAZIONE HEATMAP PER @{username} - {year}")
        print(f"📁 File input: {self.input_filename}")
        print("=" * 60)
    
    def load_data(self) -> pd.DataFrame:
        """
        Carica i dati dalla matrice oraria.
        """
        print("📊 Caricamento dati...")
        
        df = pd.read_csv(self.input_filename)
        print(f"   ✅ Dati caricati: {len(df)} giorni")
        
        # Filtra solo giorni con attività
        active_days = df[df['tweets_totali'] > 0].copy()
        print(f"   🎯 Giorni con attività: {len(active_days)}")
        
        return df, active_days
    
    def create_main_heatmap(self, df: pd.DataFrame):
        """
        Crea il heatmap principale: giorni vs ore.
        """
        print("🔥 Creazione heatmap principale...")
        
        # Prepara i dati per il heatmap
        hour_cols = [f'hour_{hour:02d}' for hour in range(24)]
        
        # Crea matrice per il heatmap
        heatmap_data = df[hour_cols].values
        
        # Crea figura
        fig, ax = plt.subplots(figsize=(20, 12))
        
        # Crea heatmap
        im = sns.heatmap(heatmap_data.T, 
                         cmap='YlOrRd', 
                         cbar_kws={'label': 'Numero Tweet'},
                         ax=ax)
        
        # Personalizza assi
        ax.set_title(f'Heatmap Attività Oraria @{self.username} - {self.year}', 
                     fontsize=18, fontweight='bold', pad=20)
        ax.set_xlabel('Giorni dell\'Anno', fontsize=14)
        ax.set_ylabel('Ore del Giorno', fontsize=14)
        
        # Personalizza y-axis (ore)
        y_ticks = range(24)
        y_labels = [f'{hour:02d}:00' for hour in y_ticks]
        ax.set_yticks(y_ticks)
        ax.set_yticklabels(y_labels)
        
        # Personalizza x-axis (giorni)
        x_ticks = np.linspace(0, len(df)-1, 12, dtype=int)
        x_labels = [df.iloc[i]['date_short'] for i in x_ticks]
        ax.set_xticks(x_ticks)
        ax.set_xticklabels(x_labels, rotation=45, ha='right')
        
        plt.tight_layout()
        
        # Salva
        filename = f"{self.output_prefix}_main.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"   ✅ Heatmap principale salvato: {filename}")
        
        return fig
    
    def create_monthly_heatmap(self, df: pd.DataFrame):
        """
        Crea heatmap aggregato per mese vs ore.
        """
        print("📅 Creazione heatmap mensile...")
        
        # Aggrega per mese
        monthly_data = df.groupby('month').agg({
            f'hour_{hour:02d}': 'sum' for hour in range(24)
        }).reset_index()
        
        # Prepara dati per heatmap
        hour_cols = [f'hour_{hour:02d}' for hour in range(24)]
        heatmap_data = monthly_data[hour_cols].values
        
        # Crea figura
        fig, ax = plt.subplots(figsize=(16, 8))
        
        # Crea heatmap
        im = sns.heatmap(heatmap_data.T, 
                         cmap='YlOrRd', 
                         cbar_kws={'label': 'Tweet Totali'},
                         ax=ax,
                         annot=True, 
                         fmt='.0f',
                         cbar=True)
        
        # Personalizza
        ax.set_title(f'Heatmap Mensile @{self.username} - {self.year}', 
                     fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel('Mese', fontsize=14)
        ax.set_ylabel('Ora', fontsize=14)
        
        # Personalizza assi
        month_names = ['Gen', 'Feb', 'Mar', 'Apr', 'Mag', 'Giu', 
                      'Lug', 'Ago', 'Set', 'Ott', 'Nov', 'Dic']
        ax.set_xticks(range(len(month_names)))
        ax.set_xticklabels(month_names)
        
        y_ticks = range(24)
        y_labels = [f'{hour:02d}:00' for hour in y_ticks]
        ax.set_yticks(y_ticks)
        ax.set_yticklabels(y_labels)
        
        plt.tight_layout()
        
        # Salva
        filename = f"{self.output_prefix}_monthly.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"   ✅ Heatmap mensile salvato: {filename}")
        
        return fig
    
    def create_weekday_heatmap(self, df: pd.DataFrame):
        """
        Crea heatmap per giorno della settimana vs ore.
        """
        print("📊 Creazione heatmap giorni settimana...")
        
        # Mappa giorni della settimana
        weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        weekday_map = {day: i for i, day in enumerate(weekday_order)}
        
        # Aggiungi colonna per ordinamento
        df['weekday_order'] = df['day_of_week'].map(weekday_map)
        
        # Aggrega per giorno della settimana
        weekday_data = df.groupby('weekday_order').agg({
            f'hour_{hour:02d}': 'mean' for hour in range(24)
        }).reset_index()
        
        # Riordina per giorno della settimana
        weekday_data = weekday_data.sort_values('weekday_order')
        
        # Prepara dati per heatmap
        hour_cols = [f'hour_{hour:02d}' for hour in range(24)]
        heatmap_data = weekday_data[hour_cols].values
        
        # Crea figura
        fig, ax = plt.subplots(figsize=(16, 8))
        
        # Crea heatmap
        im = sns.heatmap(heatmap_data, 
                         cmap='YlOrRd', 
                         cbar_kws={'label': 'Tweet Medi'},
                         ax=ax,
                         annot=True, 
                         fmt='.1f',
                         cbar=True)
        
        # Personalizza
        ax.set_title(f'Heatmap Giorni Settimana @{self.username} - {self.year}', 
                     fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel('Ora del Giorno', fontsize=14)
        ax.set_ylabel('Giorno della Settimana', fontsize=14)
        
        # Personalizza assi
        x_ticks = range(24)
        x_labels = [f'{hour:02d}:00' for hour in x_ticks]
        ax.set_xticks(x_ticks)
        ax.set_xticklabels(x_labels)
        
        y_ticks = range(7)
        y_labels = ['Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì', 'Sabato', 'Domenica']
        ax.set_yticks(y_ticks)
        ax.set_yticklabels(y_labels)
        
        plt.tight_layout()
        
        # Salva
        filename = f"{self.output_prefix}_weekday.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"   ✅ Heatmap giorni settimana salvato: {filename}")
        
        return fig
    
    def create_activity_patterns(self, df: pd.DataFrame):
        """
        Crea visualizzazioni per pattern di attività.
        """
        print("📈 Creazione pattern di attività...")
        
        # Crea figura con subplot multipli
        fig, axes = plt.subplots(2, 2, figsize=(20, 12))
        fig.suptitle(f'Pattern di Attività @{self.username} - {self.year}', 
                     fontsize=20, fontweight='bold')
        
        # 1. Ore più attive
        ax1 = axes[0, 0]
        hour_cols = [f'hour_{hour:02d}' for hour in range(24)]
        hourly_totals = df[hour_cols].sum()
        
        bars = ax1.bar(range(24), hourly_totals.values, color='#1f77b4', alpha=0.8)
        ax1.set_title('Tweet Totali per Ora', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Ora del Giorno', fontsize=12)
        ax1.set_ylabel('Tweet Totali', fontsize=12)
        ax1.set_xticks(range(24))
        ax1.set_xticklabels([f'{hour:02d}:00' for hour in range(24)], rotation=45)
        ax1.grid(True, alpha=0.3)
        
        # Evidenzia ore più attive
        top_hours = hourly_totals.nlargest(3)
        for hour, count in top_hours.items():
            hour_num = int(hour.split('_')[1])
            bars[hour_num].set_color('#ff7f0e')
            ax1.text(hour_num, count + max(hourly_totals) * 0.02, 
                     f'{count}', ha='center', va='bottom', fontweight='bold')
        
        # 2. Attività per giorno della settimana
        ax2 = axes[0, 1]
        weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        weekday_data = df.groupby('day_of_week')['tweets_totali'].sum().reindex(weekday_order)
        
        bars = ax2.bar(range(7), weekday_data.values, color='#2ca02c', alpha=0.8)
        ax2.set_title('Tweet Totali per Giorno della Settimana', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Giorno', fontsize=12)
        ax2.set_ylabel('Tweet Totali', fontsize=12)
        ax2.set_xticks(range(7))
        ax2.set_xticklabels(['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom'])
        ax2.grid(True, alpha=0.3)
        
        # 3. Attività per mese
        ax3 = axes[1, 0]
        monthly_data = df.groupby('month')['tweets_totali'].sum()
        month_names = ['Gen', 'Feb', 'Mar', 'Apr', 'Mag', 'Giu', 
                      'Lug', 'Ago', 'Set', 'Ott', 'Nov', 'Dic']
        
        bars = ax3.bar(range(12), monthly_data.values, color='#d62728', alpha=0.8)
        ax3.set_title('Tweet Totali per Mese', fontsize=14, fontweight='bold')
        ax3.set_xlabel('Mese', fontsize=12)
        ax3.set_ylabel('Tweet Totali', fontsize=12)
        ax3.set_xticks(range(12))
        ax3.set_xticklabels(month_names)
        ax3.grid(True, alpha=0.3)
        
        # 4. Distribuzione tweet per giorno
        ax4 = axes[1, 1]
        active_days = df[df['tweets_totali'] > 0]
        ax4.hist(active_days['tweets_totali'], bins=30, alpha=0.7, 
                edgecolor='black', color='#9467bd')
        ax4.set_title('Distribuzione Tweet per Giorno', fontsize=14, fontweight='bold')
        ax4.set_xlabel('Tweet per Giorno', fontsize=12)
        ax4.set_ylabel('Frequenza', fontsize=12)
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Salva
        filename = f"{self.output_prefix}_patterns.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"   ✅ Pattern di attività salvato: {filename}")
        
        return fig
    
    def create_comprehensive_heatmap(self, df: pd.DataFrame):
        """
        Crea un heatmap completo e dettagliato.
        """
        print("🎯 Creazione heatmap completo...")
        
        # Crea figura grande
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(24, 16))
        fig.suptitle(f'ANALISI COMPLETA ATTIVITÀ ORARIA @{self.username} - {self.year}', 
                     fontsize=22, fontweight='bold', y=0.98)
        
        # 1. Heatmap principale (giorni vs ore)
        hour_cols = [f'hour_{hour:02d}' for hour in range(24)]
        heatmap_data = df[hour_cols].values
        
        im1 = sns.heatmap(heatmap_data.T, 
                          cmap='YlOrRd', 
                          cbar_kws={'label': 'Tweet per Ora'},
                          ax=ax1,
                          cbar=True)
        
        ax1.set_title('Heatmap Attività Giornaliera: Giorni vs Ore', 
                      fontsize=18, fontweight='bold', pad=20)
        ax1.set_xlabel('Giorni dell\'Anno (1-366)', fontsize=14)
        ax1.set_ylabel('Ore del Giorno (00:00-23:00)', fontsize=14)
        
        # Personalizza assi
        y_ticks = range(24)
        y_labels = [f'{hour:02d}:00' for hour in y_ticks]
        ax1.set_yticks(y_ticks)
        ax1.set_yticklabels(y_labels)
        
        x_ticks = np.linspace(0, len(df)-1, 12, dtype=int)
        x_labels = [df.iloc[i]['date_short'] for i in x_ticks]
        ax1.set_xticks(x_ticks)
        ax1.set_xticklabels(x_labels, rotation=45, ha='right')
        
        # 2. Heatmap aggregato mensile
        monthly_data = df.groupby('month').agg({
            f'hour_{hour:02d}': 'sum' for hour in range(24)
        }).reset_index()
        
        monthly_heatmap = monthly_data[hour_cols].values
        
        im2 = sns.heatmap(monthly_heatmap.T, 
                          cmap='YlOrRd', 
                          cbar_kws={'label': 'Tweet Totali per Mese'},
                          ax=ax2,
                          annot=True, 
                          fmt='.0f',
                          cbar=True)
        
        ax2.set_title('Heatmap Mensile Aggregato: Mesi vs Ore', 
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
        
        plt.tight_layout()
        
        # Salva
        filename = f"{self.output_prefix}_comprehensive.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"   ✅ Heatmap completo salvato: {filename}")
        
        return fig
    
    def run(self):
        """
        Esegue la creazione di tutti i heatmap.
        """
        try:
            # Carica dati
            df, active_days = self.load_data()
            
            # Crea tutti i tipi di heatmap
            print("\n🎨 CREAZIONE HEATMAP...")
            
            # 1. Heatmap principale
            self.create_main_heatmap(df)
            
            # 2. Heatmap mensile
            self.create_monthly_heatmap(df)
            
            # 3. Heatmap giorni settimana
            self.create_weekday_heatmap(df)
            
            # 4. Pattern di attività
            self.create_activity_patterns(df)
            
            # 5. Heatmap completo
            self.create_comprehensive_heatmap(df)
            
            print(f"\n🎉 TUTTI GLI HEATMAP COMPLETATI PER @{self.username} - {self.year}!")
            print(f"📁 File creati:")
            print(f"   🔥 {self.output_prefix}_main.png")
            print(f"   📅 {self.output_prefix}_monthly.png")
            print(f"   📊 {self.output_prefix}_weekday.png")
            print(f"   📈 {self.output_prefix}_patterns.png")
            print(f"   🎯 {self.output_prefix}_comprehensive.png")
            
        except Exception as e:
            print(f"❌ Errore durante la creazione: {e}")
            raise

def main():
    """
    Funzione principale.
    """
    parser = argparse.ArgumentParser(
        description="Crea heatmap dalla matrice oraria dei tweet.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
ESEMPI:
    python3.11 create_hourly_heatmap.py NTFabiano 2024
    python3.11 create_hourly_heatmap.py md_pier 2024
        """
    )
    
    parser.add_argument("username", help="Username Twitter (es. NTFabiano)")
    parser.add_argument("year", type=int, help="Anno da analizzare (es. 2024)")
    
    args = parser.parse_args()
    
    try:
        # Crea e esegui il creator
        creator = HourlyHeatmapCreator(args.username, args.year)
        creator.run()
        
    except Exception as e:
        print(f"❌ Errore fatale: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
