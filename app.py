import json
import math
import re
import html
import secrets
from collections import Counter
from fastapi import FastAPI, Request, Form, BackgroundTasks, Query, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response, PlainTextResponse, JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import os
import sys
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

import pandas as pd
from typing import Optional
from datetime import datetime

from src.data.scraper import (
    scrape_user_tweets_by_year,
    scrape_user_tweets_by_year_monthly,
    scrape_user_tweets_by_range,
    scrape_user_tweets_by_range_monthly,
    scraper_state,
    ping_user_years,
    scrape_multi_user_24h,
)
from src.data.loader import load_json_tweets, get_available_datasets, load_csv_data, load_conversation_parents
from src.analysis.growth import GrowthAnalyzer
from src.analysis.temporal import TemporalAnalyzer
from src.analysis.likes import LikesAnalyzer
from src.visualization.plots import plot_growth_escalation, plot_hourly_heatmap, plot_likes_analysis

app = FastAPI(title="Twitter Analyzer")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Global state for background tasks (simple version)
current_task = {
    "status": "idle",
    "message": "",
    "project_dir": "",
    "logs": [],
}

# Global state for ping task
current_ping_task = {
    "status": "idle",
    "results": {},
    "logs": [],
    "username": ""
}

# Global state for 24h scrape task
current_24h_task = {
    "status": "idle",
    "message": "",
    "usernames": [],
    "current_index": 0,
    "results": [],
    "project_dirs": [],
    "logs": [],
}

# --- AUTHENTICATION ---

def get_current_user(request: Request):
    session_token = request.cookies.get("session_token")
    # In a real app, validate token against a database/store. 
    # Here we just check if the cookie exists and matches our simple "admin_session" value
    if not session_token or session_token != "admin_session_valid":
        return None
    return True

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login", response_class=HTMLResponse)
async def login(request: Request, password: str = Form(...)):
    app_password = os.getenv("APP_PASSWORD")
    if not app_password:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Password not configured on server."})
    
    # Use secrets.compare_digest to prevent timing attacks
    if secrets.compare_digest(password, app_password):
        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie(key="session_token", value="admin_session_valid", httponly=True)
        return response
    else:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid password"})

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("session_token")
    return response

def fetch_twitterapi_credits(api_key: str) -> Optional[dict]:
    """Fetch credit balance from TwitterAPI.io. Returns None on error."""
    if not api_key:
        return None
    try:
        r = requests.get(
            "https://api.twitterapi.io/oapi/my/info",
            headers={"X-API-Key": api_key},
            timeout=10,
        )
        if r.status_code == 200:
            data = r.json()
            recharge = data.get("recharge_credits", 0)
            bonus = data.get("total_bonus_credits", 0)
            # Rough capacity: 15 credits/tweet, 18/profile, 15/follower
            tweets_capacity = recharge // 15 if recharge else 0
            return {
                "recharge_credits": recharge,
                "bonus_credits": bonus,
                "tweets_capacity": tweets_capacity,
            }
    except Exception:
        pass
    return None

# Dependency for protected routes
async def verify_auth(request: Request):
    user = get_current_user(request)
    if not user:
        # If it's an API call/HTMX, maybe return 401, but for full page loads redirect
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER, detail="Not authenticated", headers={"Location": "/login"})

@app.exception_handler(status.HTTP_303_SEE_OTHER)
async def auth_redirect_handler(request: Request, exc: HTTPException):
    return RedirectResponse(url=exc.headers["Location"], status_code=303)


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, auth: bool = Depends(verify_auth)):
    api_key = os.getenv("TWITTERAPI_KEY")
    credits = fetch_twitterapi_credits(api_key) if api_key else None
    return templates.TemplateResponse(
        "index.html", {"request": request, "credits": credits}
    )

@app.get("/scrape", response_class=HTMLResponse)
async def scrape_form(request: Request, auth: bool = Depends(verify_auth)):
    return templates.TemplateResponse("scrape.html", {"request": request})

