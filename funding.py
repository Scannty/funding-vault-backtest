import os
import time
import pandas as pd
import matplotlib.pyplot as plt
from hyperliquid.info import Info
from hyperliquid.utils import constants

# Configuration
API_URL = constants.MAINNET_API_URL  # or constants.TESTNET_API_URL
info_client = Info(API_URL, skip_ws=True)

# Constants
TICKER = "HYPE"
INITIAL_LISTING_TIMESTAMP_MS = 1702392469448  # HYPE initial listing timestamp
DATA_DIR = "data/funding_history"
UPDATE_INTERVAL_SECONDS = 10   # fetch new data every 10 seconds
os.makedirs(DATA_DIR, exist_ok=True)

# Load or initialize history CSV
def load_history() -> pd.DataFrame:
    path = os.path.join(DATA_DIR, f"{TICKER}.csv")
    if os.path.isfile(path):
        df = pd.read_csv(path, parse_dates=["time"])
    else:
        df = pd.DataFrame(columns=["time", "fundingRate", "premium"])
    df.drop_duplicates(subset=["time"], keep="last", inplace=True)
    df.sort_values("time", inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df

# Persist DataFrame
def save_history(df: pd.DataFrame):
    path = os.path.join(DATA_DIR, f"{TICKER}.csv")
    df.to_csv(path, index=False)

# Update funding history using SDK
def update_history() -> pd.DataFrame:
    df = load_history()
    # Determine start timestamp
    if not df.empty:
        start_ms = int(df['time'].view('int64').iloc[-1] // 1e6)
    else:
        start_ms = INITIAL_LISTING_TIMESTAMP_MS
    end_ms = int(pd.Timestamp.now().timestamp() * 1000)

    # Fetch via SDK; may return list of dicts or DataFrame
    raw = info_client.funding_history(
        name=TICKER,
        startTime=start_ms,
        endTime=end_ms
    )
    # Normalize to DataFrame
    if len(raw) == 1:
        raw = []
    new_df = raw.copy() if isinstance(raw, pd.DataFrame) else pd.DataFrame(raw)
    if new_df.empty:
        print("No new data fetched.")
         # Plot the fully indexed data
        plot_history(df)
        return df

    # Convert and select
    new_df['time'] = pd.to_datetime(new_df['time'], unit='ms')
    new_df = new_df[['time', 'fundingRate', 'premium']]

    # Ensure numeric types
    new_df['fundingRate'] = pd.to_numeric(new_df['fundingRate'], errors='coerce')
    new_df['premium'] = pd.to_numeric(new_df['premium'], errors='coerce')

    # Merge and dedupe
    combined = pd.concat([df, new_df], ignore_index=True)
    combined.drop_duplicates(subset=['time'], keep='last', inplace=True)
    combined.sort_values('time', inplace=True)

    save_history(combined)
    print(f"Updated history: {len(new_df)} new entries, total {len(combined)}.")
    return combined

# Plotting
def plot_history(df: pd.DataFrame):
    plt.figure()
    plt.plot(df['time'], df['fundingRate'])
    plt.xlabel('Time')
    plt.ylabel('Funding Rate')
    plt.title(f'{TICKER} Funding Rate History')
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    try:
        while True:
            hype_df = update_history() 
            time.sleep(UPDATE_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print("Terminated by user.")
    except Exception as e:
        print(f"Error running script: {e}")