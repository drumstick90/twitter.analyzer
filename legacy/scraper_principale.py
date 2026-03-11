import requests
import json
import os
import time
import argparse
import sys
from datetime import datetime

def scrape_user_tweets_by_year(username, year, api_key, project_dir):
    """
    Scrape tweets for a specific user and year using Twitter Advanced Search API.
    
    Args:
        username (str): Twitter username without @ (e.g., 'NTFabiano')
        year (int): Year to scrape (e.g., 2024)
        api_key (str): Twitter API key
        project_dir (str): Main project directory where all files will be saved
    
    Returns:
        tuple: (total_tweets, total_pages, success)
    """
    
    print(f"\n{'='*60}")
    print(f"SCRAPING TWEETS FOR @{username} - YEAR {year}")
    print(f"{'='*60}")
    print(f"Output directory: {project_dir}")
    
    # Twitter Advanced Search API endpoint
    url = "https://api.twitterapi.io/twitter/tweet/advanced_search"
    headers = {"X-API-Key": api_key}
    
    # Advanced search query for specific year
    # Format: "from:username since:YYYY-MM-DD until:YYYY-MM-DD"
    start_date = f"{year}-01-01_00:00:00_UTC"
    end_date = f"{year}-12-31_23:59:59_UTC"
    search_query = f"from:{username} since:{start_date} until:{end_date}"
    query_type = "Latest"
    
    print(f"Search query: {search_query}")
    print(f"Query type: {query_type}")
    
    # Pagination variables - start with empty cursor for each year
    cursor = ""
    has_next_page = True
    page_number = 1
    total_tweets = 0
    total_pages = 0
    
    # Rate limiting - add small delay between requests
    delay_between_requests = 1  # seconds
    
    # Track consecutive empty pages to detect when we're really done
    consecutive_empty_pages = 0
    max_consecutive_empty = 3
    
    while has_next_page:
        print(f"\n--- Fetching Page {page_number} ---")
        print(f"Using cursor: '{cursor}'")
        
        # Parameters for advanced search
        querystring = {
            "query": search_query,
            "queryType": query_type,
            "cursor": cursor
        }
        
        try:
            response = requests.get(url, headers=headers, params=querystring)
            
            # Check HTTP status first
            if response.status_code != 200:
                print(f"❌ HTTP Error {response.status_code}: {response.text}")
                return total_tweets, total_pages, False
            
            response_data = response.json()
            
            # Check for API errors
            if 'error' in response_data:
                print(f"❌ API Error: {response_data.get('message', 'Unknown error')}")
                return total_tweets, total_pages, False
                
            elif response_data.get('tweets') is not None:
                tweets_on_page = response_data['tweets']
                total_pages += 1
                
                print(f"📊 Tweets received on this page: {len(tweets_on_page)}")
                
                if tweets_on_page and len(tweets_on_page) > 0:
                    # Reset consecutive empty pages counter
                    consecutive_empty_pages = 0
                    
                    # Save tweets for this page in the main directory
                    file_path = os.path.join(project_dir, f"tweets_{username}_{year}_page_{page_number:03d}.json")
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(tweets_on_page, f, indent=2, ensure_ascii=False)
                    
                    print(f"💾 Saved {len(tweets_on_page)} tweets to {file_path}")
                    total_tweets += len(tweets_on_page)
                    
                    # Update pagination - get next cursor and check if there are more pages
                    has_next_page = response_data.get('has_next_page', False)
                    next_cursor = response_data.get('next_cursor', "")
                    
                    # Validate cursor - if it's empty or same as current, we're done
                    if next_cursor and next_cursor != cursor:
                        cursor = next_cursor
                        print(f"📄 Has next page: {has_next_page}")
                        print(f"🔗 Next cursor: '{cursor}'")
                    else:
                        print("🔚 No more pages available (cursor unchanged or empty)")
                        has_next_page = False
                    
                    # Add delay to avoid rate limiting
                    if has_next_page:
                        print(f"⏳ Waiting {delay_between_requests} seconds before next request...")
                        time.sleep(delay_between_requests)
                    
                else:
                    # Handle empty page
                    consecutive_empty_pages += 1
                    print(f"⚠️  Empty page received (consecutive: {consecutive_empty_pages})")
                    
                    # If we get too many consecutive empty pages, something might be wrong
                    if consecutive_empty_pages >= max_consecutive_empty:
                        print(f"⚠️  Too many consecutive empty pages ({consecutive_empty_pages}). Stopping.")
                        has_next_page = False
                    else:
                        # Still try to get next page info
                        has_next_page = response_data.get('has_next_page', False)
                        next_cursor = response_data.get('next_cursor', "")
                        
                        if next_cursor and next_cursor != cursor:
                            cursor = next_cursor
                            print(f"📄 Has next page: {has_next_page}")
                            print(f"🔗 Next cursor: '{cursor}'")
                        else:
                            has_next_page = False
                    
            else:
                print(f"❌ Unexpected response format: {response_data}")
                break
                
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
        
        # Safety check - prevent infinite loops
        if page_number > 1000:  # Maximum reasonable number of pages
            print("⚠️  Reached maximum page limit (1000). Stopping for safety.")
            break
    
    print(f"\n✅ YEAR {year} COMPLETED")
    print(f"📊 Total tweets saved: {total_tweets}")
    print(f"📄 Total pages processed: {total_pages}")
    print(f"📁 Files saved in: {project_dir}")
    
    return total_tweets, total_pages, True