def run_scrape_task(username, year, start_date, end_date, api_key, project_dir, monthly_chunks: bool):
    global current_task
    current_task["status"] = "running"
    current_task["message"] = "Scraping in progress..."
    current_task["project_dir"] = project_dir
    current_task["logs"] = []

    original_stdout = sys.stdout
    tee = _TeeLogWriter(original_stdout, current_task["logs"])
    sys.stdout = tee

    try:
        success = False
        if year:
            if monthly_chunks:
                total_tweets, pages, success = scrape_user_tweets_by_year_monthly(
                    username, year, api_key, project_dir
                )
            else:
                total_tweets, pages, success = scrape_user_tweets_by_year(
                    username, year, api_key, project_dir
                )
            if scraper_state.stop_requested:
                current_task["message"] = f"Scraping stopped by user. Saved {total_tweets} tweets."
                current_task["status"] = "stopped"
            else:
                current_task["message"] = f"Scraping completed. Saved {total_tweets} tweets in {pages} pages."
                current_task["status"] = "completed"
        elif start_date and end_date:
            if monthly_chunks:
                total_tweets, pages, success = scrape_user_tweets_by_range_monthly(
                    username, start_date, end_date, api_key, project_dir
                )
            else:
                total_tweets, pages, success = scrape_user_tweets_by_range(
                    username, start_date, end_date, api_key, project_dir
                )
            if scraper_state.stop_requested:
                current_task["message"] = f"Scraping stopped by user. Saved {total_tweets} tweets."
                current_task["status"] = "stopped"
            else:
                current_task["message"] = f"Scraping completed. Saved {total_tweets} tweets in {pages} pages."
                current_task["status"] = "completed"

        if not success and not scraper_state.stop_requested:
             current_task["status"] = "failed"
             current_task["message"] = "Scraping failed. Check logs."

    except Exception as e:
        current_task["status"] = "error"
        current_task["message"] = f"Error: {str(e)}"
    finally:
        tee.flush()
        sys.stdout = original_stdout

@app.post("/scrape")
async def scrape_submit(
    request: Request,
    background_tasks: BackgroundTasks,
    username: str = Form(...),
    year: Optional[int] = Form(None),
    start_date: Optional[str] = Form(None),
    end_date: Optional[str] = Form(None),
    monthly_chunks: Optional[str] = Form(None),
    auth: bool = Depends(verify_auth)
):
    api_key = os.getenv("TWITTERAPI_KEY")
    if not api_key:
        return templates.TemplateResponse("scrape_status.html", {
            "request": request,
            "status": "error",
            "message": "API Key not configured on server.",
            "project_dir": ""
        })

    if current_task["status"] == "running":
        return templates.TemplateResponse("scrape_status.html", {
            "request": request,
            "status": "running",
            "message": "A scraping task is already running!",
            "project_dir": current_task["project_dir"]
        })

    project_dir = os.path.join("datasets", f"{username}_tweets_analysis")
    os.makedirs(project_dir, exist_ok=True)

    monthly = monthly_chunks is not None and str(monthly_chunks).lower() in (
        "on",
        "true",
        "1",
        "yes",
    )

    background_tasks.add_task(
        run_scrape_task,
        username,
        year,
        start_date,
        end_date,
        api_key,
        project_dir,
        monthly,
    )
    
    return RedirectResponse(url="/scrape/status", status_code=303)

@app.get("/scrape/status", response_class=HTMLResponse)
async def scrape_status(request: Request, auth: bool = Depends(verify_auth)):
    return templates.TemplateResponse("scrape_status.html", {
        "request": request,
        "status": current_task["status"],
        "message": current_task["message"],
        "project_dir": current_task["project_dir"],
        "logs": current_task.get("logs", []),
    })

@app.get("/scrape/status/logs")
async def scrape_status_logs(auth: bool = Depends(verify_auth)):
    return JSONResponse({
        "status": current_task["status"],
        "message": current_task["message"],
        "logs": current_task.get("logs", []),
    })

@app.post("/scrape/stop")
async def scrape_stop(request: Request, auth: bool = Depends(verify_auth)):
    if current_task["status"] == "running":
        scraper_state.stop()
        current_task["message"] = "Stopping..."
    return RedirectResponse(url="/scrape/status", status_code=303)

# --- 24H SCRAPE FEATURE ---

