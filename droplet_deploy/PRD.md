# Product Requirements Document (PRD)

## Product Overview
**Product Name**: Market Signal Extraction & Positioning System (Droplet Edition)
**Version**: 1.0.0
**Purpose**: Automated daily system to scrape financial commentary from Twitter/X, extract actionable market signals using LLMs (Claude 3 Opus), and synthesize a professional portfolio positioning plan.

## User Stories
- **As a Portfolio Manager**, I want to wake up to a synthesized view of what key market commentators are saying, so I can adjust my positioning without reading thousands of tweets.
- **As a Trader**, I want to identify consensus trades to fade and emerging tail risks to hedge.
- **As a System Administrator**, I want a "set and forget" system that runs reliably on a cheap VPS (Droplet) without manual intervention.

## Key Features

### 1. Automated Data Collection (24h Scan)
- **Input**: List of high-signal Twitter accounts (configurable).
- **Process**: Scrape tweets, replies, and quoted tweets from the last 24 hours.
- **Output**: JSON datasets of raw social media activity.
- **Constraint**: Must use `twitterapi.io` to avoid risking personal accounts.

### 2. Signal Extraction (Agent 1)
- **Input**: Raw tweet batches per commentator.
- **Process**: LLM analysis to extract specific trade ideas, risk flags, and market views.
- **Output**: Structured JSON "Extraction Reports" per commentator.

### 3. Positioning Synthesis (Agent 2)
- **Input**: Batch of Extraction Reports.
- **Process**: LLM orchestration to weigh consensus, detect conflicts, and apply risk frameworks (e.g., Barbell Strategy).
- **Output**: A final `positioning_plan.json` containing:
    - Theme Map
    - Convergence Matrix
    - Concrete Trade Recommendations (Tickers, Direction, Sizing)
    - Tail Risk Register
    - Daily Briefing

### 4. Lightweight Deployment
- **Constraint**: Must run on a low-resource Linux server (1GB RAM, 1 vCPU).
- **Constraint**: No complex database or web server requirements.
- **Constraint**: Output must be easily viewable via a simple HTML file.

## Success Metrics
- **Reliability**: Pipeline completes daily execution >99% of the time.
- **Accuracy**: Extracted signals accurately reflect the commentators' views (no hallucinations).
- **Usability**: The "Daily Briefing" provides a clear <30s read for market context.
