import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

TRANSACTION_FEE_RATE = 0  # 0.02% per trade

def load_price_funding(price_path, spot_path, funding_path):
    price_df = pd.read_csv(price_path, parse_dates=['time'])
    spot_df = pd.read_csv(spot_path, parse_dates=['time'])
    funding_df = pd.read_csv(funding_path, parse_dates=['time'])
    # Filter to start from March 1
    start_date = pd.Timestamp('2025-02-01')
    price_df = price_df[price_df['time'] >= start_date]
    spot_df = spot_df[spot_df['time'] >= start_date]
    funding_df = funding_df[funding_df['time'] >= start_date]
    # Merge perp and spot on time
    df = pd.merge_asof(price_df.sort_values('time'), spot_df.sort_values('time'), on='time', suffixes=('_perp', '_spot'))
    df = pd.merge_asof(df.sort_values('time'), funding_df.sort_values('time'), on='time')
    df = df.dropna(subset=['price_perp', 'price_spot', 'fundingRate'])
    return df

def simulate_funding_strategy(df, target_leverage=2, rebalance_threshold=0.1, starting_capital=1_000_000):
    first_row = df.iloc[0]
    initial_size = starting_capital / (first_row['price_spot'] + (first_row['price_perp'] / target_leverage))
    position_spot = initial_size
    position_perp = -initial_size   
    entry_price_perp = first_row['price_perp']
    # Initial margin for perp is the notional divided by leverage
    margin_perp = abs(position_perp) * first_row['price_perp'] / target_leverage
    spot_value = position_spot * first_row['price_spot']
    portfolio_value = spot_value + margin_perp
    history = []
    for i, row in df.iterrows():
        price_perp = row['price_perp']
        price_spot = row['price_spot']
        funding = row['fundingRate']
        # Mark-to-market PnL for perp
        perp_pnl = abs(position_perp) * (entry_price_perp - price_perp)
        margin_perp += perp_pnl
        # Funding payment (paid on perp notional, deducted from margin)
        funding_payment = abs(position_perp) * price_perp * funding
        margin_perp += funding_payment
        # Mark-to-market portfolio value: spot value + perp margin
        spot_value = position_spot * price_spot
        # Effective leverage: perp notional / margin
        notional_perp = abs(position_perp) * price_perp
        maintenance_margin = 0.1 * notional_perp
        if (margin_perp < maintenance_margin) and (notional_perp > 0):
            # Liquidation condition: if margin falls below maintenance margin
            print(f"Liquidation at time {row['time']}: Margin ${margin_perp} < Maintenance Margin ${maintenance_margin}")
            history.append({'time': row['time'], 'portfolio_value': 0, 'leverage': effective_leverage, 'margin_perp': margin_perp})
            break
        effective_leverage = notional_perp / margin_perp if margin_perp != 0 else 0
        # Rebalance if margin buffer is too low or too high
        if (effective_leverage > target_leverage * (1 + rebalance_threshold)) or (effective_leverage < target_leverage * (1 - rebalance_threshold)):
            denominator = spot_value + (notional_perp / target_leverage)
            if denominator <= 0:
                scale = 1.0  # Avoid division by zero or negative denominator
            else:
                scale = (spot_value + margin_perp) / denominator
                
            new_position_spot = position_spot * scale
            new_position_perp = position_perp * scale
            delta_spot = new_position_spot - position_spot
            delta_perp = new_position_perp - position_perp
            # Transaction fees + estimated TSI
            tsi_spot = 0.001 * abs(delta_spot) * price_spot 
            tsi_perp = 0.001 * abs(delta_perp) * price_perp
            margin_perp = (abs(new_position_perp) * price_perp / target_leverage) - tsi_perp 
            # portfolio_value -= fee
            spot_value = new_position_spot * price_spot - tsi_spot
            position_spot = new_position_spot
            position_perp = new_position_perp
        
        portfolio_value = spot_value + margin_perp
        history.append({'time': row['time'], 'portfolio_value': portfolio_value, 'leverage': effective_leverage, 'margin_perp': margin_perp})
        entry_price_perp = price_perp
    return pd.DataFrame(history)

if __name__ == "__main__":
    price_path = "data/price_history/HYPE_perp_prices.csv"
    spot_path = "data/price_history/HYPE_spot_prices.csv"
    funding_path = "data/funding_history/HYPE.csv"
    df = load_price_funding(price_path, spot_path, funding_path)
    rebalance_threshold = 0.5

    # Example parameter grid
    leverage_values = [1.5, 2.0, 2.5, 3.0, 4.0, 5.0]
    threshold_values = [0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.75, 1]

    results = []

    # Calculate the number of years in your dataset for APY calculation
    n_days = (df['time'].iloc[-1] - df['time'].iloc[0]).days
    years = n_days / 365

    for leverage in leverage_values:
        for threshold in threshold_values:
            # Run simulation
            sim_results = simulate_funding_strategy(
                df, 
                target_leverage=leverage,
                rebalance_threshold=threshold,
            )
            
            final_value = sim_results['portfolio_value'].iloc[-1]
            returns = (final_value / 1_000_000) - 1
            volatility = sim_results['portfolio_value'].pct_change().std()
            sharpe_ratio = returns / volatility if volatility != 0 else 0

            # Calculate APY
            initial_value = 1_000_000
            apy = (final_value / initial_value) ** (1 / years) - 1 if years > 0 else 0
            
            results.append({
                'leverage': leverage,
                'threshold': threshold,
                'final_value': final_value,
                'returns': returns,
                'sharpe_ratio': sharpe_ratio,
                'apy': apy
            })

    # Convert results to DataFrame
    results_df = pd.DataFrame(results)

    # Pivot tables for heatmaps
    pivot_apy = results_df.pivot(index='leverage', columns='threshold', values='apy')
    pivot_sharpe = results_df.pivot(index='leverage', columns='threshold', values='sharpe_ratio')

    # Plot APY heatmap
    plt.figure(figsize=(12, 6))
    sns.heatmap(pivot_apy * 100, annot=True, fmt=".2f", cmap='viridis')
    plt.title('APY (%) by Leverage and Threshold')
    plt.xlabel('Rebalance Threshold')
    plt.ylabel('Leverage')
    plt.show()

    # Plot Sharpe Ratio heatmap
    plt.figure(figsize=(12, 6))
    sns.heatmap(pivot_sharpe, annot=True, fmt=".2f", cmap='viridis')
    plt.title('Sharpe Ratio by Leverage and Threshold')
    plt.xlabel('Rebalance Threshold')
    plt.ylabel('Leverage')
    plt.show()

