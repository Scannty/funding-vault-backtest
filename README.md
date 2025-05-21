# Funding Vault Backtest

This repository provides a backtesting framework for simulating and analyzing funding rate arbitrage strategies on the HYPE perpetual and spot markets. The code is designed to help you evaluate the performance, risk, and optimal parameters for delta-neutral strategies using historical price and funding data.

## Features

-   Fetch and store historical perp and spot prices for HYPE
-   Fetch and store historical funding rates
-   Simulate delta-neutral funding strategies with customizable leverage and rebalance thresholds
-   Automatic rebalancing to avoid liquidation and optimize capital usage
-   Parameter grid search for leverage and rebalance thresholds
-   Visualization of results, including APY and Sharpe ratio heatmaps

## File Structure

```
funding-vault-backtest/
├── backtest.py         # Main simulation and analysis script
├── funding.py          # Funding rate data fetching and storage
├── price.py            # Price data fetching and storage (perp and spot)
├── data/
│   ├── funding_history/
│   │   └── HYPE.csv
│   └── price_history/
│       ├── HYPE_perp_prices.csv
│       └── HYPE_spot_prices.csv
└── README.md           # This file
```

## Usage

1. **Fetch Data**

    - Run `price.py` to fetch and store HYPE perp and spot price history.
    - Run `funding.py` to fetch and store HYPE funding rate history.

2. **Run Backtest**

    - Execute `backtest.py` to simulate the funding strategy and analyze results.
    - The script will:
        - Load historical data
        - Simulate the strategy for a grid of leverage and rebalance threshold values
        - Output APY and Sharpe ratio heatmaps for parameter selection

3. **Customize Parameters**
    - Adjust leverage, rebalance thresholds, or simulation logic in `backtest.py` as needed.

## Requirements

Install dependencies with:

```sh
pip install pandas numpy matplotlib seaborn
```

## Notes

-   The simulation logic closely follows real-world margin and funding mechanics for perpetual contracts.
-   Transaction fees and TSI are parameterized and can be adjusted in the code.
