import pandas as pd
import json
import os
import glob
from typing import List, Dict, Union, Optional

def load_json_tweets(directory: str, pattern: str = "*.json") -> List[Dict]:
    """
    Load all JSON tweet files from a directory matching a pattern.
    
    Args:
        directory (str): Directory containing JSON files.
        pattern (str): Glob pattern to match files (default: "*.json").
        
    Returns:
        List[Dict]: List of all tweets loaded from the files.
    """
    all_tweets = []
    search_path = os.path.join(directory, pattern)
    files = glob.glob(search_path)
    
    print(f"Found {len(files)} files matching {pattern} in {directory}")
    
    for file_path in files:
        # Skip conversation_parents.json (thread context metadata, not tweet list)
        if os.path.basename(file_path) == "conversation_parents.json":
            continue
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    all_tweets.extend(data)
                elif isinstance(data, dict):
                    # Handle case where single tweet or wrapped response
                    if 'tweets' in data:
                        all_tweets.extend(data['tweets'])
                    else:
                        all_tweets.append(data)
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            
    return all_tweets

def load_csv_data(file_path: str) -> pd.DataFrame:
    """
    Load data from a CSV file.
    
    Args:
        file_path (str): Path to the CSV file.
        
    Returns:
        pd.DataFrame: Loaded DataFrame.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
        
    return pd.read_csv(file_path)

def load_conversation_parents(directory: str) -> Dict[str, Dict]:
    """
    Load conversation parent tweets from conversation_parents.json.
    Used for displaying reply context in Browse.

    Args:
        directory (str): Directory containing conversation_parents.json.

    Returns:
        Dict[str, Dict]: Map of tweet_id -> parent tweet object. Empty dict if file missing.
    """
    file_path = os.path.join(directory, "conversation_parents.json")
    if not os.path.exists(file_path):
        return {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
            return {}
    except Exception as e:
        print(f"Error loading conversation_parents.json: {e}")
        return {}


def get_available_datasets(base_path: str = "datasets") -> List[str]:
    """
    Find all directories that look like tweet datasets (contain 'tweets_analysis' or similar).
    
    Args:
        base_path (str): Root directory to search. Default is 'datasets'.
        
    Returns:
        List[str]: List of directory names.
    """
    datasets = []
    if not os.path.exists(base_path):
        return []
        
    for item in os.listdir(base_path):
        if os.path.isdir(os.path.join(base_path, item)):
            if "tweets_analysis" in item or "_json" in item or "_24h_" in item or "24h_accrued" in item:
                datasets.append(item)
    return sorted(datasets)
