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
        if stock_data.empty:
            logger.warning("Downloaded stock data is empty.")
            return pandas.DataFrame()

        # Handle multi-index columns if present (common with yfinance for multiple tickers)
        if isinstance(stock_data.columns, pandas.MultiIndex):
            if 'Close' in stock_data.columns.get_level_values(0):
                closing_data = stock_data['Close']
            else:
                # Fallback or specific handling if structure differs
                closing_data = stock_data
        elif "Close" in stock_data.columns:
            closing_data = stock_data["Close"]
        else:
            # If single ticker and no 'Close' column, it might be the series itself or different format
            closing_data = stock_data

        # Drop columns (tickers) that are all NaN
        closing_data = closing_data.dropna(axis=1, how='all')
        
        # Identify and log dropped tickers
        downloaded_tickers = set(closing_data.columns)
        requested_tickers = set(tickers)
        missing_tickers = requested_tickers - downloaded_tickers
        if missing_tickers:
            logger.warning(f"Failed to fetch valid data for: {missing_tickers}")

        return closing_data
    except Exception as e:
        logger.error(f"Error processing stock data: {e}")
        return pandas.DataFrame()

def scrape_risk_free_rate(start_date, end_date):
    logger.info(f"Fetching 10-year treasury yield from {start_date} to {end_date}")
    tnx = yfinance.download("^TNX", start=start_date, end=end_date, auto_adjust=True)
    try:
        if "Close" in tnx.columns:
             rf_data = tnx["Close"] / 100
        else:
             rf_data = tnx / 100 # Fallback
        return rf_data
    except: # just in case
        logger.warning(f"Could not fetch ^TNX closing data.")
        return tnx

def append_to_sql_database(data, table_name):
    if data.empty:
        logger.warning(f"No data to append to {table_name}")
        return

    connection = sqlite3.connect(DatabaseName)
    data.to_sql(table_name, connection, if_exists='replace', index=True)
    connection.close()
    logger.info(f"Data appended to {table_name} in {DatabaseName}")


def get_table_from_database(table_name):
    connection = sqlite3.connect(DatabaseName)
    try:
        data = pandas.read_sql(f"SELECT * FROM {table_name}", connection, index_col='Date')
    except Exception as e:
        logger.warning(f"Could not read table {table_name}: {e}")
        data = pandas.DataFrame()
    connection.close()
    return data