class _TeeLogWriter:
    """Writes to original stdout and appends lines to a log list."""

    def __init__(self, original, log_list):
        self._original = original
        self._log_list = log_list
        self._buffer = ""

    def write(self, data):
        self._original.write(data)
        self._buffer += data
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            self._log_list.append(line)

    def flush(self):
        self._original.flush()
        if self._buffer.strip():
            self._log_list.append(self._buffer.rstrip())
            self._buffer = ""


def run_24h_scrape_task(usernames, include_thread_context):
    global current_24h_task
    current_24h_task["status"] = "running"
    current_24h_task["message"] = "Starting 24h scrape..."
    current_24h_task["results"] = []
    current_24h_task["project_dirs"] = []
    current_24h_task["logs"] = []

    def progress_callback(index, username, message, count, project_dir):
        current_24h_task["current_index"] = index
        current_24h_task["message"] = f"@{username}: {message}"

    original_stdout = sys.stdout
    tee = _TeeLogWriter(original_stdout, current_24h_task["logs"])
    sys.stdout = tee

    try:
        api_key = os.getenv("TWITTERAPI_KEY")
        if not api_key:
            current_24h_task["status"] = "error"
            current_24h_task["message"] = "API Key not configured on server."
            return

        results = scrape_multi_user_24h(
            usernames, api_key,
            include_thread_context=include_thread_context,
            progress_callback=progress_callback
        )
        current_24h_task["results"] = results
        current_24h_task["project_dirs"] = [r.get("project_dir") for r in results if r.get("project_dir")]
        current_24h_task["status"] = "completed"
        total = sum(r.get("tweet_count", 0) for r in results)
        current_24h_task["message"] = f"Completed. {len(results)} users, {total} tweets total."
    except Exception as e:
        current_24h_task["status"] = "error"
        current_24h_task["message"] = f"Error: {str(e)}"
    finally:
        tee.flush()
        sys.stdout = original_stdout

@app.get("/scrape-24h", response_class=HTMLResponse)
async def scrape_24h_form(request: Request, auth: bool = Depends(verify_auth)):
    api_key = os.getenv("TWITTERAPI_KEY")
    credits = fetch_twitterapi_credits(api_key) if api_key else None
    return templates.TemplateResponse("scrape_24h.html", {
        "request": request,
        "credits": credits,
    })

@app.post("/scrape-24h")
async def scrape_24h_submit(
    request: Request,
    background_tasks: BackgroundTasks,
    usernames: str = Form(...),
    include_thread_context: Optional[str] = Form(None),
    auth: bool = Depends(verify_auth)
):
    api_key = os.getenv("TWITTERAPI_KEY")
    if not api_key:
        return templates.TemplateResponse("scrape_24h_status.html", {
            "request": request,
            "status": "error",
            "message": "API Key not configured on server.",
            "usernames": [],
            "current_index": 0,
            "results": [],
            "project_dirs": []
        })

    if current_24h_task["status"] == "running":
        return templates.TemplateResponse("scrape_24h_status.html", {
            "request": request,
            "status": "running",
            "message": "A 24h scrape is already running!",
            "usernames": current_24h_task["usernames"],
            "current_index": current_24h_task["current_index"],
            "results": current_24h_task["results"],
            "project_dirs": current_24h_task["project_dirs"]
        })

    username_list = [u.strip().lstrip("@") for u in usernames.strip().splitlines() if u.strip()]
    if not username_list:
        return templates.TemplateResponse("scrape_24h_status.html", {
            "request": request,
            "status": "error",
            "message": "No usernames provided.",
            "usernames": [],
            "current_index": 0,
            "results": [],
            "project_dirs": []
        })

    current_24h_task["usernames"] = username_list
    include_context = include_thread_context is not None and include_thread_context.lower() in ("on", "true", "1", "yes")
    background_tasks.add_task(run_24h_scrape_task, username_list, include_context)
    return RedirectResponse(url="/scrape-24h/status", status_code=303)

