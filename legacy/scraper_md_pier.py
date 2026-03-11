#!/usr/bin/env python3
"""
Twitter Scraper - scarica tutti i tweet di un utente (senza filtri di data)
"""

import requests
import json
import os
import time
import argparse
import sys
from datetime import datetime

def scrape_user_tweets(username, api_key):
    """
    Scarica tutti i tweet di un utente
    
    Args:
        username (str): Twitter username senza @
        api_key (str): API key
    """
    output_dir = f"{username}_tweets_analysis"
    
    print(f"🚀 Avvio scraping per @{username}")
    print(f"📁 Output: {output_dir}")
    
    # Crea directory di output
    os.makedirs(output_dir, exist_ok=True)
    
    # Parametri per la ricerca avanzata
    url = "https://api.twitterapi.io/twitter/tweet/advanced_search"
    search_query = f"from:{username}"
    query_type = "Latest"
    
    headers = {
        "X-API-KEY": api_key
    }
    
    page_number = 1
    cursor = None
    consecutive_empty_pages = 0
    max_consecutive_empty = 3
    
    while True:
        print(f"📄 Pagina {page_number:03d}...")
        
        querystring = {
            "query": search_query,
            "queryType": query_type
        }
        
        if cursor:
            querystring["cursor"] = cursor
        
        try:
            response = requests.get(url, headers=headers, params=querystring, timeout=30)
            
            if response.status_code != 200:
                print(f"❌ Errore API: {response.status_code}")
                break
            
            response_data = response.json()
            
            # Estrai i tweet
            if 'tweets' in response_data:
                tweets = response_data['tweets']
            elif 'data' in response_data and 'tweets' in response_data['data']:
                tweets = response_data['data']['tweets']
            else:
                tweets = []
            
            if not tweets:
                consecutive_empty_pages += 1
                print(f"⚠️ Pagina {page_number} vuota ({consecutive_empty_pages}/{max_consecutive_empty})")
                
                if consecutive_empty_pages >= max_consecutive_empty:
                    print("🛑 Fine paginazione")
                    break
            else:
                consecutive_empty_pages = 0
                print(f"✅ Trovati {len(tweets)} tweet")
            
            # Salva i tweet
            if tweets:
                output_file = os.path.join(output_dir, f"tweets_{username}_page_{page_number:03d}.json")
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(response_data, f, indent=2, ensure_ascii=False)
                
                print(f"💾 Salvato: {output_file}")
            
            # Controlla pagina successiva
            next_cursor = response_data.get('nextCursor')
            
            if not next_cursor or next_cursor == cursor:
                print("🏁 Fine paginazione")
                break
            
            cursor = next_cursor
            page_number += 1
            
            # Rate limiting
            time.sleep(1)
            
        except Exception as e:
            print(f"❌ Errore: {e}")
            break
    
    print(f"✅ Scraping completato per @{username}")
    print(f"📊 Pagine processate: {page_number - 1}")
    print(f"📁 Output salvato in: {output_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Scarica tutti i tweet di un utente Twitter (senza filtri di data)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Esempi:
  python scraper_md_pier.py md_pier
  python scraper_md_pier.py -u guruanaerobic
  python scraper_md_pier.py -u elonmusk --api-key YOUR_KEY
        """
    )
    
    parser.add_argument(
        'username_pos',
        nargs='?',
        metavar='username',
        help='Twitter username (senza @)'
    )
    
    parser.add_argument(
        '-u', '--username',
        help='Twitter username (alternativa all\'argomento posizionale)'
    )
    
    parser.add_argument(
        '--api-key',
        default="7ca4adac7ee14461995df707b9c2c8f2",
        help='Twitter API key (default: usa quella nello script)'
    )
    
    args = parser.parse_args()
    
    # Determina username (priorità a named argument)
    username = args.username or args.username_pos
    
    if not username:
        print("❌ ERROR: Username richiesto!")
        print("Esempi:")
        print("  python scraper_md_pier.py md_pier")
        print("  python scraper_md_pier.py -u guruanaerobic")
        sys.exit(1)
    
    api_key = args.api_key
    
    print(f"🚀 TWITTER SCRAPER")
    print(f"👤 Username: @{username}")
    print(f"🔑 API key: {api_key[:8]}...")
    
    # Esegui scraping
    scrape_user_tweets(username, api_key)
