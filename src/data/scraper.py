import calendar
import glob
import requests
import json
import os
import time
from datetime import date, datetime, timedelta

class ScraperState:
    def __init__(self):
        self.stop_requested = False

    def stop(self):
        self.stop_requested = True
    
    def reset(self):
        self.stop_requested = False

# Global state
scraper_state = ScraperState()


def _paginate_advanced_search(api_key, search_query, project_dir, file_stem_prefix):
    """
    Run one advanced-search query with cursor pagination.

    Saves pages as {file_stem_prefix}_page_{NNN}.json under project_dir.
    Each file contains only tweets whose id had not appeared in earlier pages
    for this query (deduped). Stops early if a page returns tweets but none are
    new — avoids burning pages/credits when the API repeats the same window.

    Returns (total_unique_tweets_saved, pages_fetched_from_api, success).
    """
    url = "https://api.twitterapi.io/twitter/tweet/advanced_search"
    headers = {"X-API-Key": api_key}
    query_type = "Latest"

    print(f"Search query: {search_query}")
    print(f"Query type: {query_type}")

    cursor = ""
    has_next_page = True
    page_number = 1
    total_tweets = 0
    total_pages = 0
    delay_between_requests = 1
    consecutive_empty_pages = 0
    max_consecutive_empty = 3
    consecutive_duplicate_only_pages = 0
    max_consecutive_duplicate_only = 8
    seen_ids = set()

    while has_next_page:
        if scraper_state.stop_requested:
            print("\n🛑 SCRAPING STOPPED BY USER")
            return total_tweets, total_pages, False

        print(f"\n--- Fetching Page {page_number} ---")
        print(f"Using cursor: '{cursor}'")

        querystring = {
            "query": search_query,
            "queryType": query_type,
            "cursor": cursor,
        }

        try:
            response = requests.get(url, headers=headers, params=querystring)

            if response.status_code != 200:
                print(f"❌ HTTP Error {response.status_code}: {response.text}")
                return total_tweets, total_pages, False

            response_data = response.json()

            if "error" in response_data:
                print(f"❌ API Error: {response_data.get('message', 'Unknown error')}")
                return total_tweets, total_pages, False

            if response_data.get("tweets") is None:
                print(f"❌ Unexpected response format: {response_data}")
                return total_tweets, total_pages, False

            tweets_on_page = response_data["tweets"]
            total_pages += 1

            print(f"📊 Tweets received on this page: {len(tweets_on_page)}")

            if tweets_on_page and len(tweets_on_page) > 0:
                consecutive_empty_pages = 0

                new_tweets = []
                for t in tweets_on_page:
                    if not isinstance(t, dict):
                        continue
                    tid = t.get("id") or t.get("id_str")
                    if tid is None:
                        continue
                    sid = str(tid)
                    if sid in seen_ids:
                        continue
                    seen_ids.add(sid)
                    new_tweets.append(t)

                if len(new_tweets) == 0:
                    # Overlap-only page: do not stop until cursor cannot advance, or too many
                    # consecutive overlap pages (API stuck). Earlier bug: we stopped here and never
                    # advanced the cursor, so months with >1 page of results were truncated.
                    consecutive_duplicate_only_pages += 1
                    next_cursor = response_data.get("next_cursor", "")
                    print(
                        f"⚠️  No new tweet ids on this page ({len(tweets_on_page)} rows all already seen). "
                        f"Overlap pass {consecutive_duplicate_only_pages}/{max_consecutive_duplicate_only}."
                    )
                    if next_cursor and next_cursor != cursor:
                        cursor = next_cursor
                        print(f"🔗 Advancing cursor anyway; fetching next window...")
                        if consecutive_duplicate_only_pages >= max_consecutive_duplicate_only:
                            print(
                                "🔚 Stopping: too many consecutive overlap-only pages "
                                f"({max_consecutive_duplicate_only}). Possible API loop."
                            )
                            has_next_page = False
                        else:
                            print(
                                f"⏳ Waiting {delay_between_requests} seconds before next request..."
                            )
                            time.sleep(delay_between_requests)
                    else:
                        print(
                            "🔚 Stopping: overlap-only page and cursor empty or unchanged "
                            "(no further pages)."
                        )
                        has_next_page = False
                else:
                    consecutive_duplicate_only_pages = 0
                    if len(new_tweets) < len(tweets_on_page):
                        print(
                            f"   ({len(new_tweets)} new, "
                            f"{len(tweets_on_page) - len(new_tweets)} duplicate ids skipped)"
                        )

                    file_path = os.path.join(
                        project_dir, f"{file_stem_prefix}_page_{page_number:03d}.json"
                    )
                    with open(file_path, "w", encoding="utf-8") as f:
                        json.dump(new_tweets, f, indent=2, ensure_ascii=False)

                    print(f"💾 Saved {len(new_tweets)} new tweets to {file_path}")
                    total_tweets += len(new_tweets)

                    has_next_page = response_data.get("has_next_page", False)
                    next_cursor = response_data.get("next_cursor", "")

                    if next_cursor and next_cursor != cursor:
                        cursor = next_cursor
                        print(f"📄 Has next page: {has_next_page}")
                        print(f"🔗 Next cursor: '{cursor}'")
                    else:
                        print("🔚 No more pages available (cursor unchanged or empty)")
                        has_next_page = False

                    if has_next_page:
                        print(
                            f"⏳ Waiting {delay_between_requests} seconds before next request..."
                        )
                        time.sleep(delay_between_requests)

            else:
                consecutive_empty_pages += 1
                print(
                    f"⚠️  Empty page received (consecutive: {consecutive_empty_pages})"
                )

                if consecutive_empty_pages >= max_consecutive_empty:
                    print(
                        f"⚠️  Too many consecutive empty pages ({consecutive_empty_pages}). Stopping."
                    )
                    has_next_page = False
                else:
                    has_next_page = response_data.get("has_next_page", False)
                    next_cursor = response_data.get("next_cursor", "")

                    if next_cursor and next_cursor != cursor:
                        cursor = next_cursor
                        print(f"📄 Has next page: {has_next_page}")
                        print(f"🔗 Next cursor: '{cursor}'")
                    else:
                        has_next_page = False

        except requests.exceptions.RequestException as e:
            print(f"❌ Network/Request Error: {str(e)}")
            return total_tweets, total_pages, False
        except json.JSONDecodeError as e:
            print(f"❌ JSON Decode Error: {str(e)}")
            print(f"Response text: {response.text[:200]}...")
            return total_tweets, total_pages, False
        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}")
            return total_tweets, total_pages, False

        page_number += 1

        if page_number > 1000:
            print("⚠️  Reached maximum page limit (1000). Stopping for safety.")
            break

    return total_tweets, total_pages, True