@app.get("/scrape-24h/status", response_class=HTMLResponse)
async def scrape_24h_status(request: Request, auth: bool = Depends(verify_auth)):
    return templates.TemplateResponse("scrape_24h_status.html", {
        "request": request,
        "status": current_24h_task["status"],
        "message": current_24h_task["message"],
        "usernames": current_24h_task["usernames"],
        "current_index": current_24h_task["current_index"],
        "results": current_24h_task["results"],
        "project_dirs": current_24h_task["project_dirs"],
        "logs": current_24h_task.get("logs", []),
    })


@app.get("/scrape-24h/status/logs")
async def scrape_24h_status_logs(auth: bool = Depends(verify_auth)):
    """JSON endpoint for polling live log output."""
    return JSONResponse({
        "status": current_24h_task["status"],
        "message": current_24h_task["message"],
        "logs": current_24h_task.get("logs", []),
    })

@app.post("/scrape-24h/stop")
async def scrape_24h_stop(request: Request, auth: bool = Depends(verify_auth)):
    if current_24h_task["status"] == "running":
        scraper_state.stop()
        current_24h_task["message"] = "Stopping..."
    return RedirectResponse(url="/scrape-24h/status", status_code=303)

@app.get("/analyze", response_class=HTMLResponse)
async def analyze_form(request: Request, auth: bool = Depends(verify_auth)):
    datasets = get_available_datasets()
    return templates.TemplateResponse("analyze.html", {"request": request, "datasets": datasets})

@app.post("/analyze")
async def analyze_submit(
    request: Request,
    dataset: str = Form(...),
    analysis_type: str = Form(...),
    auth: bool = Depends(verify_auth)
):
    # Determine username and year from dataset name if possible
    # Expecting format like "username_tweets_analysis" or similar
    username = dataset.split('_')[0]
    year = "Unknown" # Placeholder
    
    plot_image = None
    error_message = None
    
    try:
        if analysis_type == "growth":
            tweets = load_json_tweets(os.path.join("datasets", dataset))
            if not tweets:
                raise ValueError("No tweets found in dataset.")
                
            likes_analyzer = LikesAnalyzer(tweets)
            df = likes_analyzer.df
            if df.empty:
                raise ValueError("Could not process tweets.")
                
            daily_counts = df.groupby('date').size().reset_index(name='tweets_totali')
            daily_counts['date_short'] = daily_counts['date']
            daily_counts['tweets_singoli'] = daily_counts['tweets_totali'] # Assumption
            daily_counts['thread_count'] = 0
            daily_counts['thread_tweets_total'] = 0
            
            analyzer = GrowthAnalyzer(daily_counts)
            monthly = analyzer.analyze_monthly()
            quarterly = analyzer.analyze_quarterly()
            weekly = analyzer.analyze_weekly()
            
            plot_image = plot_growth_escalation(monthly, quarterly, weekly, username, year)
            
        elif analysis_type == "heatmap":
            tweets = load_json_tweets(os.path.join("datasets", dataset))
            if not tweets:
                raise ValueError("No tweets found.")
            
            likes_analyzer = LikesAnalyzer(tweets)
            df = likes_analyzer.df
            
            df['hour'] = df['created_at'].dt.hour
            
            daily_hourly = df.groupby(['date', 'hour']).size().unstack(fill_value=0)
            daily_hourly = daily_hourly.reindex(columns=range(24), fill_value=0)
            daily_hourly.columns = [f'hour_{h:02d}' for h in range(24)]
            daily_hourly = daily_hourly.reset_index()
            daily_hourly['date_short'] = daily_hourly['date'] # For plotting
            
            plot_image = plot_hourly_heatmap(daily_hourly, username, year)
            
        elif analysis_type == "likes":
            tweets = load_json_tweets(os.path.join("datasets", dataset))
            if not tweets:
                raise ValueError("No tweets found.")
                
            analyzer = LikesAnalyzer(tweets)
            daily = analyzer.get_daily_stats()
            monthly = analyzer.get_monthly_stats()
            
            plot_image = plot_likes_analysis(daily, monthly, username)
            
        else:
            error_message = "Unknown analysis type."
            
    except Exception as e:
        error_message = f"Analysis failed: {str(e)}"
        import traceback
        traceback.print_exc()

    return templates.TemplateResponse("result.html", {
        "request": request,
        "plot_image": plot_image,
        "error_message": error_message,
        "analysis_type": analysis_type,
        "dataset": dataset
    })

