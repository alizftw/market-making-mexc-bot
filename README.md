# MEXC Spot Market Making Bot 🤖

This is a Python-based algorithmic trading bot designed for market making on the **MEXC Spot Exchange**. It employs a sophisticated strategy that goes beyond simple order placement, incorporating dynamic risk management features to adapt to changing market conditions.

The bot includes a fully-featured **simulation mode**, allowing for extensive testing and strategy refinement without risking real capital.

## Features ✨

* **MEXC Spot Integration:** Connects directly to the MEXC v3 API for live trading.
* **Realistic Simulation Mode:** A robust paper trading environment that uses live market data to simulate order fills and PNL.
* **Dynamic Spread Adjustment:** Automatically widens or narrows the bid-ask spread based on recent market volatility to protect against losses during turbulent periods.
* **Inventory Skewing:** Intelligently adjusts quoting prices based on the bot's current inventory to manage risk and maintain a target asset balance.
* **Cancel-and-Replace Logic:** Ensures the bot is never exposed to stale orders by cancelling all open orders at the start of each cycle before placing new ones.
* **Live PNL Tracking:** Provides real-time profit and loss calculations during a session to monitor performance.

---

## How It Works: The Trading Strategy 🧠

The bot operates in a continuous loop, making decisions based on real-time market data. Here’s a detailed breakdown of the logic in each cycle:

### 1. Clean Slate: Order Cancellation

At the beginning of every cycle (e.g., every 10 seconds), the first thing the bot does is **cancel all its previously placed open orders**. This is a critical risk management step that prevents stale orders from being filled at outdated, unprofitable prices if the market moves suddenly.

### 2. Market Analysis: Finding the "True" Mid-Price

The bot fetches the current order book for the specified trading pair (e.g., `LTCUSDT`). It identifies the highest bid price and the lowest ask price to calculate the **market mid-price**.

$Market\ Mid-Price = (Best\ Bid + Best\ Ask) / 2$

This price represents the current fair value consensus of the market.

### 3. Volatility Assessment: Dynamic Spread

Instead of using a fixed spread, the bot calculates a **dynamic spread** based on recent price volatility. It keeps a short history of the last `N` mid-prices.

* **Measure Volatility:** It finds the difference between the highest and lowest price in its recent history (`price_range`).
* **Adjust Spread:** This range is used to calculate a `volatility_component`, which is then added to a `base_spread`.

$Dynamic\ Spread = Base\ Spread + (Volatility\ Component * Dampening\ Factor)$

This means:
* In **choppy, volatile markets**, the spread automatically widens to protect the bot from losses.
* In **calm, stable markets**, the spread narrows to increase the chances of getting orders filled and capturing profit.

### 4. Inventory Management: Price Skewing

This is the core of the bot's risk management. The goal is to maintain a target portfolio balance (e.g., 50% in LTC, 50% in USDT).

1.  **Calculate Current Ratio:** The bot checks its current balances and calculates the value of its base asset (`LTC`) as a percentage of its total portfolio value.
2.  **Find the Delta:** It compares this current ratio to its `target_base_asset_value_ratio` (e.g., 0.5 for 50%). The difference is the `inventory_delta`.
3.  **Calculate Skew:** This delta is used to create a **price skew**.
    * If the bot holds **too much LTC** (delta > 0), it skews its quoting price *downwards*. This makes its sell price more attractive and its buy price less attractive, encouraging a sell.
    * If the bot holds **too little LTC** (delta < 0), it skews its quoting price *upwards* to encourage a buy.

The result is a new, skewed mid-price that is unique to our bot:

$Our\ Mid-Price = Market\ Mid-Price * (1 + Skew)$

### 5. Order Placement

Finally, the bot places its new buy and sell limit orders. These orders are calculated using **Our (Skewed) Mid-Price** and the **Dynamic Spread**.

$Buy\ Price = Our\ Mid-Price * (1 - Dynamic\ Spread / 2)$
$Sell\ Price = Our\ Mid-Price * (1 + Dynamic\ Spread / 2)$

This intelligent order placement ensures the bot is always working to return to its target inventory while adapting its risk exposure to market volatility.

---

## Prerequisites

* Python 3.7+
* The `requests` Python library

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/your-username/your-repo-name.git](https://github.com/your-username/your-repo-name.git)
    ```
2.  **Navigate into the directory:**
    ```bash
    cd your-repo-name
    ```
3.  **Install the required library:**
    ```bash
    pip install requests
    ```

---

## Configuration

All configuration is done directly within the Python script.

### 1. Set Trading Mode

Set the `DEMO_MODE` flag at the top of the file:
* `DEMO_MODE = True`: Runs the bot in simulation mode using paper balances. **No real money is used.**
* `DEMO_MODE = False`: Executes live trades on your MEXC account.

### 2. Add API Keys (Live Mode Only)

If you set `DEMO_MODE` to `False`, you must provide your MEXC API keys.

```python
API_KEY = 'YOUR_API_KEY'
API_SECRET = 'YOUR_API_SECRET'
```

> **🔒 Security Warning:**
> Never share your API keys or commit them to a public repository. Ensure the API key permissions **do not** include withdrawal rights. It is highly recommended to link your API key to a specific IP address for added security.

### 3. Tune Strategy Parameters

At the very bottom of the script, in the `if __name__ == "__main__":` block, you can adjust the bot's trading parameters:

* `symbol`: The trading pair you want to trade (e.g., `'LTCUSDT'`).
* `base_spread`: The minimum spread the bot will use when market volatility is zero. This should be wider than the exchange's trading fees (e.g., `0.002` for 0.2%).
* `quote_quantity`: The size of your orders in the quote currency (e.g., `5` for $5 worth of LTC per order).
* `interval`: The time in seconds between each trading cycle.
* `inventory_skew_intensity`: A factor that controls how aggressively the bot skews its price to manage inventory. Higher values mean more aggressive skewing.
* `volatility_window`: The number of recent price points to use for the volatility calculation.

---

## Usage

To run the bot, simply execute the Python script from your terminal:

```bash
python your_script_name.py
```

The bot will start running and print its status, actions, and PNL to the console.

To stop the bot gracefully, press **`Ctrl+C`**. The bot will catch the signal, cancel any open orders, and print a final session summary.

---

## Disclaimer ⚠️

This software is provided for educational purposes only. Algorithmic trading is extremely risky and can result in significant financial losses. **You are solely responsible for any and all financial losses you may incur.**

Always run extensive tests in `DEMO_MODE` to understand how the bot behaves under different market conditions before considering live trading. The authors and contributors are not responsible for the performance of this bot. **This is not financial advice.**