def _iter_months_inclusive(start_d: date, end_d: date):
    """Yield (year, month) for each calendar month overlapping [start_d, end_d]."""
    y, m = start_d.year, start_d.month
    while (y, m) <= (end_d.year, end_d.month):
        yield y, m
        if m == 12:
            y, m = y + 1, 1
        else:
            m += 1


def _utc_window_for_month_clipped(year: int, month: int, clip_start: date, clip_end: date):
    """
    Return (since_str, until_str) for Twitter advanced search for this month,
    clipped to [clip_start, clip_end] inclusive. None if no overlap.
    """
    first = date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    last = date(year, month, last_day)
    window_start = max(clip_start, first)
    window_end = min(clip_end, last)
    if window_start > window_end:
        return None
    since_str = f"{window_start.strftime('%Y-%m-%d')}_00:00:00_UTC"
    until_str = f"{window_end.strftime('%Y-%m-%d')}_23:59:59_UTC"
    return since_str, until_str


def scrape_user_tweets_by_year(username, year, api_key, project_dir):
    """
    Scrape tweets for a specific user and year using Twitter Advanced Search API.
    """
    scraper_state.reset()

    print(f"\n{'='*60}")
    print(f"SCRAPING TWEETS FOR @{username} - YEAR {year}")
    print(f"{'='*60}")
    print(f"Output directory: {project_dir}")

    start_date = f"{year}-01-01_00:00:00_UTC"
    end_date = f"{year}-12-31_23:59:59_UTC"
    search_query = f"from:{username} since:{start_date} until:{end_date}"
    file_stem_prefix = f"tweets_{username}_{year}"

    total_tweets, total_pages, success = _paginate_advanced_search(
        api_key, search_query, project_dir, file_stem_prefix
    )

    print(f"\n✅ YEAR {year} COMPLETED" if success else f"\n⚠️ YEAR {year} ENDED")
    print(f"📊 Total tweets saved: {total_tweets}")
    print(f"📄 Total pages processed: {total_pages}")
    print(f"📁 Files saved in: {project_dir}")

    return total_tweets, total_pages, success