# --- BROWSE FEATURE ---

@app.get("/browse", response_class=HTMLResponse)
async def browse_tweets(
    request: Request,
    dataset: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    search: Optional[str] = Query(None),
    author_filter: Optional[str] = Query(None),
    sort_by: str = Query("date_desc"),
    auth: bool = Depends(verify_auth)
):
    datasets = get_available_datasets()
    tweets_display = []
    total_tweets = 0
    total_pages = 1
    per_page = 50
    top_mentions = []
    authors = []
    is_content_focused = False

    parents = {}
    if dataset:
        try:
            dataset_path = os.path.join("datasets", dataset)
            # Load tweets
            all_tweets = load_json_tweets(dataset_path)
            # Load conversation parents (thread context) if available
            parents = load_conversation_parents(dataset_path)

            is_content_focused = dataset == "24h_accrued"

            # Filter by search text
            if search:
                search_lower = search.lower()
                all_tweets = [t for t in all_tweets if search_lower in t.get('text', '').lower()]

            # Filter by author (for 24h accrued content exploration)
            if author_filter and is_content_focused:
                author_lower = author_filter.lower()
                all_tweets = [t for t in all_tweets if (t.get('author') or {}).get('userName', '').lower() == author_lower]
            
            # Calculate Mentions (on the filtered dataset)
            mention_counter = Counter()
            for t in all_tweets:
                # Try entities first (more accurate)
                if 'entities' in t and 'user_mentions' in t['entities']:
                    for mention in t['entities']['user_mentions']:
                        mention_counter[mention['screen_name']] += 1
                else:
                    # Fallback to regex on text
                    text = t.get('text') or t.get('fullText') or ''
                    text = html.unescape(text) # Decode HTML entities
                    # Find @username (alphanumeric + underscore)
                    found = re.findall(r'@(\w+)', text)
                    for username in found:
                        mention_counter[username] += 1
        
            # Get top 10
            top_mentions = mention_counter.most_common(10)

            # Unique authors (for 24h accrued filter)
            if is_content_focused:
                author_set = set()
                for t in all_tweets:
                    uname = (t.get('author') or {}).get('userName')
                    if uname:
                        author_set.add(uname)
                authors = sorted(author_set)

            # Process and format tweets for display
            processed_tweets = []
            for t in all_tweets:
                # Parse date
                created_at = t.get('createdAt') or t.get('created_at')
                dt = None
                if created_at:
                    try:
                        # Try Twitter format first
                        dt = datetime.strptime(created_at, '%a %b %d %H:%M:%S %z %Y')
                    except:
                        try:
                            # Try ISO format
                            dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        except:
                            pass
                
                raw_text = t.get('text') or t.get('fullText') or ''
                decoded_text = html.unescape(raw_text)
                in_reply_to_id = t.get('inReplyToId')
                is_reply = t.get('isReply', False) or bool(in_reply_to_id)
                parent_display = None
                if is_reply and in_reply_to_id and parents:
                    pid = str(in_reply_to_id)
                    if pid in parents:
                        p = parents[pid]
                        parent_display = {
                            'text': html.unescape(p.get('text') or p.get('fullText') or ''),
                            'author': (p.get('author') or {}).get('userName') or 'unknown',
                            'id': p.get('id') or p.get('id_str') or pid
                        }
                author_name = (t.get('author') or {}).get('userName') or 'unknown'
                processed_tweets.append({
                    'id': t.get('id_str') or t.get('id'),
                    'text': decoded_text,
                    'author': author_name,
                    'created_at': dt,
                    'created_at_formatted': dt.strftime('%Y-%m-%d %H:%M') if dt else 'Unknown Date',
                    'likeCount': t.get('likeCount', 0) or t.get('favoriteCount', 0),
                    'retweetCount': t.get('retweetCount', 0),
                    'replyCount': t.get('replyCount', 0),
                    'viewCount': t.get('viewCount', 0),
                    'media_url': t.get('entities', {}).get('media', [{}])[0].get('media_url_https') if 'entities' in t else None,
                    'is_reply': is_reply,
                    'in_reply_to_id': in_reply_to_id,
                    'parent_display': parent_display
                })

            # Sort
            if sort_by == 'date_desc':
                processed_tweets.sort(key=lambda x: x['created_at'] or datetime.min, reverse=True)
            elif sort_by == 'date_asc':
                processed_tweets.sort(key=lambda x: x['created_at'] or datetime.min)
            elif sort_by == 'author':
                processed_tweets.sort(key=lambda x: (x.get('author', ''), x['created_at'] or datetime.min))
            elif sort_by == 'likes_desc':
                processed_tweets.sort(key=lambda x: x['likeCount'], reverse=True)
            elif sort_by == 'retweets_desc':
                processed_tweets.sort(key=lambda x: x['retweetCount'], reverse=True)

            # Pagination
            total_tweets = len(processed_tweets)
            total_pages = math.ceil(total_tweets / per_page)
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            tweets_display = processed_tweets[start_idx:end_idx]

        except Exception as e:
            print(f"Error browsing dataset: {e}")
            tweets_display = []

    return templates.TemplateResponse("browse.html", {
        "request": request,
        "datasets": datasets,
        "current_dataset": dataset,
        "tweets": tweets_display,
        "page": page,
        "total_pages": total_pages,
        "total_tweets": total_tweets,
        "search_query": search or "",
        "author_filter": author_filter or "",
        "sort_by": sort_by,
        "top_mentions": top_mentions,
        "authors": authors,
        "is_content_focused": is_content_focused
    })

