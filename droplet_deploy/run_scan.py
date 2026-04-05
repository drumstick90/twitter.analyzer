import json
import os
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data.scraper import scrape_multi_user_24h
from dotenv import load_dotenv

def main():
    load_dotenv()
    
    config_path = Path("config.json")
    if not config_path.exists():
        print("Error: config.json not found.")
        sys.exit(1)
        
    with open(config_path, "r") as f:
        config = json.load(f)
        
    usernames = config.get("usernames", [])
    if not usernames:
        print("Error: No usernames found in config.json.")
        sys.exit(1)
        
    api_key = os.getenv("TWITTERAPI_KEY")
    if not api_key:
        print("Error: TWITTERAPI_KEY not found in environment variables.")
        sys.exit(1)
        
    print(f"Starting 24h scan for {len(usernames)} users...")
    
    # scrape_multi_user_24h hardcodes the output directory to datasets/24h_accrued
    # We can rely on that, or modify scraper.py. For now, let's rely on it as it matches the agenti expectation.
    results = scrape_multi_user_24h(usernames, api_key, include_thread_context=True)
    
    print("Scan completed.")
    for r in results:
        status = r.get("status")
        count = r.get("tweet_count", 0)
        user = r.get("username")
        print(f"  @{user}: {status} ({count} tweets)")

if __name__ == "__main__":
    main()
