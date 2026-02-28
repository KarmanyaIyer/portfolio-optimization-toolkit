import yfinance
import pandas
import sqlite3
import datetime
import logging
import math
import matplotlib.pyplot

# PJ imports
import database
import backend

# -------------------

logging.basicConfig(filename="main.log", level=logging.INFO, format="%(asctime)s - `%(name)s` in %(filename)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

PRESETS = {
    'Tech Giants': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA'],
    'Defense': ['LMT', 'RTX', 'NOC', 'GD', 'KTOS'],
    'Pharmaceuticals': ['LLY', 'JNJ', 'PFE', 'MRK'],
    'Financial Services': ['JPM', 'BAC', 'V', 'MA', 'GS'],
    'Consumer Staples': ['PG', 'KO', 'PEP', 'COST', 'WMT'],
    'Green Energy': ['NEE', 'ENPH', 'FSLR', 'BE', 'PLUG'],
    'Semiconductors': ['TSM', 'AVGO', 'AMD', 'QCOM', 'INTC'],
    'Diversified Blue Chips': ['AAPL', 'JPM', 'JNJ', 'PG', 'XOM', 'LMT', 'DIS', 'T'],
    'Balanced Mix': ['MSFT', 'JNJ', 'JPM', 'NEE', 'AMT', 'CAT'],
    'High Growth': ['TSLA', 'NVDA', 'SHOP', 'SQ', 'PLTR']
}

def get_user_input(prompt, type_func=str):
    while True:
        try:
            user_input = input(prompt)
            return type_func(user_input)
        except ValueError:
            print("Invalid input. Please try again.")

def get_tickers_input():
    while True:
        user_input = input("Enter Ticker List (comma separated) or 'P' for Presets: ").strip()
        if user_input.upper() == 'P' or user_input.upper() == 'p':
            print("\n--- PRESETS ---")
            preset_keys = list(PRESETS.keys())
            for i, name in enumerate(preset_keys, 1):
                print(f"{i}. {name}: {', '.join(PRESETS[name])}")
            
            while True:
                selection = input("Select a preset number (or 'b' to go back): ").strip()
                if selection.lower() == 'b':
                    break
                try:
                    choice = int(selection)
                    if 1 <= choice <= len(preset_keys):
                        selected_preset = preset_keys[choice - 1]
                        return PRESETS[selected_preset]
                    else:
                        print("Invalid preset number.")
                except ValueError:
                    print("Invalid input. Please try again.")
        else:
            return [t.strip().upper() for t in user_input.split(',')]

def fetch_and_store_data(tickers):
    end = datetime.datetime.now()
    start = end - datetime.timedelta(days=365*10)

    # get stock prices
    stockdata = database.scrape_historical_stock_prices(tickers, start, end)
    if stockdata.empty:
        print("Error: No valid stock data found for the provided tickers.")
        return False
        
    database.append_to_sql_database(stockdata, "stock_prices")

    # get risk-free rates
    rf_data = database.scrape_risk_free_rate(start, end)
    database.append_to_sql_database(rf_data, "risk_free_rate")
    return True

def optimize_new_portfolio():
    tickers = get_tickers_input()
    if not tickers:
        return

    investment_amount = get_user_input("Enter Investment Amount ($): ", float)
    max_allocation_pct = get_user_input("Enter Max Allocation % (e.g., 50): ", float)
    max_allocation = max_allocation_pct / 100.0
    show_plot_input = get_user_input("Show Efficient Frontier Plot? (y/n): ").lower()
    show_plot = show_plot_input == 'y'

    if not fetch_and_store_data(tickers):
        return

    result = backend.optimize_portfolio(max_allocation=max_allocation, show_plot=show_plot)

    if result:
        print("\n--- OPTIMAL PORTFOLIO ALLOCATION ---")
        print(f"{'Ticker':<10} | {'Allocation %':<15} | {'Shares to Buy':<15} | {'Cost':<15}")
        print("-" * 65)
        
        total_cost = 0
        for ticker, weight in result['weights'].items():
            if weight > 0.001:
                allocation_amt = investment_amount * weight
                price = result['prices'][ticker]
                shares = math.floor(allocation_amt / price)
                cost = shares * price
                total_cost += cost
                print(f"{ticker:<10} | {weight:<15.2%} | {shares:<15} | ${cost:<15.2f}")
        
        print("-" * 65)
        print(f"Total Cost: ${total_cost:.2f}")
        print(f"Remaining Cash: ${investment_amount - total_cost:.2f}")
        
        print("\n--- PORTFOLIO METRICS ---")
        print(f"Expected Annual Return: {result['expected_return']:.2%}")
        print(f"Annual Volatility:      {result['volatility']:.2%}")
        print(f"Sharpe Ratio:           {result['sharpe_ratio']:.2f}")
        print(f"Value at Risk (95%):    {result['var_95']:.2%}")
        
        if show_plot:
            input("\nPress Enter to close the plot and continue...")
            matplotlib.pyplot.close()

    else:
        print("Optimization failed.")

def rebalance_portfolio():
    tickers = get_tickers_input()
    if not tickers:
        return
    
    current_shares = {}
    for ticker in tickers:
        shares = get_user_input(f"Enter Current Shares for {ticker}: ", int)
        current_shares[ticker] = shares
        
    max_allocation_pct = get_user_input("Enter Max Allocation % (e.g., 50): ", float)
    max_allocation = max_allocation_pct / 100.0
    show_plot_input = get_user_input("Show Efficient Frontier Plot? (y/n): ").lower()
    show_plot = show_plot_input == 'y'

    if not fetch_and_store_data(tickers):
        return

    result = backend.optimize_portfolio(max_allocation=max_allocation, show_plot=show_plot)

    if result:
        current_prices = result['prices']
        valid_tickers = [t for t in tickers if t in current_prices] # so it doesn't return an error if it's an invalid ticker
        
        total_portfolio_value = sum(current_shares[t] * current_prices[t] for t in valid_tickers)
        
        print(f"\nTotal Portfolio Value: ${total_portfolio_value:.2f}")
        
        print("\n--- REBALANCING ORDERS ---")
        print(f"{'Ticker':<10} | {'Current Shares':<12} | {'Trade Action':<15} | {'Optimal Shares':<12} | {'Optimal Allocation %':<12}")
        print("-" * 75)
        
        for ticker in valid_tickers:
            if ticker not in result['weights']:
                continue
                
            target_weight = result['weights'][ticker]
            target_value = total_portfolio_value * target_weight
            current_value = current_shares[ticker] * current_prices[ticker]
            
            diff_value = target_value - current_value
            price = current_prices[ticker]
            
            action_qty = 0
            if abs(diff_value) >= price:
                action_qty = math.floor(abs(diff_value) / price)
                if diff_value < 0:
                    action_qty = -action_qty
            
            new_shares = current_shares[ticker] + action_qty
            new_allocation = (new_shares * price) / total_portfolio_value if total_portfolio_value > 0 else 0
            
            action_str = f"{action_qty:+d}"
            
            print(f"{ticker:<10} | {current_shares[ticker]:<12} | {action_str:<15} | {new_shares:<12} | {new_allocation:<12.2%}")

        print("-" * 75)
        
        print("\n--- TARGET PORTFOLIO METRICS ---")
        print(f"Expected Annual Return: {result['expected_return']:.2%}")
        print(f"Annual Volatility:      {result['volatility']:.2%}")
        print(f"Sharpe Ratio:           {result['sharpe_ratio']:.2f}")
        print(f"Value at Risk (95%):    {result['var_95']:.2%}")
        
        if show_plot:
            input("\nPress Enter to close the plot and continue...")
            matplotlib.pyplot.close()

    else:
        print("Optimization failed.")

def main():
    while True:
        print("\n--- PORTFOLIO OPTIMIZATION TOOLKIT ---")
        print("1. Optimize New Portfolio")
        print("2. Rebalance Existing Portfolio")
        print("3. Quit")
        
        choice = get_user_input("Enter your choice: ")
        
        if choice == '1':
            optimize_new_portfolio()
        elif choice == '2':
            rebalance_portfolio()
        elif choice == '3':
            print("Exiting...")
            break
        else:
            print("Invalid input. Please try again.")

if __name__ == "__main__":
    main()