def scrape_user_tweets_by_year_monthly(username, year, api_key, project_dir):
    """
    Scrape one calendar year in 12 monthly queries. Files: tweets_{user}_{year}_{MM}_page_NNN.json
    Completed months are preserved if a later month fails or the run stops.
    """
    scraper_state.reset()

    print(f"\n{'='*60}")
    print(f"SCRAPING TWEETS FOR @{username} - YEAR {year} (MONTHLY CHUNKS)")
    print(f"{'='*60}")
    print(f"Output directory: {project_dir}")

    total_tweets = 0
    total_pages = 0

    for month in range(1, 13):
        if scraper_state.stop_requested:
            print("\n🛑 SCRAPING STOPPED BY USER")
            print(f"📊 Tweets saved so far: {total_tweets}")
            return total_tweets, total_pages, False

        last_day = calendar.monthrange(year, month)[1]
        start_date = f"{year}-{month:02d}-01_00:00:00_UTC"
        end_date = f"{year}-{month:02d}-{last_day:02d}_23:59:59_UTC"
        search_query = f"from:{username} since:{start_date} until:{end_date}"
        file_stem_prefix = f"tweets_{username}_{year}_{month:02d}"

        print(f"\n{'─'*50}")
        print(f"📅 Month {year}-{month:02d}")
        print(f"{'─'*50}")

        tw, pg, ok = _paginate_advanced_search(
            api_key, search_query, project_dir, file_stem_prefix
        )
        total_tweets += tw
        total_pages += pg
        if not ok:
            print(f"\n⚠️ Stopped during {year}-{month:02d} (earlier months are already saved).")
            return total_tweets, total_pages, False

    print(f"\n✅ YEAR {year} (MONTHLY) COMPLETED")
    print(f"📊 Total tweets saved: {total_tweets}")
    print(f"📄 Total pages processed: {total_pages}")
    print(f"📁 Files saved in: {project_dir}")

    return total_tweets, total_pages, True

def scrape_user_tweets_by_range(username, start_date, end_date, api_key, project_dir):
    """
    Scrape tweets for a specific user and date interval using Twitter Advanced Search API.
    """
    scraper_state.reset()

    print(f"\n{'='*60}")
    print(f"SCRAPING TWEETS FOR @{username} - RANGE {start_date} to {end_date}")
    print(f"{'='*60}")
    print(f"Output directory: {project_dir}")

    start_date_utc = f"{start_date}_00:00:00_UTC"
    end_date_utc = f"{end_date}_23:59:59_UTC"
    search_query = f"from:{username} since:{start_date_utc} until:{end_date_utc}"
    file_stem_prefix = f"tweets_{username}_{start_date}_to_{end_date}"

    total_tweets, total_pages, success = _paginate_advanced_search(
        api_key, search_query, project_dir, file_stem_prefix
    )

    print(
        f"\n✅ RANGE {start_date} to {end_date} COMPLETED"
        if success
        else f"\n⚠️ RANGE {start_date} to {end_date} ENDED"
    )
    print(f"📊 Total tweets saved: {total_tweets}")
    print(f"📄 Total pages processed: {total_pages}")
    print(f"📁 Files saved in: {project_dir}")

    return total_tweets, total_pages, success


