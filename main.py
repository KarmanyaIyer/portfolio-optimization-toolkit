import yfinance
import pandas
import sqlite3
import datetime
import logging
import database

# PJ imports
import backend

# -----------------

logging.basicConfig(filename="main.log", level=logging.INFO, format="%(asctime)s - `%(name)s` in %(filename)s - %(levelname)s - %(message)s") # '%(asctime)s - %(filename)s - %(name)s - %(levelname)s - %(message)s'

logger = logging.getLogger(__name__)

def main():
    end = datetime.datetime.now()
    start = end - datetime.timedelta(days=365*10)
    
    # Scrape and store stock prices
    stockdata = database.scrape_historical_stock_prices(['TSLA', 'AMZN', 'LLY'], start, end)
    database.append_to_sql_database(stockdata, "stock_prices")

    # Scrape and store risk-free rate
    rf_data = database.scrape_risk_free_rate(start, end)
    database.append_to_sql_database(rf_data, "risk_free_rate")

    # Run optimization
    backend.optimize_portfolio()

if __name__ == "__main__":
    main()