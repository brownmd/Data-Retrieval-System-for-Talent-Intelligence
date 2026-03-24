"""
GitHub AI Talent - Location Fetcher
-------------------------------------
Input:  ai_talent_raw_202101_202603.csv  (username, event_type, repo_name, created_at, event_score)
Output: final_talent_locations.csv       (username, raw_location)

Deduplicates usernames before hitting the GitHub API — one API call per
unique profile regardless of how many events they have.

Run on Hetzner VPS inside a screen session:
    screen -S github_fetch
    python3 fetch_locations.py
    Ctrl+A then D to detach

Override input file:
    python3 fetch_locations.py my_other_file.csv
"""

import sys
import pandas as pd
import requests
import time
import os
from dotenv import load_dotenv

# --- SETUP ---
load_dotenv()
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
INPUT_FILE = sys.argv[1] if len(sys.argv) > 1 else 'ai_talent_raw_202101_202603.csv'
OUTPUT_FILE = 'final_talent_locations.csv'
headers = {'Authorization': f'token {GITHUB_TOKEN}'}


def get_data():
    # Read input — support both CSV (event-level) and xlsx
    if INPUT_FILE.endswith('.csv'):
        df = pd.read_csv(INPUT_FILE)
    else:
        df = pd.read_excel(INPUT_FILE, engine='openpyxl')

    # Deduplicate: one API call per unique username regardless of event count
    usernames = df['username'].drop_duplicates().tolist()
    print(f"Total events: {len(df):,} | Unique usernames: {len(usernames):,}")

    if os.path.exists(OUTPUT_FILE):
        processed = set(pd.read_csv(OUTPUT_FILE)['username'].tolist())
        print(f"Resuming... {len(processed):,} users already processed.")
    else:
        processed = set()

    count = 0
    for user in usernames:
        if user in processed:
            continue

        try:
            r = requests.get(
                f'https://api.github.com/users/{user}',
                headers=headers,
                timeout=10
            )

            if r.status_code == 200:
                raw_loc = r.json().get('location')
            elif r.status_code == 404:
                raw_loc = None
            elif r.status_code == 403:
                print("Rate limit hit. Cooling down 60s...")
                time.sleep(60)
                continue
            else:
                raw_loc = None

        except Exception as e:
            print(f"Error on {user}: {e}")
            time.sleep(5)
            continue

        file_exists = os.path.exists(OUTPUT_FILE)
        pd.DataFrame([{
            'username': user,
            'raw_location': raw_loc,
        }]).to_csv(OUTPUT_FILE, mode='a', header=not file_exists, index=False)

        processed.add(user)
        count += 1

        if count % 100 == 0:
            print(f"Progress: {count:,} new users fetched (total processed: {len(processed):,})")

        time.sleep(0.8)

    print(f"Done. {count:,} users fetched. Results saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    get_data()