def scrape_user_tweets_by_range_monthly(username, start_date, end_date, api_key, project_dir):
    """
    Scrape a date range in monthly queries. Files: tweets_{user}_{year}_{MM}_page_NNN.json
    """
    scraper_state.reset()

    start_d = datetime.strptime(start_date, "%Y-%m-%d").date()
    end_d = datetime.strptime(end_date, "%Y-%m-%d").date()
    if start_d > end_d:
        print("Invalid range: start after end.")
        return 0, 0, False

    print(f"\n{'='*60}")
    print(
        f"SCRAPING TWEETS FOR @{username} - RANGE {start_date} to {end_date} (MONTHLY CHUNKS)"
    )
    print(f"{'='*60}")
    print(f"Output directory: {project_dir}")

    total_tweets = 0
    total_pages = 0

    for y, m in _iter_months_inclusive(start_d, end_d):
        if scraper_state.stop_requested:
            print("\n🛑 SCRAPING STOPPED BY USER")
            print(f"📊 Tweets saved so far: {total_tweets}")
            return total_tweets, total_pages, False

        win = _utc_window_for_month_clipped(y, m, start_d, end_d)
        if not win:
            continue

        since_str, until_str = win
        search_query = f"from:{username} since:{since_str} until:{until_str}"
        file_stem_prefix = f"tweets_{username}_{y}_{m:02d}"

        print(f"\n{'─'*50}")
        print(f"📅 Month {y}-{m:02d} ({since_str} … {until_str})")
        print(f"{'─'*50}")

        tw, pg, ok = _paginate_advanced_search(
            api_key, search_query, project_dir, file_stem_prefix
        )
        total_tweets += tw
        total_pages += pg
        if not ok:
            print(
                f"\n⚠️ Stopped during {y}-{m:02d} (earlier months are already saved)."
            )
            return total_tweets, total_pages, False

    print(f"\n✅ RANGE {start_date} to {end_date} (MONTHLY) COMPLETED")
    print(f"📊 Total tweets saved: {total_tweets}")
    print(f"📄 Total pages processed: {total_pages}")
    print(f"📁 Files saved in: {project_dir}")

    return total_tweets, total_pages, True

def ping_user_years(username, start_year, end_year, api_key, progress_callback=None):
    """
    Check activity for a user across a range of years.
    Returns a dictionary of {year: bool} indicating if tweets exist.
    """
    # Reset stop state at start
    scraper_state.reset()
    
    results = {}
    
    print(f"\n{'='*60}")
    print(f"PINGING ACTIVITY FOR @{username} ({start_year}-{end_year})")
    print(f"{'='*60}")
    
    url = "https://api.twitterapi.io/twitter/tweet/advanced_search"
    headers = {"X-API-Key": api_key}
    
    for year in range(start_year, end_year + 1):
        # Check stop signal
        if scraper_state.stop_requested:
            print("\n🛑 PING STOPPED BY USER")
            if progress_callback:
                progress_callback(year, None, "🛑 Stopped by user")
            break
            
        print(f"Checking {year}...", end=" ", flush=True)
        
        start_date = f"{year}-01-01_00:00:00_UTC"
        end_date = f"{year}-12-31_23:59:59_UTC"
        search_query = f"from:{username} since:{start_date} until:{end_date}"
        
        querystring = {
            "query": search_query,
            "queryType": "Latest",
            "cursor": "" 
        }
        
        try:
            # We only need the first page to confirm activity
            response = requests.get(url, headers=headers, params=querystring)
            
            if response.status_code == 200:
                data = response.json()
                tweets = data.get('tweets', [])
                
                if tweets and len(tweets) > 0:
                    print("✅ ACTIVE")
                    results[year] = True
                    if progress_callback:
                        progress_callback(year, True, f"✅ {year}: Active ({len(tweets)}+ tweets found)")
                else:
                    print("❌ INACTIVE")
                    results[year] = False
                    if progress_callback:
                        progress_callback(year, False, f"❌ {year}: Inactive (No tweets found)")
            else:
                print(f"⚠️ ERROR ({response.status_code})")
                results[year] = None
                if progress_callback:
                    progress_callback(year, None, f"⚠️ {year}: Error ({response.status_code})")
                
        except Exception as e:
            print(f"⚠️ EXCEPTION: {e}")
            results[year] = None
            if progress_callback:
                progress_callback(year, None, f"⚠️ {year}: Exception ({str(e)})")
            
        # Small delay to be polite
        time.sleep(0.5)
        
    return results


def fetch_conversation_parents(in_reply_to_ids, api_key, batch_size=50):
    """
    Batch fetch parent tweets by ID via TwitterAPI.io GET /twitter/tweets.
    Returns dict of {tweet_id: tweet_obj}.
    """
    if not in_reply_to_ids:
        return {}
    url = "https://api.twitterapi.io/twitter/tweets"
    headers = {"X-API-Key": api_key}
    parents = {}
    ids_list = list(in_reply_to_ids)
    for i in range(0, len(ids_list), batch_size):
        batch = ids_list[i:i + batch_size]
        tweet_ids_param = ",".join(batch)
        try:
            response = requests.get(url, headers=headers, params={"tweet_ids": tweet_ids_param})
            if response.status_code == 200:
                data = response.json()
                tweets = data.get("tweets", [])
                for t in tweets:
                    tid = t.get("id") or t.get("id_str")
                    if tid:
                        parents[str(tid)] = t
            time.sleep(0.5)
        except Exception as e:
            print(f"Error fetching parents batch: {e}")
    return parents


