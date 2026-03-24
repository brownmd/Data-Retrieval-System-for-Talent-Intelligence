"""
GitHub AI Talent - Location Fetcher
-------------------------------------
Input:  ai_talent_raw_202101_202603.csv  (username, event_type, repo_name, created_at, event_score)
Output: final_talent_locations.csv       (username, raw_location, cleaned_location)

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

# Slang/nickname map for location cleaning
slang_map = {
    # New York
    "the big apple": "New York, NY",
    "nyc": "New York, NY",
    "new york city": "New York, NY",
    "manhattan": "New York, NY",
    "brooklyn": "New York, NY",
    "queens": "New York, NY",
    "bronx": "New York, NY",
    # California
    "sf": "San Francisco, CA",
    "the bay": "San Francisco, CA",
    "bay area": "San Francisco, CA",
    "silicon valley": "San Jose, CA",
    "socal": "Los Angeles, CA",
    "so cal": "Los Angeles, CA",
    "la": "Los Angeles, CA",
    "los angeles": "Los Angeles, CA",
    "sd": "San Diego, CA",
    "oak": "Oakland, CA",
    "oakland": "Oakland, CA",
    # Texas
    "atx": "Austin, TX",
    "h-town": "Houston, TX",
    "htx": "Houston, TX",
    "dfw": "Dallas, TX",
    "dallas": "Dallas, TX",
    # Washington
    "pnw": "Seattle, WA",
    "sea": "Seattle, WA",
    # DC Area
    "dmv": "Washington, DC",
    "dc": "Washington, DC",
    "washington dc": "Washington, DC",
    "nova": "Arlington, VA",
    # Illinois
    "chi": "Chicago, IL",
    "chitown": "Chicago, IL",
    "chi-town": "Chicago, IL",
    "windy city": "Chicago, IL",
    # Pennsylvania
    "philly": "Philadelphia, PA",
    "phl": "Philadelphia, PA",
    "pgh": "Pittsburgh, PA",
    "pittsburgh": "Pittsburgh, PA",
    # Massachusetts
    "bos": "Boston, MA",
    "the hub": "Boston, MA",
    # Colorado
    "denver": "Denver, CO",
    "den": "Denver, CO",
    "mile high city": "Denver, CO",
    # Georgia
    "atl": "Atlanta, GA",
    "atlanta": "Atlanta, GA",
    # Florida
    "mia": "Miami, FL",
    "miami": "Miami, FL",
    "orlando": "Orlando, FL",
    "tampa": "Tampa, FL",
    # North Carolina
    "rdu": "Raleigh, NC",
    "raleigh": "Raleigh, NC",
    "charlotte": "Charlotte, NC",
    "clt": "Charlotte, NC",
    # Tennessee
    "nash": "Nashville, TN",
    "nashville": "Nashville, TN",
    # Oregon
    "pdx": "Portland, OR",
    "portland": "Portland, OR",
    # Minnesota
    "minneapolis": "Minneapolis, MN",
    "twin cities": "Minneapolis, MN",
    "msp": "Minneapolis, MN",
    # Arizona
    "phx": "Phoenix, AZ",
    "phoenix": "Phoenix, AZ",
    # Nevada
    "las vegas": "Las Vegas, NV",
    "lv": "Las Vegas, NV",
    "vegas": "Las Vegas, NV",
    # Full state names
    "alabama": "Alabama, AL",
    "alaska": "Alaska, AK",
    "arizona": "Arizona, AZ",
    "arkansas": "Arkansas, AR",
    "california": "California, CA",
    "colorado": "Colorado, CO",
    "connecticut": "Connecticut, CT",
    "delaware": "Delaware, DE",
    "florida": "Florida, FL",
    "georgia": "Georgia, GA",
    "hawaii": "Hawaii, HI",
    "idaho": "Idaho, ID",
    "illinois": "Illinois, IL",
    "indiana": "Indiana, IN",
    "iowa": "Iowa, IA",
    "kansas": "Kansas, KS",
    "kentucky": "Kentucky, KY",
    "louisiana": "Louisiana, LA",
    "maine": "Maine, ME",
    "maryland": "Maryland, MD",
    "massachusetts": "Massachusetts, MA",
    "michigan": "Michigan, MI",
    "minnesota": "Minnesota, MN",
    "mississippi": "Mississippi, MS",
    "missouri": "Missouri, MO",
    "montana": "Montana, MT",
    "nebraska": "Nebraska, NE",
    "nevada": "Nevada, NV",
    "new hampshire": "New Hampshire, NH",
    "new jersey": "New Jersey, NJ",
    "new mexico": "New Mexico, NM",
    "new york": "New York, NY",
    "north carolina": "North Carolina, NC",
    "north dakota": "North Dakota, ND",
    "ohio": "Ohio, OH",
    "oklahoma": "Oklahoma, OK",
    "oregon": "Oregon, OR",
    "pennsylvania": "Pennsylvania, PA",
    "rhode island": "Rhode Island, RI",
    "south carolina": "South Carolina, SC",
    "south dakota": "South Dakota, SD",
    "tennessee": "Tennessee, TN",
    "texas": "Texas, TX",
    "utah": "Utah, UT",
    "vermont": "Vermont, VT",
    "virginia": "Virginia, VA",
    "washington": "Washington, WA",
    "west virginia": "West Virginia, WV",
    "wisconsin": "Wisconsin, WI",
    "wyoming": "Wyoming, WY",
    # State abbreviations
    "al": "Alabama, AL",
    "ak": "Alaska, AK",
    "az": "Arizona, AZ",
    "ar": "Arkansas, AR",
    "ca": "California, CA",
    "co": "Colorado, CO",
    "ct": "Connecticut, CT",
    "de": "Delaware, DE",
    "fl": "Florida, FL",
    "ga": "Georgia, GA",
    "hi": "Hawaii, HI",
    "id": "Idaho, ID",
    "il": "Illinois, IL",
    "in": "Indiana, IN",
    "ia": "Iowa, IA",
    "ks": "Kansas, KS",
    "ky": "Kentucky, KY",
    "me": "Maine, ME",
    "md": "Maryland, MD",
    "ma": "Massachusetts, MA",
    "mi": "Michigan, MI",
    "mn": "Minnesota, MN",
    "ms": "Mississippi, MS",
    "mo": "Missouri, MO",
    "mt": "Montana, MT",
    "ne": "Nebraska, NE",
    "nv": "Nevada, NV",
    "nh": "New Hampshire, NH",
    "nj": "New Jersey, NJ",
    "nm": "New Mexico, NM",
    "ny": "New York, NY",
    "nc": "North Carolina, NC",
    "nd": "North Dakota, ND",
    "oh": "Ohio, OH",
    "ok": "Oklahoma, OK",
    "or": "Oregon, OR",
    "pa": "Pennsylvania, PA",
    "ri": "Rhode Island, RI",
    "sc": "South Carolina, SC",
    "sd": "South Dakota, SD",
    "tn": "Tennessee, TN",
    "tx": "Texas, TX",
    "ut": "Utah, UT",
    "vt": "Vermont, VT",
    "va": "Virginia, VA",
    "wa": "Washington, WA",
    "wv": "West Virginia, WV",
    "wi": "Wisconsin, WI",
    "wy": "Wyoming, WY",
}


def clean_location(raw_loc):
    if not raw_loc:
        return None
    low_loc = raw_loc.lower().strip()
    for slang, clean in slang_map.items():
        if slang in low_loc:
            return clean
    return raw_loc


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

        clean_loc = clean_location(raw_loc)

        file_exists = os.path.exists(OUTPUT_FILE)
        pd.DataFrame([{
            'username': user,
            'raw_location': raw_loc,
            'cleaned_location': clean_loc,
        }]).to_csv(OUTPUT_FILE, mode='a', header=not file_exists, index=False)

        processed.add(user)
        count += 1

        if count % 100 == 0:
            print(f"Progress: {count:,} new users fetched (total processed: {len(processed):,})")

        time.sleep(0.8)

    print(f"Done. {count:,} users fetched. Results saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    get_data()