# --- LLM EXPORT (24h accrued) ---

def _get_author(t):
    return (t.get("author") or {}).get("userName") or "unknown"


def _get_text(t):
    return html.unescape(t.get("text") or t.get("fullText") or "")


def _parse_created_at(created_at):
    if not created_at:
        return None
    try:
        return datetime.strptime(created_at, "%a %b %d %H:%M:%S %z %Y")
    except Exception:
        try:
            return datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        except Exception:
            return None


def _build_reply_chain(tid, lookup, seen):
    """Build recursive reply_to chain. lookup = parents + all tweets."""
    if tid in seen or tid not in lookup:
        return None
    seen.add(tid)
    p = lookup[tid]
    author = _get_author(p)
    text = _get_text(p)
    pid = p.get("inReplyToId")
    pid = str(pid) if pid else None
    out = {"author": author, "text": text}
    if pid and pid in lookup:
        out["reply_to"] = _build_reply_chain(pid, lookup, seen)
    return out


def _format_tweets_for_llm(tweets, parents):
    """
    Build chronological stream for LLM consumption with full reply chains and quoted tweets.
    Output: list of {author, timestamp, text, reply_to?, quoted_tweet?}.
    """
    lookup = {str(t.get("id")): t for t in tweets}
    for pid, p in parents.items():
        if pid not in lookup:
            lookup[pid] = p

    processed = []
    for t in tweets:
        dt = _parse_created_at(t.get("createdAt") or t.get("created_at"))
        ts_str = dt.strftime("%Y-%m-%d %H:%M") if dt else "Unknown"
        obj = {
            "author": _get_author(t),
            "timestamp": ts_str,
            "text": _get_text(t),
        }
        qt = t.get("quoted_tweet")
        if qt:
            obj["quoted_tweet"] = {"author": _get_author(qt), "text": _get_text(qt)}
        rid = t.get("inReplyToId")
        if rid:
            chain = _build_reply_chain(str(rid), lookup, set())
            if chain:
                obj["reply_to"] = chain
        processed.append({"created_at": dt, **obj})

    processed.sort(key=lambda x: x["created_at"] or datetime.min)
    return processed


