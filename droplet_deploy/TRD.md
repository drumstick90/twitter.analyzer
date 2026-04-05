# Technical Requirements Document (TRD)

## System Architecture

The system is a linear pipeline designed for a headless Linux environment (e.g., DigitalOcean Droplet).

```mermaid
graph TD
    A[Cron Job (6:00 UTC)] --> B[run_pipeline.sh]
    B --> C[run_scan.py]
    C -->|TwitterAPI.io| D[Raw Tweets JSON]
    B --> E[agenti.cli (Extraction)]
    D --> E
    E -->|Claude 3 Opus| F[Extraction JSONs]
    B --> G[agenti.cli (Orchestration)]
    F --> G
    G -->|Claude 3 Opus| H[positioning_plan.json]
    H --> I[view_results.html]
```

## Component Specifications

### 1. Environment & Dependencies
- **OS**: Linux (Ubuntu/Debian recommended)
- **Runtime**: Python 3.11+
- **Key Libraries**:
    - `requests`: For TwitterAPI and Anthropic API calls.
    - `anthropic`: For LLM interaction.
    - `python-dotenv`: For secrets management.
- **Secrets**: Stored in `.env` (TWITTERAPI_KEY, ANTHROPIC_API_KEY).

### 2. Data Ingestion (`src/data/scraper.py`)
- **Source**: `twitterapi.io` (Advanced Search endpoint).
- **Logic**: Iterates through `config.json` usernames. Fetches tweets `since: 24h ago`.
- **Storage**: JSON files in `datasets/24h_accrued/`.
- **Rate Limiting**: Built-in delays to respect API limits.

### 3. AI Agents (`agenti/`)
- **Model Strategy**: Dynamically resolves the latest `claude-3-opus` model via `utils.py` to ensure longevity.
- **Extraction Agent**:
    - Prompt: `EXTRACTION_SYSTEM` (in `prompts.py`).
    - Context Window: Handles ~24h of tweets per user.
- **Orchestrator Agent**:
    - Prompt: `ORCHESTRATOR_SYSTEM` (in `prompts.py`).
    - Logic: Synthesizes N extraction reports into one plan.

### 4. Output & Visualization
- **Data**: `agenti/output/positioning_plan.json`.
- **Viewer**: `view_results.html` (Single-page app, vanilla JS).
    - Loads local JSON file.
    - Renders responsive dashboard.
    - No build step required.

## Deployment & Operations
- **Installation**: `pip install -r requirements.txt`.
- **Automation**: Standard `cron` job managed via `setup_cron.sh`.
- **Logging**: `stdout/stderr` redirected to `logs/pipeline.log`.
- **Maintenance**: Minimal. Python virtual environment isolates dependencies.

## Security Considerations
- **API Keys**: Never committed to code. Loaded from environment.
- **Network**: No inbound ports opened. Outbound HTTPS only (443).
- **Isolation**: Runs as a standard user process.
