from flask import Flask, render_template, request, jsonify
import numpy as np
import pandas as pd
import yfinance as yf
from pandas.tseries.offsets import BDay
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

# Function to get stock data and simulate Monte Carlo projections
def monte_carlo_simulation(stock, years, n_mc=10000):
    
    ticker = yf.Ticker(stock)
    actual_hist = ticker.history(start="2020-12-29", end="2024-09-20", auto_adjust=False)
    
    
    if actual_hist.empty:
        return None
    
    # Calculate log returns and volatility
    actual_hist['Log Returns'] = np.log(actual_hist['Close'] / actual_hist['Close'].shift(1))
    actual_hist.dropna(inplace=True)
    daily_volatility = actual_hist['Log Returns'].std()
    annual_volatility = daily_volatility * np.sqrt(252)
    sigma = annual_volatility
    mu = .008  # Drift (adjustable)

    # Time step
    future_days = years * 252
    n_t = len(actual_hist)
    dt = 2. / (n_t + future_days - 1)
    
    
    last_date = actual_hist.index[-1]
    future_dates = pd.date_range(last_date, periods=future_days + 1, freq=BDay())[1:]
    all_dates = actual_hist.index.append(future_dates)

    # Initialize Monte Carlo simulation
    St = pd.DataFrame(np.zeros((n_t + future_days, n_mc)), index=all_dates)
    St.iloc[0] = actual_hist['Close'].iloc[0]
    
    # Perform the simulation
    for i in range(1, n_t + future_days):
        dS_2_S = mu * dt + sigma * np.sqrt(dt) * np.random.randn(n_mc)
        St.iloc[i] = St.iloc[i-1] + St.iloc[i-1] * dS_2_S

    # Get mean and median
    St_mc_mean = St.mean(axis=1)
    St_mc_median = St.median(axis=1)
    
    # Plot results to a PNG
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(actual_hist.index, actual_hist['Close'], 'r', lw=1, label="Actual Price")
    for i in np.random.choice(np.array(range(1, n_mc+1)), size=20):
        ax.plot(St.index, St[i], 'b', lw=.5)
    ax.plot(St_mc_mean.index, St_mc_mean, 'g', lw=2, label="Monte Carlo Mean")
    ax.plot(St_mc_median.index, St_mc_median, 'orange', lw=2, label="Monte Carlo Median")
    ax.set_xlabel('Date')
    ax.set_ylabel('Stock Price')
    ax.set_title(f'Monte Carlo Simulation for {stock}: {years} Years into the Future')
    ax.legend()

    
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode('utf8')
    plt.close()

    return plot_url

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/simulate', methods=['POST'])
def simulate():
    stock = request.form['stock']
    years = int(request.form['years'])
    
    result = monte_carlo_simulation(stock, years)
    
    if result:
        return jsonify({'status': 'success', 'plot_url': result})
    else:
        return jsonify({'status': 'error', 'message': f'No data for stock: {stock}'})

if __name__ == '__main__':
    app.run(debug=True)
