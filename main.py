import yfinance
import pandas
import sqlite3
import datetime
import logging
import math

# PJ imports
import database
import backend

# -------------------

logging.basicConfig(filename="main.log", level=logging.INFO, format="%(asctime)s - `%(name)s` in %(filename)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def get_user_input(prompt, type_func=str):
    while True:
        try:
            user_input = input(prompt)
            return type_func(user_input)
        except ValueError:
            print("Invalid input. Please try again.")

def optimize_new_portfolio():
    tickers_input = get_user_input("Enter Ticker List (comma separated): ")
    tickers = [t.strip().upper() for t in tickers_input.split(',')]
    investment_amount = get_user_input("Enter Investment Amount ($): ", float)
    max_allocation_pct = get_user_input("Enter Max Allocation % (e.g., 50): ", float)
    max_allocation = max_allocation_pct / 100.0

    end = datetime.datetime.now()
    start = end - datetime.timedelta(days=365*10)

    # Scrape and store stock prices
    stockdata = database.scrape_historical_stock_prices(tickers, start, end)
    database.append_to_sql_database(stockdata, "stock_prices")

    # Scrape and store risk-free rate
    rf_data = database.scrape_risk_free_rate(start, end)
    database.append_to_sql_database(rf_data, "risk_free_rate")

    result = backend.optimize_portfolio(max_allocation=max_allocation)

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
    else:
        print("Optimization failed.")

def rebalance_portfolio():
    tickers_input = get_user_input("Enter Ticker List (comma separated): ")
    tickers = [t.strip().upper() for t in tickers_input.split(',')]
    
    current_shares = {}
    for ticker in tickers:
        shares = get_user_input(f"Enter Current Shares for {ticker}: ", int)
        current_shares[ticker] = shares
        
    max_allocation_pct = get_user_input("Enter Max Allocation % (e.g., 50): ", float)
    max_allocation = max_allocation_pct / 100.0

    end = datetime.datetime.now()
    start = end - datetime.timedelta(days=365*10)

    # Scrape and store stock prices
    stockdata = database.scrape_historical_stock_prices(tickers, start, end)
    database.append_to_sql_database(stockdata, "stock_prices")

    # Scrape and store risk-free rate
    rf_data = database.scrape_risk_free_rate(start, end)
    database.append_to_sql_database(rf_data, "risk_free_rate")

    result = backend.optimize_portfolio(max_allocation=max_allocation)

    if result:
        current_prices = result['prices']
        total_portfolio_value = sum(current_shares[t] * current_prices[t] for t in tickers if t in current_prices)
        
        print(f"\nTotal Portfolio Value: ${total_portfolio_value:.2f}")
        
        print("\n--- REBALANCING ORDERS ---")
        print(f"{'Ticker':<10} | {'Action':<10} | {'Quantity':<10} | {'Est. Value':<15}")
        print("-" * 55)
        
        for ticker in tickers:
            if ticker not in result['weights']:
                continue
                
            target_weight = result['weights'][ticker]
            target_value = total_portfolio_value * target_weight
            current_value = current_shares[ticker] * current_prices[ticker]
            
            diff_value = target_value - current_value
            price = current_prices[ticker]
            
            if abs(diff_value) < price: # No action if difference is less than 1 share price
                continue
                
            action = "Buy" if diff_value > 0 else "Sell"
            quantity = math.floor(abs(diff_value) / price)
            
            if quantity > 0:
                est_value = quantity * price
                print(f"{ticker:<10} | {action:<10} | {quantity:<10} | ${est_value:<15.2f}")

        print("-" * 55)
        
        print("\n--- TARGET PORTFOLIO METRICS ---")
        print(f"Expected Annual Return: {result['expected_return']:.2%}")
        print(f"Annual Volatility:      {result['volatility']:.2%}")
        print(f"Sharpe Ratio:           {result['sharpe_ratio']:.2f}")
        print(f"Value at Risk (95%):    {result['var_95']:.2%}")

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
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()