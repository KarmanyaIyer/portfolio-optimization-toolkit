import yfinance
import pandas
import sqlite3
import datetime
import logging
logger = logging.getLogger(__name__)

DatabaseName = "portfolio_database.db"

def scrape_historical_stock_prices(tickers, start_date, end_date):
    logger.info(f"Fetching adj close for {tickers} from {start_date} to {end_date}")
    stock_data = yfinance.download(tickers, start=start_date, end=end_date, auto_adjust=True)
    try:
        closing_data = stock_data["Close"]
        return closing_data
    except: # just in case
        logger.warning(f"Could not fetch tickers closing data.")
        return stock_data

def scrape_risk_free_rate(start_date, end_date):
    logger.info(f"Fetching 10-year treasury yield from {start_date} to {end_date}")
    tnx = yfinance.download("^TNX", start=start_date, end=end_date, auto_adjust=True)
    try:
        rf_data = tnx["Close"] / 100
        return rf_data
    except: # just in case
        logger.warning(f"Could not fetch ^TNX closing data.")
        return tnx

def append_to_sql_database(data, table_name):
    connection = sqlite3.connect(DatabaseName)
    data.to_sql(table_name, connection, if_exists='replace', index=True)
    connection.close()
    logger.info(f"Data appended to {table_name} in {DatabaseName}")


def get_table_from_database(table_name):
    connection = sqlite3.connect(DatabaseName)
    data = pandas.read_sql(f"SELECT * FROM {table_name}", connection, index_col='Date')
    connection.close()
    return data