def validate_year(year_str):
    """Validate that the year is reasonable."""
    try:
        year = int(year_str)
        if 2006 <= year <= 2030:  # Twitter started in 2006, reasonable future limit
            return year
        else:
            raise ValueError(f"Year {year} is outside reasonable range (2006-2030)")
    except ValueError as e:
        raise argparse.ArgumentTypeError(f"Invalid year: {e}")

def validate_username(username):
    """Validate that the username is reasonable."""
    if not username or len(username) > 15:  # Twitter username max length
        raise argparse.ArgumentTypeError("Username must be 1-15 characters long")
    if not username.replace('_', '').replace('-', '').isalnum():
        raise argparse.ArgumentTypeError("Username can only contain letters, numbers, underscores, and hyphens")
    return username

def validate_date(date_str):
    """Validate date in YYYY-MM-DD format."""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        if 2006 <= dt.year <= 2030:
            return date_str
        raise argparse.ArgumentTypeError(
            f"Date {date_str} year is outside reasonable range (2006-2030)"
        )
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Invalid date '{date_str}'. Expected format YYYY-MM-DD"
        )

def scrape_user_tweets_by_range(username, start_date, end_date, api_key, project_dir):
    """
    Scrape tweets for a specific user and date interval using Twitter Advanced Search API.
    
    Args:
        username (str): Twitter username without @
        start_date (str): Start date in YYYY-MM-DD format (inclusive)
        end_date (str): End date in YYYY-MM-DD format (inclusive)
        api_key (str): Twitter API key
        project_dir (str): Main project directory where all files will be saved
    
    Returns:
        tuple: (total_tweets, total_pages, success)
    """
    
    print(f"\n{'='*60}")
    print(f"SCRAPING TWEETS FOR @{username} - RANGE {start_date} to {end_date}")
    print(f"{'='*60}")
    print(f"Output directory: {project_dir}")
    
    # Twitter Advanced Search API endpoint
    url = "https://api.twitterapi.io/twitter/tweet/advanced_search"
    headers = {"X-API-Key": api_key}
    
    # Advanced search query for date range
    start_date_utc = f"{start_date}_00:00:00_UTC"
    end_date_utc = f"{end_date}_23:59:59_UTC"
    search_query = f"from:{username} since:{start_date_utc} until:{end_date_utc}"
    query_type = "Latest"
    
    print(f"Search query: {search_query}")
    print(f"Query type: {query_type}")
    
    # Pagination variables
    cursor = ""
    has_next_page = True
    page_number = 1
    total_tweets = 0
    total_pages = 0
    
    # Rate limiting
    delay_between_requests = 1  # seconds
    
    # Track consecutive empty pages
    consecutive_empty_pages = 0
    max_consecutive_empty = 3
    
    while has_next_page:
        print(f"\n--- Fetching Page {page_number} ---")
        print(f"Using cursor: '{cursor}'")
        
        # Parameters for advanced search
        querystring = {
            "query": search_query,
            "queryType": query_type,
            "cursor": cursor
        }
        
        try:
            response = requests.get(url, headers=headers, params=querystring)
            
            # Check HTTP status first
            if response.status_code != 200:
                print(f"❌ HTTP Error {response.status_code}: {response.text}")
                return total_tweets, total_pages, False
            
            response_data = response.json()
            
            # Check for API errors
            if 'error' in response_data:
                print(f"❌ API Error: {response_data.get('message', 'Unknown error')}")
                return total_tweets, total_pages, False
                
            elif response_data.get('tweets') is not None:
                tweets_on_page = response_data['tweets']
                total_pages += 1
                
                print(f"📊 Tweets received on this page: {len(tweets_on_page)}")
                
                if tweets_on_page and len(tweets_on_page) > 0:
                    # Reset consecutive empty pages counter
                    consecutive_empty_pages = 0
                    
                    # Save tweets for this page
                    file_path = os.path.join(project_dir, f"tweets_{username}_{start_date}_to_{end_date}_page_{page_number:03d}.json")
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(tweets_on_page, f, indent=2, ensure_ascii=False)
                    
                    print(f"💾 Saved {len(tweets_on_page)} tweets to {file_path}")
                    total_tweets += len(tweets_on_page)
                    
                    # Update pagination
                    has_next_page = response_data.get('has_next_page', False)
                    next_cursor = response_data.get('next_cursor', "")
                    
                    if next_cursor and next_cursor != cursor:
                        cursor = next_cursor
                        print(f"📄 Has next page: {has_next_page}")
                        print(f"🔗 Next cursor: '{cursor}'")
                    else:
                        print("🔚 No more pages available (cursor unchanged or empty)")
                        has_next_page = False
                    
                    # Add delay to avoid rate limiting
                    if has_next_page:
                        print(f"⏳ Waiting {delay_between_requests} seconds before next request...")
                        time.sleep(delay_between_requests)
                    
                else:
                    # Handle empty page
                    consecutive_empty_pages += 1
                    print(f"⚠️  Empty page received (consecutive: {consecutive_empty_pages})")
                    
                    if consecutive_empty_pages >= max_consecutive_empty:
                        print(f"⚠️  Too many consecutive empty pages ({consecutive_empty_pages}). Stopping.")
                        has_next_page = False
                    else:
                        has_next_page = response_data.get('has_next_page', False)
                        next_cursor = response_data.get('next_cursor', "")
                        
                        if next_cursor and next_cursor != cursor:
                            cursor = next_cursor
                            print(f"📄 Has next page: {has_next_page}")
                            print(f"🔗 Next cursor: '{cursor}'")
                        else:
                            has_next_page = False
                    
            else:
                print(f"❌ Unexpected response format: {response_data}")
                break
                
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
        
        # Safety check
        if page_number > 1000:
            print("⚠️  Reached maximum page limit (1000). Stopping for safety.")
            break
    
    print(f"\n✅ RANGE {start_date} to {end_date} COMPLETED")
    print(f"📊 Total tweets saved: {total_tweets}")
    print(f"📄 Total pages processed: {total_pages}")
    print(f"📁 Files saved in: {project_dir}")
    
    return total_tweets, total_pages, True

