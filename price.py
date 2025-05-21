import os
import pandas as pd
import matplotlib.pyplot as plt
from hyperliquid.info import Info
from hyperliquid.utils import constants

INITIAL_LISTING_TIMESTAMP_MS = 1702392469448  # HYPE initial listing timestamp
DATA_DIR = "data/price_history"
os.makedirs(DATA_DIR, exist_ok=True)

# Configuration
API_URL = constants.MAINNET_API_URL  # or constants.TESTNET_API_URL
info_client = Info(API_URL, skip_ws=True)

def fetch_perp_price_history() -> pd.DataFrame:
    path = os.path.join(DATA_DIR, "HYPE_perp_prices.csv")
    if os.path.isfile(path):
        existing = pd.read_csv(path, parse_dates=["time"])
    else:
        existing = pd.DataFrame(columns=["time", "price"])


    end_time = int(pd.Timestamp.now().timestamp() * 1000)

    price_data = info_client.candles_snapshot(
        name="HYPE",
        startTime=0,
        endTime=end_time,
        interval="1h" 
    )

    print(f"Fetched {len(price_data)} new price entries.")
    # print(price_data)
    df = price_data.copy() if isinstance(price_data, pd.DataFrame) else pd.DataFrame(price_data)
    if df.empty:
        print("No new price data fetched.")
        return existing

    df["time"] = pd.to_datetime(df["t"], unit="ms")
    df = df[["time", "c"]].rename(columns={"c": "price"})
    combined = pd.concat([existing, df], ignore_index=True)
    combined.drop_duplicates(subset=["time"], keep="last", inplace=True)
    combined.sort_values("time", inplace=True)
    combined.to_csv(path, index=False)
    print(f"Fetched {len(df)} new price entries. Total: {len(combined)}.")
    return combined

def fetch_spot_price_history() -> pd.DataFrame:
    os.makedirs(DATA_DIR, exist_ok=True)
    path = os.path.join(DATA_DIR, f"HYPE_spot_prices.csv")
    if os.path.isfile(path):
        existing = pd.read_csv(path, parse_dates=["time"])
    else:
        existing = pd.DataFrame(columns=["time", "price"])

    end_time = int(pd.Timestamp.now().timestamp() * 1000)
    price_data = info_client.candles_snapshot(
        name="@107",
        startTime=0,
        endTime=end_time,
        interval="1h"
    )

    print(f"Fetched {len(price_data)} new spot price entries.")
    df = price_data.copy() if isinstance(price_data, pd.DataFrame) else pd.DataFrame(price_data)
    if df.empty:
        print("No new spot price data fetched.")
        return existing

    df["time"] = pd.to_datetime(df["t"], unit="ms")
    df = df[["time", "c"]].rename(columns={"c": "price"})
    combined = pd.concat([existing, df], ignore_index=True)
    combined.drop_duplicates(subset=["time"], keep="last", inplace=True)
    combined.sort_values("time", inplace=True)
    combined.to_csv(path, index=False)
    print(f"Fetched {len(df)} new spot price entries. Total: {len(combined)}.")
    return combined

def plot_history(df: pd.DataFrame):
    print(f"DataFrame shape before plotting: {df.shape}")
    print(df.head())
    # Ensure 'time' is datetime
    if not pd.api.types.is_datetime64_any_dtype(df['time']):
        df['time'] = pd.to_datetime(df['time'])
    # Downsample to daily frequency
    df_resampled = df.set_index('time').resample('1D').last().dropna().reset_index()
    print(f"Resampled DataFrame shape: {df_resampled.shape}")
    # If too many points, plot only the last 365 days
    if len(df_resampled) > 365:
        df_resampled = df_resampled.iloc[-365:]
        print("Plotting only the last 365 days.")
    plt.figure(figsize=(12, 6))
    plt.plot(df_resampled['time'], df_resampled['price'], marker='o', markersize=2, linewidth=1)
    plt.xlabel('Time')
    plt.ylabel('Price in $')
    plt.title('HYPE Perp Price History (Daily)')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.xticks(rotation=45)
    # Limit number of x-ticks for readability
    if len(df_resampled) > 20:
        step = max(1, len(df_resampled) // 20)
        plt.xticks(df_resampled['time'][::step])
    plt.tight_layout()
    plt.show()

def plot_spot_history(df: pd.DataFrame):
    print(f"Spot DataFrame shape before plotting: {df.shape}")
    print(df.head())
    if not pd.api.types.is_datetime64_any_dtype(df['time']):
        df['time'] = pd.to_datetime(df['time'])
    df_resampled = df.set_index('time').resample('1D').last().dropna().reset_index()
    print(f"Resampled Spot DataFrame shape: {df_resampled.shape}")
    if len(df_resampled) > 365:
        df_resampled = df_resampled.iloc[-365:]
        print("Plotting only the last 365 days.")
    plt.figure(figsize=(12, 6))
    plt.plot(df_resampled['time'], df_resampled['price'], marker='o', markersize=2, linewidth=1)
    plt.xlabel('Time')
    plt.ylabel('Spot Price in $')
    plt.title('HYPE Spot Price History (Daily)')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.xticks(rotation=45)
    if len(df_resampled) > 20:
        step = max(1, len(df_resampled) // 20)
        plt.xticks(df_resampled['time'][::step])
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    df = fetch_perp_price_history()
    if not df.empty:
        print(f"Latest price: {df['price'].iloc[-1]}")
        print(f"Latest time: {df['time'].iloc[-1]}")
        plot_history(df)
    else:
        print("No price data available.")

    # Fetch and plot spot price
    spot_df = fetch_spot_price_history()
    if not spot_df.empty:
        print(f"Latest spot price: {spot_df['price'].iloc[-1]}")
        print(f"Latest spot time: {spot_df['time'].iloc[-1]}")
        plot_spot_history(spot_df)
    else:
        print("No spot price data available.")