# Twitter Analyzer

A modular web application to scrape and analyze Twitter activity, growth patterns, and engagement metrics.

## Features

*   **Scraper**: Download tweets from any public profile using the third-party `api.twitterapi.io` service (intermediary for Twitter Advanced Search).
*   **Browse Interface**: Explore, search, filter, and view stats for thousands of scraped tweets in a responsive grid layout.
*   **Growth Analysis**: Visualize monthly and quarterly tweet volume trends.
*   **Hourly Heatmap**: Analyze activity patterns (time of day vs. day of year).
*   **Likes Analysis**: Track daily engagement progression.
*   **Web Interface**: Simple and intuitive UI for all operations.

## API Requirement

This application relies on **[TwitterAPI.io](https://twitterapi.io/)** (an intermediary service) to fetch data. It does **not** use the official Twitter/X API.

*   You must obtain an API Key from `api.twitterapi.io`.
*   This key is required to use the **Scrape** and **Ping** features.
*   You will be prompted to enter this key in the web interface forms.

## Installation

1.  **Prerequisites**: Python 3.11+
2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  **Start the App**:
    ```bash
    python3.11 app.py
    ```
    The server will start at `http://0.0.0.0:8000`.

2.  **Open Web Interface**:
    Navigate to `http://localhost:8000` in your browser.

3.  **Scrape Data**:
    *   Go to the "Scrape" tab.
    *   Enter the Twitter username (without @).
    *   Choose a year or date range.
    *   Click "Start Scraping".
    *   **Stopping**: You can stop a running scrape job by clicking the "Stop Scraping" button on the status page.

4.  **Analyze Data**:
    *   Go to the "Analyze" tab.
    *   Select a dataset (folder) from the dropdown.
    *   Choose an analysis type (Growth, Heatmap, Likes).
    *   View the generated visualizations.

## Project Structure

*   `app.py`: Main FastAPI application.
*   `src/`: Source code for data loading, analysis, and visualization.
*   `templates/`: HTML templates for the web UI.
*   `datasets/`: Directory where scraped tweet data is stored.
*   `output/`: Directory for generated plots and reports.
*   `legacy/`: Old standalone scripts.

## Stopping the Server

To stop the web server, press `Ctrl+C` in the terminal where `app.py` is running.