def main():
    """Main function to scrape tweets with command-line arguments."""
    
    # Set up command-line argument parser
    parser = argparse.ArgumentParser(
        description="Scrape tweets from a specific Twitter user for a specific year or date range",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scraper_principale.py NTFabiano 2020
  python scraper_principale.py --username NTFabiano --year 2020
  python scraper_principale.py -u elonmusk -y 2023
  python scraper_principale.py -u elonmusk --start-date 2023-01-15 --end-date 2023-03-01
        """
    )
    
    parser.add_argument(
        'username_pos', 
        nargs='?', 
        type=validate_username,
        metavar='username',
        help='Twitter username (without @) to scrape'
    )
    
    parser.add_argument(
        'year_pos', 
        nargs='?', 
        type=validate_year,
        metavar='year',
        help='Year to scrape (e.g., 2020)'
    )
    
    parser.add_argument(
        '-u', '--username',
        type=validate_username,
        help='Twitter username (alternative to positional argument)'
    )
    
    parser.add_argument(
        '-y', '--year',
        type=validate_year,
        help='Year to scrape (alternative to positional argument)'
    )
    
    parser.add_argument(
        '--start-date',
        type=validate_date,
        help='Start date inclusive (YYYY-MM-DD). Use with --end-date.'
    )
    
    parser.add_argument(
        '--end-date',
        type=validate_date,
        help='End date inclusive (YYYY-MM-DD). Use with --start-date.'
    )
    
    parser.add_argument(
        '--api-key',
        default="7ca4adac7ee14461995df707b9c2c8f2",
        help='Twitter API key (default: uses the one in the script)'
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Determine username and year (prioritize named arguments over positional)
    username = args.username or args.username_pos
    year = args.year or args.year_pos
    start_date = args.start_date
    end_date = args.end_date
    
    # Username is required
    if not username:
        print("❌ ERROR: Username is required!")
        print("Usage examples:")
        print("  python scraper_principale.py username year")
        print("  python scraper_principale.py --username username --year year")
        print("  python scraper_principale.py -u username -y year")
        print("  python scraper_principale.py -u username --start-date YYYY-MM-DD --end-date YYYY-MM-DD")
        sys.exit(1)
    
    # Year or date range is required
    if not year and not (start_date and end_date):
        print("❌ ERROR: Provide either a year or a start/end date range!")
        print("Usage examples:")
        print("  python scraper_principale.py username year")
        print("  python scraper_principale.py --username username --year year")
        print("  python scraper_principale.py -u username -y year")
        print("  python scraper_principale.py -u username --start-date YYYY-MM-DD --end-date YYYY-MM-DD")
        sys.exit(1)
    
    # Both start and end date must be provided together
    if (start_date and not end_date) or (end_date and not start_date):
        print("❌ ERROR: --start-date and --end-date must be used together")
        sys.exit(1)
    
    # Validate date order
    if start_date and end_date:
        if datetime.strptime(start_date, "%Y-%m-%d") > datetime.strptime(end_date, "%Y-%m-%d"):
            print("❌ ERROR: --start-date must be before or equal to --end-date")
            sys.exit(1)
    
    # Configuration
    api_key = args.api_key
    
    print(f"🚀 TWITTER SCRAPER FOR @{username}")
    if year:
        print(f"📅 Year to analyze: {year}")
    else:
        print(f"📅 Date range to analyze: {start_date} to {end_date}")
    print(f"🔑 Using API key: {api_key[:8]}...")
    
    # Create main project directory (single directory for all files)
    project_dir = f"{username}_tweets_analysis"
    os.makedirs(project_dir, exist_ok=True)
    
    # Summary statistics
    total_tweets_all_years = 0
    total_pages_all_years = 0
    successful_years = []
    failed_years = []
    
    # Scrape the specified year or date range
    try:
        if year:
            tweets, pages, success = scrape_user_tweets_by_year(username, year, api_key, project_dir)
            
            if success:
                total_tweets_all_years += tweets
                total_pages_all_years += pages
                successful_years.append(year)
                print(f"✅ {year}: {tweets} tweets, {pages} pages")
            else:
                failed_years.append(year)
                print(f"❌ {year}: Failed")
        else:
            tweets, pages, success = scrape_user_tweets_by_range(username, start_date, end_date, api_key, project_dir)
            
            if success:
                total_tweets_all_years += tweets
                total_pages_all_years += pages
                range_str = f"{start_date}..{end_date}"
                successful_years.append(range_str)
                print(f"✅ {range_str}: {tweets} tweets, {pages} pages")
            else:
                range_str = f"{start_date}..{end_date}"
                failed_years.append(range_str)
                print(f"❌ {range_str}: Failed")
            
    except KeyboardInterrupt:
        if year:
            print(f"\n⚠️  User interrupted scraping for year {year}")
        else:
            print(f"\n⚠️  User interrupted scraping for range {start_date}..{end_date}")
    except Exception as e:
        if year:
            print(f"❌ Unexpected error for year {year}: {str(e)}")
            failed_years.append(year)
        else:
            range_str = f"{start_date}..{end_date}"
            print(f"❌ Unexpected error for range {range_str}: {str(e)}")
            failed_years.append(range_str)
    
    # Final summary
    print(f"\n{'='*60}")
    print(f"🎯 SCRAPING COMPLETED FOR @{username}")
    print(f"{'='*60}")
    print(f"✅ Successful years: {successful_years}")
    print(f"❌ Failed years: {failed_years}")
    print(f"📊 Total tweets across all years: {total_tweets_all_years:,}")
    print(f"📄 Total pages processed: {total_pages_all_years:,}")
    print(f"📁 Project directory: {project_dir}")
    
    # Create summary file
    summary_file = os.path.join(project_dir, "scraping_summary.json")
    summary_data = {
        "username": username,
        "year": year,
        "start_date": start_date,
        "end_date": end_date,
        "scraping_date": datetime.now().isoformat(),
        "successful_years": successful_years,
        "failed_years": failed_years,
        "total_tweets": total_tweets_all_years,
        "total_pages": total_pages_all_years,
        "api_key_used": f"{api_key[:8]}..."
    }
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, indent=2, ensure_ascii=False)
    
    print(f"📋 Summary saved to: {summary_file}")

if __name__ == "__main__":
    main()