@app.get("/24h_accrued/export")
async def export_24h_for_llm(
    request: Request,
    format: str = Query("text", description="text or json"),
    author: Optional[str] = Query(None, description="Filter by username (e.g. clkleinmonaco)"),
    auth: bool = Depends(verify_auth),
):
    """Export 24h_accrued dataset as chronological stream for LLM consumption."""
    dataset_path = os.path.join("datasets", "24h_accrued")
    if not os.path.exists(dataset_path):
        raise HTTPException(status_code=404, detail="24h_accrued dataset not found")
    tweets = load_json_tweets(dataset_path)
    parents = load_conversation_parents(dataset_path)
    if not tweets:
        raise HTTPException(status_code=404, detail="No tweets in 24h_accrued")

    if author:
        author_clean = author.strip().lstrip("@").lower()
        tweets = [t for t in tweets if (t.get("author") or {}).get("userName", "").lower() == author_clean]

    formatted = _format_tweets_for_llm(tweets, parents)

    if format == "json":
        out = [
            {k: v for k, v in f.items() if k != "created_at"}
            for f in formatted
        ]
        return Response(
            content=json.dumps(out, ensure_ascii=False, indent=2),
            media_type="application/json",
        )
    lines = []
    for f in formatted:
        block = f"@{f['author']} | {f['timestamp']}\n{f['text']}"
        if f.get("quoted_tweet"):
            qt = f["quoted_tweet"]
            block += f"\n[Quoting @{qt['author']}]: {qt['text']}"
        if f.get("reply_to"):
            chain = f["reply_to"]
            indent = ""
            while chain:
                block += f"\n{indent}[Reply to @{chain['author']}]: {chain['text']}"
                chain = chain.get("reply_to")
                indent += "  "
        lines.append(block)
    return PlainTextResponse(content="\n\n---\n\n".join(lines))

# --- PING FEATURE ---

@app.get("/ping", response_class=HTMLResponse)
async def ping_form(request: Request, auth: bool = Depends(verify_auth)):
    return templates.TemplateResponse("ping.html", {"request": request})

def ping_progress_callback(year, is_active, message):
    current_ping_task["results"][year] = is_active
    timestamp = datetime.now().strftime("%H:%M:%S")
    current_ping_task["logs"].append(f"[{timestamp}] {message}")

def run_ping_task(username, start_year, end_year, api_key):
    global current_ping_task
    current_ping_task["status"] = "running"
    current_ping_task["username"] = username
    current_ping_task["results"] = {}
    current_ping_task["logs"] = []
    current_ping_task["logs"].append(f"[{datetime.now().strftime('%H:%M:%S')}] Starting ping for @{username} ({start_year}-{end_year})...")
    
    try:
        results = ping_user_years(username, start_year, end_year, api_key, progress_callback=ping_progress_callback)
        current_ping_task["results"] = results # Ensure final state matches
        current_ping_task["status"] = "completed"
        current_ping_task["logs"].append(f"[{datetime.now().strftime('%H:%M:%S')}] Ping completed.")
    except Exception as e:
        current_ping_task["status"] = "error"
        current_ping_task["logs"].append(f"[{datetime.now().strftime('%H:%M:%S')}] Error: {str(e)}")

@app.post("/ping")
async def ping_submit(
    request: Request,
    background_tasks: BackgroundTasks,
    username: str = Form(...),
    start_year: int = Form(...),
    end_year: int = Form(...),
    auth: bool = Depends(verify_auth)
):
    api_key = os.getenv("TWITTERAPI_KEY")
    if not api_key:
        # Handle missing key gracefully - redirect to result but log error
        current_ping_task["status"] = "error"
        current_ping_task["logs"].append("Error: API Key not configured on server.")
        return RedirectResponse(url="/ping/result", status_code=303)

    if current_ping_task["status"] == "running":
        return RedirectResponse(url="/ping/result", status_code=303)
        
    background_tasks.add_task(run_ping_task, username, start_year, end_year, api_key)
    return RedirectResponse(url="/ping/result", status_code=303)

@app.get("/ping/result", response_class=HTMLResponse)
async def ping_result(request: Request, auth: bool = Depends(verify_auth)):
    return templates.TemplateResponse("ping_result.html", {
        "request": request,
        "status": current_ping_task["status"],
        "results": current_ping_task["results"],
        "logs": current_ping_task["logs"],
        "username": current_ping_task["username"]
    })

@app.post("/ping/stop")
async def ping_stop(request: Request, auth: bool = Depends(verify_auth)):
    if current_ping_task["status"] == "running":
        scraper_state.stop()
    return RedirectResponse(url="/ping/result", status_code=303)

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
