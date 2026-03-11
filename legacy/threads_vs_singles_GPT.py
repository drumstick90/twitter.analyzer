#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analisi Thread vs Post Singoli (schema X/Twitter: likeCount, retweetCount, replyCount, viewCount, createdAt, isReply, inReplyToId, conversationId)
- Input: directory con più .json o file singolo .json (array di tweet)
- Riconoscimento thread affidabile via conversationId:
    Un thread è un gruppo dove esiste un root (id == conversationId) non-reply dell'account,
    e ci sono >= 2 tweet dell'account nel gruppo.
- Esclude retweet (campo `retweeted_tweet` o testo "RT @").
- Calcola 2 ROI:
    1) ROI base = (engagement medio per tweet del thread) / (engagement medio dei post singoli)
    2) ROI rate = (ER thread = engagement/visualizzazioni) / (ER medio dei post singoli)
- Salva:
    - thread_analysis.csv
    - single_posts.csv
    - thread_vs_singles_report.json
    - thread_vs_singles_analysis.png (grafici)

USO:
    python analyze_threads.py <percorso_input> [--year 2025] [--user NTFabiano]

Esempi:
    python analyze_threads.py ./NTFabiano_tweets_analysis --year 2025 --user NTFabiano
    python analyze_threads.py ./ESEMPIO.json
