import pandas
import numpy
import scipy.optimize
import database
import logging
import matplotlib.pyplot

logger = logging.getLogger(__name__)

def get_portfolio_metrics(weights, expected_returns, covariance_matrix, risk_free_rate=0.04):
    portfolio_return = numpy.dot(weights, expected_returns)
    portfolio_volatility = numpy.sqrt(numpy.dot(weights.T, numpy.dot(covariance_matrix, weights)))
    sharpe_ratio = (portfolio_return - risk_free_rate) / portfolio_volatility
    return portfolio_return, portfolio_volatility, sharpe_ratio

def calculate_var(weights, returns, confidence_level=0.05):
    """
    Calculate the Historical Value at Risk (VaR).
    """
    portfolio_returns = returns.dot(weights)
    return portfolio_returns.quantile(confidence_level)

def maximize_sharpe_ratio(mean_returns, covariance_matrix, risk_free_rate=0.04, max_allocation=1.0):
    number_of_assets = len(mean_returns)
    args = (mean_returns, covariance_matrix, risk_free_rate)

    # Scipy optimization does not have a maximize function, so we just minimize it's inverse {minimize -f(x) to maximize f(x)}
    def negative_sharpe_ratio(weights, m_returns, cov_matrix, rf_rate):
        portfolio_return, portfolio_volatility, sharpe_ratio = get_portfolio_metrics(weights, m_returns, cov_matrix, rf_rate)
        return -1 * sharpe_ratio

    constraints = ({'type': 'eq', 'fun': lambda x: numpy.sum(x) - 1})
    bounds = tuple((0.0, max_allocation) for _ in range(number_of_assets)) # assumes no shorting
    initial_guess = [1.0 / number_of_assets] * number_of_assets
    result = scipy.optimize.minimize(negative_sharpe_ratio, initial_guess, args=args, method='SLSQP', bounds=bounds, constraints=constraints)
    return result

def plot_efficient_frontier(mean_returns, covariance_matrix, optimal_weights, num_portfolios=20000, risk_free_rate=0.04):
    logger.info(f"Generating {num_portfolios} random portfolios for Efficient Frontier...")
    
    num_assets = len(mean_returns)
    
    # Generate random weights
    weights = numpy.random.random((num_portfolios, num_assets))
    weights /= numpy.sum(weights, axis=1)[:, numpy.newaxis]
    
    # Vectorized calculation of returns
    portfolio_returns = numpy.dot(weights, mean_returns)

    # Variance = w^T * Cov * w.
    # Using einsum (Einstein summation) for efficient batch matrix multiplication: 'ij,jk,ik->i'
    # i: portfolio index, j: asset index 1, k: asset index 2
    # weights (i, j), covariance_matrix (j, k), weights (i, k)
    portfolio_variances = numpy.einsum('ij,jk,ik->i', weights, covariance_matrix, weights)
    portfolio_volatilities = numpy.sqrt(portfolio_variances)
    
    sharpe_ratios = (portfolio_returns - risk_free_rate) / portfolio_volatilities
    
    matplotlib.pyplot.figure(figsize=(12, 6.75), dpi=140)
    scatter = matplotlib.pyplot.scatter(portfolio_volatilities, portfolio_returns, c=sharpe_ratios, cmap='viridis', marker='.', s=5, alpha=0.9)
    matplotlib.pyplot.colorbar(scatter, label='Sharpe Ratio')

    # Plot optimal portfolio
    opt_ret, opt_vol, opt_sharpe = get_portfolio_metrics(optimal_weights, mean_returns, covariance_matrix, risk_free_rate)
    matplotlib.pyplot.scatter(opt_vol, opt_ret, marker='x', color='r', s=50, label='Maximum Sharpe Ratio')

    matplotlib.pyplot.title('Efficient Frontier with Monte Carlo Simulation')
    matplotlib.pyplot.xlabel('Volatility (Std. Dev)')
    matplotlib.pyplot.ylabel('Expected Return')
    matplotlib.pyplot.legend()
    matplotlib.pyplot.grid(True, linestyle='--', alpha=0.9)

    logger.info("Generating Efficient Frontier plot...")
    matplotlib.pyplot.show(block=False)
    matplotlib.pyplot.pause(0.1)

def optimize_portfolio(max_allocation=1.0, show_plot=False):
    try:
        df_prices = database.get_table_from_database("stock_prices")
    except Exception as e:
        logger.error(f"Failed to retrieve data from database: {e}")
        return None

    if df_prices.empty:
        logger.warning("Stock prices table is empty.")
        return None

    # Clean data before log returns
    df_prices = df_prices.dropna(axis=1, how='all') # Drop columns that are all NaN
    df_prices = df_prices.dropna() # Drop rows with any NaN

    if df_prices.empty:
        logger.warning("Stock prices table is empty after cleaning.")
        return None

    try:
        log_returns = numpy.log(df_prices / df_prices.shift(1))
        log_returns = log_returns.dropna()
    except Exception as e:
        logger.error(f"Error calculating log returns: {e}")
        return None

    if log_returns.empty:
        logger.warning("Log returns are empty.")
        return None

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

    optimization_result = maximize_sharpe_ratio(mean_returns, covariance_matrix, risk_free_rate, max_allocation)

    optimal_weights = optimization_result.x
    weights_dict = dict(zip(df_prices.columns, optimal_weights))

    # Calculate metrics for the optimal portfolio
    expected_return, expected_volatility, sharpe_ratio = get_portfolio_metrics(optimal_weights, mean_returns, covariance_matrix, risk_free_rate)
    
    var_95 = calculate_var(optimal_weights, log_returns)

    if show_plot:
        plot_efficient_frontier(mean_returns, covariance_matrix, optimal_weights, risk_free_rate=risk_free_rate)

    return {
        "weights": weights_dict,
        "expected_return": expected_return,
        "volatility": expected_volatility,
        "sharpe_ratio": sharpe_ratio,
        "var_95": var_95,
        "prices": df_prices.iloc[-1]
    }
