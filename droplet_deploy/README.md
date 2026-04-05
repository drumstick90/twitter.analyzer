# Ocean Droplet Deployment

This folder contains the necessary files to deploy the "Last 24h Scan + Positioning" pipeline to a DigitalOcean Droplet (or any Linux server).

## Documentation

- **[PRD.md](PRD.md)**: Product Requirements Document (What this is and why).
- **[TRD.md](TRD.md)**: Technical Requirements Document (How it works and architecture).

## Prerequisites

- Python 3.11+
- `pip`
- `virtualenv` (optional but recommended)

## Setup

1.  **Upload files to Droplet:**
    Use `scp` or `rsync` to copy this folder to your server.
    ```bash
    scp -r droplet_deploy user@your_droplet_ip:~/twitter_analyzer
    ```

2.  **Install Dependencies:**
    SSH into your server and navigate to the folder.
    ```bash
    cd ~/twitter_analyzer
    python3.11 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

3.  **Configuration:**
    - Copy `.env.example` to `.env` and fill in your API keys.
      ```bash
      cp .env.example .env
      nano .env
      ```
    - Edit `config.json` to update the list of usernames if needed.
      ```bash
      nano config.json
      ```

4.  **Run Manually:**
    To test the pipeline manually:
    ```bash
    ./run_pipeline.sh
    ```
    This will:
    1.  Scrape tweets for the users in `config.json` (last 24h).
    2.  Run the positioning analysis using the latest Claude 3 Opus model.
    3.  Save the output to `agenti/output/positioning_plan.json`.

## Viewing Results

The results are stored in:
`agenti/output/positioning_plan.json`

To view them nicely:
1.  **Download** the `view_results.html` and `agenti/output/positioning_plan.json` to your local machine.
2.  **Open** `view_results.html` in your browser.
    - If the JSON is in the correct relative path (`agenti/output/positioning_plan.json`), it might load automatically (depending on browser security settings).
    - If not, simply click the "Load JSON file..." button and select the `positioning_plan.json` file.

Alternatively, you can run a simple HTTP server on the droplet to view remotely (if ports are open/tunneled):
```bash
python3 -m http.server 8000
```
Then visit `http://your_droplet_ip:8000/view_results.html`.

## Automation (Cron)

To set up a daily cron job (runs at 6:00 AM UTC):

```bash
./setup_cron.sh
```

Logs will be available in `logs/pipeline.log`.

## Structure

- `run_scan.py`: Script to run the 24h scrape based on `config.json`.
- `run_pipeline.sh`: Master script that runs scan and then positioning.
- `view_results.html`: Standalone HTML viewer for the results.
- `agenti/`: Contains the positioning logic (extraction + orchestration).
- `src/data/`: Contains the scraping logic.
- `datasets/`: Where scraped data is stored.