"""

import os
import glob
import json
import argparse
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

import pandas as pd
import matplotlib.pyplot as plt


class ThreadAnalyzer:
    def __init__(self, input_path: str, year: Optional[int] = None, account_username: Optional[str] = None):
        self.input_path = input_path
        self.year = year
        self.account_username = account_username  # opzionale; se fornito, filtra autore
        self.tweets: List[Dict[str, Any]] = []
        self.threads: List[List[Dict[str, Any]]] = []
        self.single_posts: List[Dict[str, Any]] = []

    # -------------------- Helpers --------------------
    @staticmethod
    def parse_ts(ts: str) -> Optional[datetime]:
        """Ritorna datetime UTC-aware, o None."""
        if not ts or not isinstance(ts, str):
            return None
        # Formato classico Twitter: "Thu Jan 02 13:19:55 +0000 2025"
        try:
            return datetime.strptime(ts, '%a %b %d %H:%M:%S %z %Y').astimezone(timezone.utc)
        except Exception:
            pass
        # ISO-like: ...Z / +00:00
        try:
            ts2 = ts.replace('Z', '+00:00') if ts.endswith('Z') else ts
            return datetime.fromisoformat(ts2).astimezone(timezone.utc)
        except Exception:
            return None

    @staticmethod
    def is_retweet(tw: Dict[str, Any]) -> bool:
        if tw.get('retweeted_tweet'):
            return True
        txt = (tw.get('text') or '').strip().lower()
        if txt.startswith('rt @') or txt.startswith('rt:'):
            return True
        return False

    @staticmethod
    def get_like(tw: Dict[str, Any]) -> int:
        try:
            return int(tw.get('likeCount') or 0)
        except Exception:
            return 0

    @staticmethod
    def get_rt(tw: Dict[str, Any]) -> int:
        try:
            return int(tw.get('retweetCount') or tw.get('repostCount') or 0)
        except Exception:
            return 0

    @staticmethod
    def get_reply(tw: Dict[str, Any]) -> int:
        try:
            return int(tw.get('replyCount') or 0)
        except Exception:
            return 0

    @staticmethod
    def get_views(tw: Dict[str, Any]) -> int:
        try:
            return int(tw.get('viewCount') or 0)
        except Exception:
            return 0

    @staticmethod
    def author_username(tw: Dict[str, Any]) -> Optional[str]:
        a = tw.get('author') or {}
        return a.get('userName') or a.get('screen_name')
    
    def _is_valid_thread_tweet(self, tweet: Dict[str, Any], all_user_tweets: List[Dict[str, Any]]) -> bool:
        """
        Verifica se un tweet fa parte di un thread valido
        
        Criteri:
        1. Stesso utente (già verificato nel chiamante)
        2. Risposta a se stesso (inReplyToId punta a suo tweet precedente)
        3. Gap < 30 secondi
        """
        
        # 2. Risposta a se stesso
        reply_to_id = tweet.get('inReplyToId')
        if not reply_to_id:
            return False  # Non è una risposta
        
        # Trova il tweet a cui risponde
        replied_tweet = next((t for t in all_user_tweets if t.get('id') == reply_to_id), None)
        if not replied_tweet:
            return False  # Tweet non trovato
        
        # Verifica che sia dello stesso utente
        replied_username = self.author_username(replied_tweet)
        if not replied_username or replied_username.lower() != self.account_username.lower():
            return False  # Risponde a terzi
        
        # 3. Gap < 30 secondi
        tweet_time = self.parse_ts(tweet.get('createdAt') or tweet.get('created_at'))
        replied_time = self.parse_ts(replied_tweet.get('createdAt') or replied_tweet.get('created_at'))
        
        if not tweet_time or not replied_time:
            return False
        
        gap_seconds = (tweet_time - replied_time).total_seconds()
        return gap_seconds < 30  # Gap < 30 secondi

    # -------------------- IO --------------------
    def _load_file(self, file_path: str) -> List[Dict[str, Any]]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"❌ Errore caricando {file_path}: {e}")
            return []

        # Normalizza in lista di tweet
        if isinstance(data, list):
            tweets = data
        elif isinstance(data, dict):
            tweets = data.get('tweets') or data.get('data', {}).get('tweets') or data.get('items') or []
            if not isinstance(tweets, list):
                tweets = []
        else:
            tweets = []

        out = []
        for tw in tweets:
            if not isinstance(tw, dict):
                continue
            if self.is_retweet(tw):
                continue
            # filtro anno (opzionale)
            ts = self.parse_ts(tw.get('createdAt') or tw.get('created_at'))
            if self.year and (not ts or ts.year != self.year):
                continue
            # filtro autore (opzionale)
            if self.account_username:
                if (self.author_username(tw) or '').lower() != self.account_username.lower():
                    continue
            out.append(tw)

        print(f"✅ {os.path.basename(file_path)}: {len(out)} tweet utili")
        return out

    def load_data(self) -> bool:
        print("🔄 Caricamento dati...")
        if os.path.isdir(self.input_path):
            files = sorted(glob.glob(os.path.join(self.input_path, '*.json')))
            if not files:
                print("❌ Nessun file .json trovato nella cartella")
                return False
            for fp in files:
                self.tweets.extend(self._load_file(fp))
        else:
            # file singolo
            self.tweets.extend(self._load_file(self.input_path))

        print(f"📊 Totale tweet caricati: {len(self.tweets)}")
        return len(self.tweets) > 0

    # -------------------- Thread logic (conversationId) --------------------
    def identify_threads(self):
        """
        Raggruppa per conversationId e identifica thread validi.

        Definizione di THREAD (proprio dell'account):
          - Esiste un tweet "root" con id == conversationId
          - Il root è non-reply (isReply == False o inReplyToId mancante)
          - (Se --user è specificato) root e membri sono dello stesso autore
          - Numero di tweet dell'account nel gruppo >= 2
          
        CRITERI DI IDENTIFICAZIONE THREAD (CORRETTI):
          - Stesso utente (NTFabiano)
          - Tweet root SEMPRE incluso (inizio thread)
          - Tweet successivi: risposta a se stesso + gap < 30 secondi
          
        Gli altri tweet dell'account in conversazioni che non rispettano i criteri
        vengono conteggiati come post singoli.
        """
        print("🧵 Identificazione thread (via conversationId)...")

        if not self.tweets:
            print("❌ Nessun tweet da analizzare!")
            return

        by_id = {tw.get('id'): tw for tw in self.tweets}
        by_conv: Dict[str, List[Dict[str, Any]]] = {}
        for tw in self.tweets:
            cid = tw.get('conversationId')
            if not cid:
                # tweet senza conversationId → trattalo come singolo
                self.single_posts.append(tw)
                continue
            by_conv.setdefault(cid, []).append(tw)

        for conv_id, group in by_conv.items():
            root = by_id.get(conv_id)
            root_is_valid = False
            if root:
                root_is_valid = (not root.get('isReply', False)) and (root.get('inReplyToId') in (None, '', False))
                if self.account_username:
                    root_is_valid = root_is_valid and ((self.author_username(root) or '').lower() == self.account_username.lower())

            # limite ai soli tweet dell'account (se specificato)
            if self.account_username:
                mine = [tw for tw in group if (self.author_username(tw) or '').lower() == self.account_username.lower()]
            else:
                mine = group  # dataset monoutente

            if root and root_is_valid and len(mine) >= 2:
                # è un nostro thread - ora identifichiamo i tweet validi con la nuova logica
                mine_sorted = sorted(
                    mine,
                    key=lambda t: self.parse_ts(t.get('createdAt') or t.get('created_at')) or datetime.min.replace(tzinfo=timezone.utc)
                )
                
                # LOGICA CORRETTA: root sempre incluso + tweet validi
                valid_thread_tweets = [mine_sorted[0]]  # Il root è SEMPRE incluso
                
                # Aggiungi tweet che rispondono a se stesso con gap < 30s
                for tweet in mine_sorted[1:]:
                    if self._is_valid_thread_tweet(tweet, mine_sorted):
                        valid_thread_tweets.append(tweet)
                
                # Solo thread con almeno 2 tweet validi
                if len(valid_thread_tweets) >= 2:
                    self.threads.append(valid_thread_tweets)
                    # I tweet non validi diventano singoli
                    remaining_tweets = [tw for tw in mine_sorted if tw not in valid_thread_tweets]
                    self.single_posts.extend(remaining_tweets)
                else:
                    # Non è un thread valido → tutti i tweet sono singoli
                    self.single_posts.extend(mine_sorted)
            else:
                # non thread → i nostri tweet sono singoli
                self.single_posts.extend(mine)

        # dedup singoli (può succedere se gruppi si sovrappongono nei dati)
        seen = set()
        uniq = []
        for tw in self.single_posts:
            tid = tw.get('id')
            if tid not in seen:
                seen.add(tid)
                uniq.append(tw)
        self.single_posts = uniq

        print(f"🧵 Thread identificati: {len(self.threads)}")
        print(f"📝 Post singoli: {len(self.single_posts)}")
        if self.threads:
            lens = [len(t) for t in self.threads]
            media = sum(lens) / len(lens)
            print(f"📏 Lunghezza thread: min={min(lens)}, max={max(lens)}, media={media:.1f}")

    # -------------------- Analisi con ROI --------------------
    def analyze_engagement(self):
        """Analizza engagement e calcola ROI base & ROI rate (ER)."""
        print("📊 Analisi engagement con ROI...")

        # -------- 1) Post singoli: metriche + baseline --------
        single_post_stats = []
        for tw in self.single_posts:
            likes = self.get_like(tw)
            rts   = self.get_rt(tw)
            reps  = self.get_reply(tw)
            tot   = likes + rts + reps
            views = self.get_views(tw)
            text  = tw.get('text') or ''
            created_iso = (self.parse_ts(tw.get('createdAt')) or datetime.min.replace(tzinfo=timezone.utc)).isoformat()
            single_post_stats.append({
                'tweet_id': tw.get('id'),
                'likes': likes,
                'retweets': rts,
                'replies': reps,
                'total_engagement': tot,
                'views': views,
                'created_at': created_iso,
                'text': (text[:100] + '...') if len(text) > 100 else text,
                'url': tw.get('url') or tw.get('twitterUrl')
            })

        baseline_avg_eng_single = (
            sum(s['total_engagement'] for s in single_post_stats) / len(single_post_stats)
        ) if single_post_stats else 0.0

        total_views_singles = sum(s['views'] for s in single_post_stats)
        baseline_er_single = (
            (sum(s['total_engagement'] for s in single_post_stats) / total_views_singles)
            if total_views_singles > 0 else 0.0
        )

        # -------- 2) Thread: metriche + ROI --------
        thread_stats = []
        for i, thread in enumerate(self.threads):
            total_likes = sum(self.get_like(t) for t in thread)
            total_retweets = sum(self.get_rt(t) for t in thread)
            total_replies = sum(self.get_reply(t) for t in thread)
            total_engagement = total_likes + total_retweets + total_replies
            sum_views = sum(self.get_views(t) for t in thread)

            avg_likes_per_tweet = (total_likes / len(thread)) if thread else 0.0
            avg_eng_per_tweet = (total_engagement / len(thread)) if thread else 0.0
            er_thread = (total_engagement / sum_views) if sum_views > 0 else None

            roi_per_tweet = (
                (avg_eng_per_tweet / baseline_avg_eng_single)
                if baseline_avg_eng_single > 0 else None
            )
            roi_er = (
                (er_thread / baseline_er_single)
                if (er_thread is not None and baseline_er_single > 0) else None
            )

            first_ts = (self.parse_ts(thread[0].get('createdAt')) or datetime.min.replace(tzinfo=timezone.utc)).isoformat()
            last_ts  = (self.parse_ts(thread[-1].get('createdAt')) or datetime.min.replace(tzinfo=timezone.utc)).isoformat()

            # testo del root se presente, altrimenti il primo
            conv_id = thread[0].get('conversationId')
            root = None
            if conv_id:
                root = next((t for t in thread if t.get('id') == conv_id), None)
            root_text = (root or thread[0]).get('text', '')

            thread_stats.append({
                'thread_id': i + 1,
                'conversation_id': conv_id,
                'tweet_count': len(thread),
                'total_likes': total_likes,
                'total_retweets': total_retweets,
                'total_replies': total_replies,
                'total_engagement': total_engagement,
                'sum_views': sum_views,
                'avg_likes_per_tweet': avg_likes_per_tweet,
                'avg_engagement_per_tweet': avg_eng_per_tweet,
                'er_thread': er_thread,
                'roi_per_tweet_vs_singles': roi_per_tweet,  # ROI base
                'roi_er_vs_singles': roi_er,                # ROI rate (ER)
                'first_tweet_time': first_ts,
                'last_tweet_time': last_ts,
                'root_text': root_text
            })

        # -------- 3) Log e salvataggi --------
        if thread_stats:
            avg_thread_likes = sum(t['total_likes'] for t in thread_stats) / len(thread_stats)
            avg_thread_eng   = sum(t['total_engagement'] for t in thread_stats) / len(thread_stats)
            print(f"🧵 Thread - Media likes: {avg_thread_likes:.0f}, Media engagement: {avg_thread_eng:.0f}")

        if single_post_stats:
            avg_single_likes = sum(s['likes'] for s in single_post_stats) / len(single_post_stats)
            avg_single_eng   = sum(s['total_engagement'] for s in single_post_stats) / len(single_post_stats)
            print(f"📝 Singoli - Media likes: {avg_single_likes:.0f}, Media engagement: {avg_single_eng:.0f}")

        # ROI summary
        roi_base_vals = [t['roi_per_tweet_vs_singles'] for t in thread_stats if t['roi_per_tweet_vs_singles'] is not None]
        roi_er_vals   = [t['roi_er_vs_singles'] for t in thread_stats if t['roi_er_vs_singles'] is not None]
        if roi_base_vals:
            print(f"📈 ROI base medio (thread vs singoli): {sum(roi_base_vals)/len(roi_base_vals):.2f}")
        if roi_er_vals:
            print(f"📈 ROI rate medio (ER thread vs ER singoli): {sum(roi_er_vals)/len(roi_er_vals):.2f}")

        # CSV
        if thread_stats:
            pd.DataFrame(thread_stats).to_csv('thread_analysis.csv', index=False)
            print("💾 thread_analysis.csv salvato")
        if single_post_stats:
            pd.DataFrame(single_post_stats).to_csv('single_posts.csv', index=False)
            print("💾 single_posts.csv salvato")

        # JSON report con baseline + media ROI
        report = {
            'analysis_date': datetime.now(timezone.utc).isoformat(),
            'filters': {'year': self.year, 'account_username': self.account_username},
            'total_tweets': len(self.tweets),
            'threads_count': len(self.threads),
            'single_posts_count': len(self.single_posts),
            'baselines': {
                'avg_engagement_single': baseline_avg_eng_single,
                'engagement_rate_single': baseline_er_single
            },
            'roi_summary': {
                'roi_base_mean': (sum(roi_base_vals)/len(roi_base_vals)) if roi_base_vals else None,
                'roi_rate_mean': (sum(roi_er_vals)/len(roi_er_vals)) if roi_er_vals else None
            }
        }
        with open('thread_vs_singles_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print("💾 thread_vs_singles_report.json salvato")

        return thread_stats, single_post_stats

    # -------------------- Grafici --------------------
    def create_visualizations(self, thread_stats, single_post_stats, show_plot: bool = False):
        print("📈 Creazione visualizzazioni...")
        plt.style.use('default')
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Thread vs Post Singoli - Analisi Engagement', fontsize=16, fontweight='bold')

        # 1) Boxplot Likes/Engagement: Thread vs Singoli
        if thread_stats and single_post_stats:
            ax1 = axes[0, 0]
            ax1.boxplot(
                [[t['total_likes'] for t in thread_stats],
                 [s['likes'] for s in single_post_stats]],
                tick_labels=['Thread (tot likes)', 'Singoli (likes)']
            )
            ax1.set_title('Distribuzione Likes')
            ax1.grid(True, alpha=0.3)

        # 2) Engagement totale per thread
        if thread_stats:
            ax2 = axes[0, 1]
            ids = [f"T{i+1}" for i in range(len(thread_stats))]
            vals = [t['total_engagement'] for t in thread_stats]
            bars = ax2.bar(ids, vals, alpha=0.7)
            ax2.set_title('Engagement Totale per Thread')
            ax2.set_ylabel('Likes + RT + Replies')
            ax2.grid(True, alpha=0.3)
            if vals:
                maxv = max(vals)
                for b, v in zip(bars, vals):
                    if v > 0:
                        ax2.text(b.get_x()+b.get_width()/2, b.get_height()+maxv*0.01, f"{v:.0f}",
                                 ha='center', va='bottom', fontsize=8)

        # 3) Likes vs lunghezza thread
        if thread_stats:
            ax3 = axes[1, 0]
            ax3.scatter([t['tweet_count'] for t in thread_stats],
                        [t['total_likes'] for t in thread_stats], s=100, alpha=0.7)
            ax3.set_xlabel('Tweet per Thread')
            ax3.set_ylabel('Likes Totali')
            ax3.set_title('Likes vs Lunghezza Thread')
            ax3.grid(True, alpha=0.3)

        # 4) Distribuzione engagement singoli
        if single_post_stats:
            ax4 = axes[1, 1]
            ax4.hist([s['total_engagement'] for s in single_post_stats], bins=20, alpha=0.7, edgecolor='black')
            ax4.set_xlabel('Engagement Totale')
            ax4.set_ylabel('Frequenza')
            ax4.set_title('Distribuzione Engagement Singoli')
            ax4.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig('thread_vs_singles_analysis.png', dpi=300, bbox_inches='tight')
        print("📊 thread_vs_singles_analysis.png salvato")
        if show_plot:
            plt.show()

    # -------------------- Runner --------------------
    def run(self):
        print("🚀 Avvio analisi")
        print("=" * 60)
        if not self.load_data():
            return
        self.identify_threads()
        thread_stats, single_post_stats = self.analyze_engagement()
        self.create_visualizations(thread_stats, single_post_stats, show_plot=False)
        print("=" * 60)
        print(f"🧵 Thread: {len(self.threads)}  |  📝 Singoli: {len(self.single_posts)}  |  🧮 Totali: {len(self.tweets)}")


def main():
    ap = argparse.ArgumentParser(
        description="Analisi Thread vs Post Singoli (schema X/Twitter con conversationId: ROI base e ROI rate)."
    )
    ap.add_argument("input", help="Cartella con .json o file .json (array di tweet).")
    ap.add_argument("--year", type=int, default=None, help="Filtra per anno (es. 2025).")
    ap.add_argument("--user", type=str, default=None, help="Filtra per username autore (es. NTFabiano).")
    args = ap.parse_args()
    ThreadAnalyzer(args.input, year=args.year, account_username=args.user).run()


if __name__ == "__main__":
    main()
