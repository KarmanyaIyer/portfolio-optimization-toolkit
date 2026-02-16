# Portfolio Optimization Toolkit

## Overview
A Python-based financial modeling tool that constructs optimal portfolios using **Mean-Variance Optimization (MVO)**. It uses Monte Carlo simulations (plotted) to analyze risk/return trade-offs and calculates **Value at Risk (VaR)** to quantify downside potential.

## Installation
1. Clone this repo.
2. Run `pip install -r requirements.txt` to install the necessary libraries
3. Run main.py and follow the CLI prompts.

## Features
* **Data & Storage:** Scrapes financial data, stores it in SQL database.
* **Mathematical Optimization:** Uses optimization to maximize Sharpe Ratio.
* **Risk Analysis:** Calculates 95% Historical VaR and Volatility.
* **Monte Carlo Simulation:** Generates 20,000 random portfolios to visualize the Efficient Frontier in matplotlib.
* **Portfolio Rebalancing:** Calculates necessary trades (buy/sell) to transform current portfolio into the optimal portfolio.
* **Interactive CLI:** Rebalancing tool to calculate necessary trades (buy/sell) to transform current portfolio into the optimal portfolio.

### To Do:
* More models (CAPM, Black-Litterman, risk parity)
  * Additional asset types (derivatives, fixed income)
* Improve UI
* Additional constraints
* Market signals

### Libraries used
* **Python:** Pandas, NumPy, SciPy, Matplotlib, Logging, and more (in [requirements.txt]).
* **SQL:** SQLite for time-series data storage.


## Showcase
Some examples of portfolios and what the model outputs. Any number of stocks (2+) will work. These (and more) are portfolios that are included as presets (enter 'P' in the CLI) if you wish to use them as testcases.

### Portfolio A: wip
insert screenshot

### Portfolio B: wip
insert screenshot

### Portfolio C: wip
insert screenshot


------------------------------

## Disclaimers
For educational purposes only. Not financial advice. 
MIT License.