def scrape_user_24h(username, api_key, project_dir, include_thread_context=False, run_ts=None):
    """
    Scrape tweets and replies for one user over the past 24 hours.
    Optionally fetches parent tweets for replies (thread context).
    """
    end = datetime.utcnow()
    start = end - timedelta(hours=24)
    start_str = start.strftime("%Y-%m-%d_%H:%M:%S_UTC")
    end_str = end.strftime("%Y-%m-%d_%H:%M:%S_UTC")
    date_label = run_ts or end.strftime("%Y-%m-%d_%H%M")

    print(f"\n{'='*60}")
    print(f"SCRAPING 24H TWEETS FOR @{username}")
    print(f"{'='*60}")
    print(f"Output directory: {project_dir}")

    search_query = f"from:{username} since:{start_str} until:{end_str}"
    file_stem_prefix = f"tweets_{username}_24h_{date_label}"

    total_tweets, total_pages, ok = _paginate_advanced_search(
        api_key, search_query, project_dir, file_stem_prefix
    )

    all_reply_ids = set()
    if include_thread_context:
        pattern = os.path.join(project_dir, f"{file_stem_prefix}_page_*.json")
        for fp in sorted(glob.glob(pattern)):
            try:
                with open(fp, encoding="utf-8") as f:
                    page_tweets = json.load(f)
                if not isinstance(page_tweets, list):
                    continue
                for t in page_tweets:
                    if isinstance(t, dict) and t.get("inReplyToId"):
                        all_reply_ids.add(str(t["inReplyToId"]))
            except (json.JSONDecodeError, OSError):
                continue

    if include_thread_context and all_reply_ids:
        print(f"📥 Fetching {len(all_reply_ids)} parent tweets for thread context...")
        new_parents = fetch_conversation_parents(all_reply_ids, api_key)
        parents_path = os.path.join(project_dir, "conversation_parents.json")
        # Merge with existing parents (accrued storage)
        existing = {}
        if os.path.exists(parents_path):
            try:
                with open(parents_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
                if not isinstance(existing, dict):
                    existing = {}
            except Exception:
                existing = {}
        existing.update(new_parents)
        with open(parents_path, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)
        print(f"💾 Saved {len(existing)} parent tweets (merged) to {parents_path}")

    print(f"\n✅ 24H SCRAPE FOR @{username} COMPLETED")
    print(f"📊 Total tweets saved: {total_tweets}")
    return total_tweets


def scrape_multi_user_24h(usernames, api_key, include_thread_context=False, progress_callback=None):
    """
    Run N independent 24h scrapes, one per target. All tweets accrue into a single
    shared folder (datasets/24h_accrued/) for content exploration.
    """
    scraper_state.reset()
    run_ts = datetime.utcnow().strftime("%Y-%m-%d_%H%M")
    project_dir = os.path.join("datasets", "24h_accrued")
    os.makedirs(project_dir, exist_ok=True)
    results = []
    for i, username in enumerate(usernames):
        if scraper_state.stop_requested:
            if progress_callback:
                progress_callback(i, username, "Stopped by user", 0, None)
            break
        username = username.strip().lstrip("@")
        if not username:
            continue
        if progress_callback:
            progress_callback(i, username, "Scraping...", 0, project_dir)
        try:
            count = scrape_user_24h(username, api_key, project_dir, include_thread_context, run_ts=run_ts)
            results.append({"username": username, "status": "completed", "tweet_count": count, "project_dir": project_dir})
            if progress_callback:
                progress_callback(i, username, "Completed", count, project_dir)
        except Exception as e:
            results.append({"username": username, "status": "error", "tweet_count": 0, "project_dir": project_dir, "error": str(e)})
            if progress_callback:
                progress_callback(i, username, f"Error: {e}", 0, project_dir)
    return results
