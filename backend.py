import pandas
import numpy
import scipy.optimize
import database
import logging

logger = logging.getLogger(__name__)

def get_portfolio_metrics(weights, expected_returns, covariance_matrix, risk_free_rate=0.04):
    portfolio_return = numpy.dot(weights, expected_returns)
    portfolio_volatility = numpy.sqrt(numpy.dot(weights.T, numpy.dot(covariance_matrix, weights)))
    sharpe_ratio = (portfolio_return - risk_free_rate) / portfolio_volatility
    return portfolio_return, portfolio_volatility, sharpe_ratio

def maximize_sharpe_ratio(mean_returns, covariance_matrix, risk_free_rate=0.04):
    number_of_assets = len(mean_returns)
    args = (mean_returns, covariance_matrix, risk_free_rate)

    # Scipy optimization does not have a maximize function, so we just minimize it's inverse {minimize -f(x) to maximize f(x)}
    def negative_sharpe_ratio(weights, mean_returns, covariance_matrix, risk_free_rate):
        portfolio_return, portfolio_volatility, sharpe_ratio = get_portfolio_metrics(weights, mean_returns, covariance_matrix, risk_free_rate)
        return -1 * sharpe_ratio

    constraints = ({'type': 'eq', 'fun': lambda x: numpy.sum(x) - 1})
    bounds = tuple((0.0, 1.0) for asset in range(number_of_assets)) # assumes no shorting
    initial_guess = [1.0 / number_of_assets] * number_of_assets
    result = scipy.optimize.minimize(negative_sharpe_ratio, initial_guess, args=args, method='SLSQP', bounds=bounds, constraints=constraints)
    return result


def optimize_portfolio():
    try:
        df_prices = database.get_table_from_database("stock_prices")
    except Exception as e:
        logger.error(f"Failed to retrieve data from database: {e}")
        return

    if df_prices.empty:
        logger.warning("Stock prices table is empty.")
        return


    log_returns = numpy.log(df_prices / df_prices.shift(1))
    log_returns = log_returns.dropna()


    mean_returns = log_returns.mean() * 252
    covariance_matrix = log_returns.cov() * 252


    logger.info("Running Max Sharpe Optimization...")
    
    # Fetch dynamic risk-free rate from database
    try:
        df_rf = database.get_table_from_database("risk_free_rate")
        if not df_rf.empty:
            # Get the most recent rate (last row, first column)
            risk_free_rate = df_rf.iloc[-1, 0]
        else:
            risk_free_rate = 0.04
    except Exception as e:
        logger.warning(f"Could not fetch risk-free rate from database, using default 0.04. Error: {e}")
        risk_free_rate = 0.04

    optimization_result = maximize_sharpe_ratio(mean_returns, covariance_matrix, risk_free_rate)

    optimal_weights = optimization_result.x


    print("\n--- OPTIMAL PORTFOLIO ALLOCATION ---")
    tickers = df_prices.columns
    for ticker, weight in zip(tickers, optimal_weights):
        # Only print if weight is significant (greater than 0.1%)
        if weight > 0.001:
            print(f"{ticker}: {weight:.2%}")

    # Calculate metrics for the optimal portfolio
    expected_return, expected_volatility, sharpe_ratio = get_portfolio_metrics(optimal_weights, mean_returns, covariance_matrix, risk_free_rate)
    
    print("------------------------------------")
    print(f"Expected Annual Return: {expected_return:.2%}")
    print(f"Annual Volatility:      {expected_volatility:.2%}")
    print(f"Sharpe Ratio (Rf={risk_free_rate:.2%}):   {sharpe_ratio:.2f}")

# Suggestions to user to add:
# 1. Efficient Frontier Plotting: Visualize the risk-return trade-off.
# 2. Monte Carlo Simulation: Project future portfolio performance.
# 3. Value at Risk (VaR): Calculate potential loss at a given confidence level.


if __name__ == "__main__":
    optimize_portfolio()