#!/usr/bin/env python3
"""
Script per analizzare l'evoluzione del contenuto di @md_pier nel tempo.
Traccia cambiamenti di temi, linguaggio, engagement e pattern di contenuto.

USAGE:
    python3.11 analyze_md_pier_evolution.py
"""

import pandas as pd
import json
import os
import re
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from collections import Counter

class MDPierEvolutionAnalyzer:
    """
    Classe per analizzare l'evoluzione del contenuto di @md_pier nel tempo.
    """
    
    def __init__(self):
        self.md_pier_dir = "md_pier_tweets_analysis"
        self.output_filename = "md_pier_content_evolution_analysis.png"
        
        # Validazioni
        if not os.path.exists(self.md_pier_dir):
            raise FileNotFoundError(f"Directory {self.md_pier_dir} non trovata!")
        
        print(f"📈 ANALISI EVOLUZIONE CONTENUTO @md_pier")
        print(f"📁 Directory: {self.md_pier_dir}")
        print(f"📁 File output: {self.output_filename}")
        print("=" * 70)
        
        # Temi e categorie di contenuto
        self.content_themes = {
            'medical': ['psychiatry', 'psychology', 'medicine', 'clinical', 'patient', 'treatment', 'diagnosis', 'symptoms', 'medication', 'therapy', 'mental health', 'depression', 'anxiety', 'bipolar', 'schizophrenia', 'antidepressant', 'antipsychotic', 'psychopharmacology'],
            'scientific': ['research', 'study', 'paper', 'publication', 'data', 'analysis', 'statistics', 'evidence', 'clinical trial', 'meta-analysis', 'systematic review', 'peer-reviewed', 'journal', 'conference', 'presentation'],
            'technology': ['AI', 'artificial intelligence', 'machine learning', 'algorithm', 'software', 'app', 'digital', 'online', 'platform', 'tool', 'system', 'automation', 'chatbot', 'GPT', 'LLM', 'neural network'],
            'social_media': ['twitter', 'social media', 'platform', 'content', 'engagement', 'followers', 'viral', 'trending', 'hashtag', 'mention', 'retweet', 'like', 'share'],
            'politics': ['politics', 'political', 'government', 'policy', 'election', 'democracy', 'authority', 'power', 'corruption', 'scandal', 'protest', 'activism', 'freedom', 'rights'],
            'philosophy': ['philosophy', 'philosophical', 'ethics', 'morality', 'values', 'beliefs', 'ideology', 'theory', 'concept', 'principle', 'wisdom', 'knowledge', 'truth', 'reality'],
            'personal': ['I', 'me', 'my', 'personal', 'experience', 'opinion', 'think', 'believe', 'feel', 'hope', 'wish', 'dream', 'goal', 'life', 'family', 'friend']
        }
        
        # Lingue rilevate
        self.languages = {
            'english': ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'about', 'against', 'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below'],
            'italian': ['il', 'la', 'lo', 'gli', 'le', 'di', 'da', 'in', 'con', 'su', 'per', 'tra', 'fra', 'senza', 'contro', 'dopo', 'prima', 'sopra', 'sotto', 'dentro', 'fuori', 'vicino', 'lontano'],
            'spanish': ['el', 'la', 'los', 'las', 'de', 'del', 'en', 'con', 'por', 'para', 'sin', 'contra', 'después', 'antes', 'sobre', 'bajo', 'dentro', 'fuera', 'cerca', 'lejos'],
            'french': ['le', 'la', 'les', 'de', 'du', 'des', 'en', 'avec', 'pour', 'par', 'sans', 'contre', 'après', 'avant', 'sur', 'sous', 'dans', 'hors', 'près', 'loin']
        }
    
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
                        
                        if year not in tweets_by_year:
                            tweets_by_year[year] = []
                        tweets_by_year[year].extend(tweets)
                        
                    except Exception as e:
                        print(f"   ❌ Errore caricamento {filename}: {e}")
        
        # Mostra statistiche per anno
        for year in sorted(tweets_by_year.keys()):
            print(f"   ✅ {year}: {len(tweets_by_year[year])} tweet caricati")
        
        return tweets_by_year
    
    def analyze_content_themes(self, tweets: list):
        """
        Analizza i temi di contenuto per un anno specifico.
        """
        theme_counts = {theme: 0 for theme in self.content_themes.keys()}
        total_tweets = len(tweets)
        
        for tweet in tweets:
            text = tweet.get('text', '').lower()
            if not text:
                continue
            
            # Conta occorrenze per ogni tema
            for theme, keywords in self.content_themes.items():
                for keyword in keywords:
                    if keyword.lower() in text:
                        theme_counts[theme] += 1
                        break  # Un tweet può essere classificato in un solo tema
        
        # Calcola percentuali
        theme_percentages = {theme: (count/total_tweets)*100 for theme, count in theme_counts.items()}
        
        return theme_counts, theme_percentages
    
    def analyze_language_usage(self, tweets: list):
        """
        Analizza l'uso delle lingue per un anno specifico.
        """
        language_counts = {lang: 0 for lang in self.languages.keys()}
        total_tweets = len(tweets)
        
        for tweet in tweets:
            text = tweet.get('text', '').lower()
            if not text:
                continue
            
            # Conta parole per ogni lingua
            for lang, words in self.languages.items():
                word_count = sum(1 for word in words if word.lower() in text.split())
                if word_count > 0:
                    language_counts[lang] += 1
        
        # Calcola percentuali
        language_percentages = {lang: (count/total_tweets)*100 for lang, count in language_counts.items()}
        
        return language_counts, language_percentages
    
    def analyze_engagement_evolution(self, tweets: list):
        """
        Analizza l'evoluzione dell'engagement per un anno specifico.
        """
        if not tweets:
            return 0, 0, 0, 0
        
        likes = [tweet.get('likeCount', 0) for tweet in tweets]
        retweets = [tweet.get('retweetCount', 0) for tweet in tweets]
        replies = [tweet.get('replyCount', 0) for tweet in tweets]
        
        avg_likes = np.mean(likes) if likes else 0
        avg_retweets = np.mean(retweets) if retweets else 0
        avg_replies = np.mean(replies) if replies else 0
        total_engagement = avg_likes + avg_retweets + avg_replies
        
        return avg_likes, avg_retweets, avg_replies, total_engagement
    
    def analyze_content_patterns(self, tweets: list):
        """
        Analizza i pattern di contenuto per un anno specifico.
        """
        patterns = {
            'hashtags': 0,
            'mentions': 0,
            'urls': 0,
            'long_tweets': 0,
            'questions': 0,
            'emojis': 0
        }
        
        total_tweets = len(tweets)
        
        for tweet in tweets:
            text = tweet.get('text', '')
            if not text:
                continue
            
            # Conta hashtag
            if '#' in text:
                patterns['hashtags'] += 1
            
            # Conta menzioni
            if '@' in text:
                patterns['mentions'] += 1
            
            # Conta URL
            if 'http' in text:
                patterns['urls'] += 1
            
            # Tweet lunghi (>200 caratteri)
            if len(text) > 200:
                patterns['long_tweets'] += 1
            
            # Domande
            if '?' in text:
                patterns['questions'] += 1
            
            # Emoji
            if any(ord(char) > 127 for char in text):
                patterns['emojis'] += 1
        
        # Calcola percentuali
        pattern_percentages = {pattern: (count/total_tweets)*100 for pattern, count in patterns.items()}
        
        return patterns, pattern_percentages
    
    def create_evolution_visualization(self, evolution_data: dict):
        """
        Crea visualizzazione dell'evoluzione del contenuto.
        """
        print("🎨 Creazione visualizzazione evoluzione...")
        
        # Crea figura con subplot
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 16))
        fig.suptitle(f'EVOLUZIONE CONTENUTO @md_pier NEL TEMPO\nAnalisi Temi, Lingue, Engagement e Pattern', 
                     fontsize=20, fontweight='bold', y=0.98)
        
        years = sorted(evolution_data.keys())
        
        # 1. Evoluzione temi di contenuto
        themes = list(self.content_themes.keys())
        theme_data = {theme: [evolution_data[year]['themes'][theme] for year in years] for theme in themes}
        
        x = np.arange(len(years))
        width = 0.15
        
        for i, theme in enumerate(themes):
            ax1.bar(x + i*width, theme_data[theme], width, label=theme.replace('_', ' ').title(), alpha=0.8)
        
        ax1.set_title('Evoluzione Temi di Contenuto', fontsize=16, fontweight='bold')
        ax1.set_xlabel('Anno', fontsize=12)
        ax1.set_ylabel('Percentuale Tweet', fontsize=12)
        ax1.set_xticks(x + width * (len(themes)-1)/2)
        ax1.set_xticklabels(years)
        ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax1.grid(True, alpha=0.3)
        
        # 2. Evoluzione lingue
        languages = list(self.languages.keys())
        lang_data = {lang: [evolution_data[year]['languages'][lang] for year in years] for lang in languages}
        
        for i, lang in enumerate(languages):
            ax2.plot(years, lang_data[lang], 'o-', linewidth=2, markersize=6, label=lang.title())
        
        ax2.set_title('Evoluzione Uso Lingue', fontsize=16, fontweight='bold')
        ax2.set_xlabel('Anno', fontsize=12)
        ax2.set_ylabel('Percentuale Tweet', fontsize=12)
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 3. Evoluzione engagement
        engagement_metrics = ['likes', 'retweets', 'replies', 'total']
        engagement_data = {metric: [evolution_data[year]['engagement'][metric] for year in years] for metric in engagement_metrics}
        
        for i, metric in enumerate(engagement_metrics):
            ax3.plot(years, engagement_data[metric], 's-', linewidth=2, markersize=6, label=metric.title())
        
        ax3.set_title('Evoluzione Engagement', fontsize=16, fontweight='bold')
        ax3.set_xlabel('Anno', fontsize=12)
        ax3.set_ylabel('Media per Tweet', fontsize=12)
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # 4. Evoluzione pattern di contenuto
        patterns = list(evolution_data[years[0]]['patterns'].keys())
        pattern_data = {pattern: [evolution_data[year]['patterns'][pattern] for year in years] for pattern in patterns}
        
        x = np.arange(len(years))
        width = 0.15
        
        for i, pattern in enumerate(patterns):
            ax4.bar(x + i*width, pattern_data[pattern], width, label=pattern.replace('_', ' ').title(), alpha=0.8)
        
        ax4.set_title('Evoluzione Pattern di Contenuto', fontsize=16, fontweight='bold')
        ax4.set_xlabel('Anno', fontsize=12)
        ax4.set_ylabel('Percentuale Tweet', fontsize=12)
        ax4.set_xticks(x + width * (len(patterns)-1)/2)
        ax4.set_xticklabels(years)
        ax4.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Salva
        plt.savefig(self.output_filename, dpi=300, bbox_inches='tight')
        print(f"   ✅ Visualizzazione evoluzione salvata: {self.output_filename}")
        
        return fig
    
    def generate_evolution_summary(self, evolution_data: dict):
        """
        Genera riepilogo dell'evoluzione del contenuto.
        """
        print("\n📈 RIEPILOGO EVOLUZIONE CONTENUTO @md_pier:")
        print("=" * 70)
        
        years = sorted(evolution_data.keys())
        
        print(f"📊 ANALISI TEMPORALE: {years[0]} - {years[-1]}")
        print()
        
        # Analisi temi
        print(f"🎯 EVOLUZIONE TEMI:")
        themes = list(self.content_themes.keys())
        for theme in themes:
            theme_values = [evolution_data[year]['themes'][theme] for year in years]
            trend = "↗️" if theme_values[-1] > theme_values[0] else "↘️" if theme_values[-1] < theme_values[0] else "➡️"
            change = theme_values[-1] - theme_values[0]
            print(f"   {theme.replace('_', ' ').title()}: {theme_values[0]:.1f}% → {theme_values[-1]:.1f}% {trend} ({change:+.1f}%)")
        
        print()
        
        # Analisi lingue
        print(f"🌍 EVOLUZIONE LINGUE:")
        languages = list(self.languages.keys())
        for lang in languages:
            lang_values = [evolution_data[year]['languages'][lang] for year in years]
            trend = "↗️" if lang_values[-1] > lang_values[0] else "↘️" if lang_values[-1] < lang_values[0] else "➡️"
            change = lang_values[-1] - lang_values[0]
            print(f"   {lang.title()}: {lang_values[0]:.1f}% → {lang_values[-1]:.1f}% {trend} ({change:+.1f}%)")
        
        print()
        
        # Analisi engagement
        print(f"📈 EVOLUZIONE ENGAGEMENT:")
        engagement_metrics = ['likes', 'retweets', 'replies', 'total']
        for metric in engagement_metrics:
            metric_values = [evolution_data[year]['engagement'][metric] for year in years]
            trend = "↗️" if metric_values[-1] > metric_values[0] else "↘️" if metric_values[-1] < metric_values[0] else "➡️"
            change = metric_values[-1] - metric_values[0]
            print(f"   {metric.title()}: {metric_values[0]:.1f} → {metric_values[-1]:.1f} {trend} ({change:+.1f})")
        
        print()
        
        # Analisi pattern
        print(f"🔍 EVOLUZIONE PATTERN:")
        patterns = list(evolution_data[years[0]]['patterns'].keys())
        for pattern in patterns:
            pattern_values = [evolution_data[year]['patterns'][pattern] for year in years]
            trend = "↗️" if pattern_values[-1] > pattern_values[0] else "↘️" if pattern_values[-1] < pattern_values[0] else "➡️"
            change = pattern_values[-1] - pattern_values[0]
            print(f"   {pattern.replace('_', ' ').title()}: {pattern_values[0]:.1f}% → {pattern_values[-1]:.1f}% {trend} ({change:+.1f}%)")
        
        print()
        
        # Tendenze principali
        print(f"💡 TENDENZE PRINCIPALI:")
        
        # Tema più cresciuto
        theme_growth = {}
        for theme in themes:
            theme_values = [evolution_data[year]['themes'][theme] for year in years]
            theme_growth[theme] = theme_values[-1] - theme_values[0]
        
        fastest_growing_theme = max(theme_growth, key=theme_growth.get)
        fastest_declining_theme = min(theme_growth, key=theme_growth.get)
        
        print(f"   🚀 Tema in crescita: {fastest_growing_theme.replace('_', ' ').title()} (+{theme_growth[fastest_growing_theme]:.1f}%)")
        print(f"   📉 Tema in declino: {fastest_declining_theme.replace('_', ' ').title()} ({theme_growth[fastest_declining_theme]:+.1f}%)")
        
        # Lingua più usata
        lang_usage = {}
        for lang in languages:
            lang_values = [evolution_data[year]['languages'][lang] for year in years]
            lang_usage[lang] = np.mean(lang_values)
        
        most_used_lang = max(lang_usage, key=lang_usage.get)
        print(f"   🌍 Lingua principale: {most_used_lang.title()} ({lang_usage[most_used_lang]:.1f}% media)")
        
        # Engagement trend
        total_engagement_values = [evolution_data[year]['engagement']['total'] for year in years]
        engagement_trend = "crescente" if total_engagement_values[-1] > total_engagement_values[0] else "decrescente" if total_engagement_values[-1] < total_engagement_values[0] else "stabile"
        print(f"   📊 Engagement: {engagement_trend} ({total_engagement_values[0]:.1f} → {total_engagement_values[-1]:.1f})")
    
    def run(self):
        """
        Esegue l'analisi completa dell'evoluzione del contenuto.
        """
        try:
            # 1. Carica tweet per anno
            tweets_by_year = self.load_tweets_by_year()
            
            if not tweets_by_year:
                print("❌ Nessun tweet trovato!")
                return
            
            # 2. Analizza ogni anno
            evolution_data = {}
            
            for year in sorted(tweets_by_year.keys()):
                print(f"\n📅 ANALISI ANNO {year}:")
                print("=" * 50)
                
                tweets = tweets_by_year[year]
                
                # Analizza temi
                theme_counts, theme_percentages = self.analyze_content_themes(tweets)
                print(f"   🎯 Temi: {theme_percentages}")
                
                # Analizza lingue
                lang_counts, lang_percentages = self.analyze_language_usage(tweets)
                print(f"   🌍 Lingue: {lang_percentages}")
                
                # Analizza engagement
                avg_likes, avg_retweets, avg_replies, total_engagement = self.analyze_engagement_evolution(tweets)
                print(f"   📊 Engagement: Likes={avg_likes:.1f}, RT={avg_retweets:.1f}, Replies={avg_replies:.1f}, Tot={total_engagement:.1f}")
                
                # Analizza pattern
                patterns, pattern_percentages = self.analyze_content_patterns(tweets)
                print(f"   🔍 Pattern: {pattern_percentages}")
                
                # Salva dati
                evolution_data[year] = {
                    'themes': theme_percentages,
                    'languages': lang_percentages,
                    'engagement': {
                        'likes': avg_likes,
                        'retweets': avg_retweets,
                        'replies': avg_replies,
                        'total': total_engagement
                    },
                    'patterns': pattern_percentages
                }
            
            # 3. Crea visualizzazione
            self.create_evolution_visualization(evolution_data)
            
            # 4. Genera riepilogo
            self.generate_evolution_summary(evolution_data)
            
            print(f"\n🎉 ANALISI EVOLUZIONE COMPLETATA PER @md_pier!")
            print(f"📁 File creato: {self.output_filename}")
            
        except Exception as e:
            print(f"❌ Errore durante l'analisi: {e}")
            raise

def main():
    """
    Funzione principale.
    """
    try:
        # Crea e esegui l'analyzer
        analyzer = MDPierEvolutionAnalyzer()
        analyzer.run()
        
    except Exception as e:
        print(f"❌ Errore fatale: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

