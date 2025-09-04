import requests
import time
import hmac
import hashlib
import json
from collections import deque

# --- CONFIGURATION ---
DEMO_MODE = True # <<< SET TO False FOR LIVE TRADING >>>
API_KEY = 'YOUR_API_KEY' if not DEMO_MODE else 'DEMO_KEY'
API_SECRET = 'YOUR_API_SECRET' if not DEMO_MODE else 'DEMO_SECRET'
BASE_URL = 'https://api.mexc.com'

# --- REAL MEXC API FUNCTIONS ---
def sign(params, secret):
    query_string = '&'.join([f"{k}={v}" for k, v in sorted(params.items())])
    return hmac.new(secret.encode(), query_string.encode(), hashlib.sha256).hexdigest()

def get_server_time():
    url = f"{BASE_URL}/api/v3/time"
    return requests.get(url).json()['serverTime']

class LiveMexcClient:
    def place_order(self, symbol, side, price, quantity):
        path = '/api/v3/order'
        url = BASE_URL + path
        params = {
            'symbol': symbol,
            'side': side,
            'type': 'LIMIT',
            'price': str(price),
            'quantity': str(quantity),
            'timestamp': get_server_time()
        }
        params['signature'] = sign(params, API_SECRET)
        headers = {'X-MEXC-APIKEY': API_KEY}
        response = requests.post(url, params=params, headers=headers)
        return response.json()

    def cancel_all_orders(self, symbol):
        path = '/api/v3/openOrders'
        url = BASE_URL + path
        params = {
            'symbol': symbol,
            'timestamp': get_server_time()
        }
        params['signature'] = sign(params, API_SECRET)
        headers = {'X-MEXC-APIKEY': API_KEY}
        print("Cancelling all live orders...")
        response = requests.delete(url, params=params, headers=headers)
        print(response.json())
        return response.json()

# --- SIMULATED CLIENT ---
class SimulatedMexcClient:
    def __init__(self, symbol, initial_balances={'USDT': 5}):
        self.balances = initial_balances.copy()
        self.base_asset = symbol.replace('USDT', '')
        if self.base_asset not in self.balances:
            self.balances[self.base_asset] = 0
        self.open_orders = []
        self.order_id_counter = 1
        print("--- SIMULATED CLIENT INITIALIZED ---")
        print(f"Initial Balances: {self.balances}")

    def place_order(self, symbol, side, price, quantity):
        # Assumes symbol is 'BTCUSDT' for simplicity
        base_asset = symbol.replace('USDT', '')
        quote_asset = 'USDT'

        print(f"\nAttempting to place simulated {side} order: {quantity} {base_asset} @ {price} {quote_asset}")

        if side == 'BUY':
            cost = price * quantity
            if self.balances[quote_asset] >= cost:
                self.balances[quote_asset] -= cost
                order = {'id': self.order_id_counter, 'symbol': symbol, 'side': side, 'price': price, 'quantity': quantity}
                self.open_orders.append(order)
                self.order_id_counter += 1
                print(f"  > Success: Simulated BUY order placed. {quote_asset} balance: {self.balances[quote_asset]:.2f}")
                return {'status': 'success', 'orderId': order['id']}
            else:
                print(f"  > FAILED: Insufficient {quote_asset} balance.")
                return {'status': 'failed', 'error': 'Insufficient balance'}
        
        elif side == 'SELL':
            if self.balances.get(base_asset, 0) >= quantity:
                self.balances[base_asset] -= quantity
                order = {'id': self.order_id_counter, 'symbol': symbol, 'side': side, 'price': price, 'quantity': quantity}
                self.open_orders.append(order)
                self.order_id_counter += 1
                print(f"  > Success: Simulated SELL order placed. {base_asset} balance: {self.balances.get(base_asset, 0):.4f}")
                return {'status': 'success', 'orderId': order['id']}
            else:
                print(f"  > FAILED: Insufficient {base_asset} balance.")
                return {'status': 'failed', 'error': 'Insufficient balance'}

    def cancel_all_orders(self, symbol):
        """For simulation, just clear the list of open orders."""
        print("Cancelling all simulated open orders...")
        self.open_orders = []
        return {'status': 'success', 'message': 'All simulated orders cancelled'}

    def check_fills(self, order_book):
        if not self.open_orders:
            return

        print("\nChecking for simulated fills...")
        best_bid = float(order_book['bids'][0][0])
        best_ask = float(order_book['asks'][0][0])
        
        # Use a copy of the list to iterate over, so we can modify the original
        for order in list(self.open_orders):
            filled = False
            if order['side'] == 'BUY' and order['price'] >= best_ask:
                # Buy order filled if our price is at or above the market's lowest ask
                filled = True
                fill_price = best_ask
            elif order['side'] == 'SELL' and order['price'] <= best_bid:
                # Sell order filled if our price is at or below the market's highest bid
                filled = True
                fill_price = best_bid

            if filled:
                base_asset = order['symbol'].replace('USDT', '')
                quote_asset = 'USDT'
                quantity = order['quantity']
                
                if order['side'] == 'BUY':
                    # On a buy, the base asset increases
                    self.balances[base_asset] = self.balances.get(base_asset, 0) + quantity
                    print(f"  > FILLED: BUY order {order['id']} for {quantity:.6f} {base_asset} at {fill_price}")
                elif order['side'] == 'SELL':
                    # On a sell, the quote asset we held is now realized as cash
                    proceeds = quantity * fill_price
                    self.balances[quote_asset] += proceeds
                    print(f"  > FILLED: SELL order {order['id']} for {quantity:.6f} {base_asset} at {fill_price}. Proceeds: {proceeds:.2f} {quote_asset}")
                
                self.open_orders.remove(order)


# --- PUBLIC DATA & MAIN LOGIC ---
def get_order_book(symbol, limit=5):
    url = f"{BASE_URL}/api/v3/depth"
    params = {'symbol': symbol, 'limit': limit}
    return requests.get(url, params=params).json()

def get_last_trade_price(symbol):
    """Gets the most recently traded price of a symbol."""
    url = f"{BASE_URL}/api/v3/ticker/price"
    params = {'symbol': symbol}
    response = requests.get(url, params=params)
    data = response.json()
    return float(data['price'])

def market_make(symbol, spread=0.003, quote_quantity=5, interval=10, inventory_skew_intensity=0.5):
    # Select the client based on the mode
    initial_balances = {'USDT': 204.93, 'LTC': 0.46805458}
    client = SimulatedMexcClient(symbol, initial_balances=initial_balances) if DEMO_MODE else LiveMexcClient()

    # --- PNL & Inventory Tracking ---
    initial_portfolio_value = 0
    pnl_calculated = False
    # Define the target inventory ratio (e.g., 50% base, 50% quote)
    target_base_asset_value_ratio = 0.5 

    print("\nStarting smarter market making bot...")
    print("Press Ctrl+C to stop.")

    # Initialize market_mid_price to ensure it's available in the exception block
    market_mid_price = 0

    while True:
        try:
            # --- 1. Cancel all previous orders ---
            # This is crucial to prevent stale orders from filling at bad prices
            client.cancel_all_orders(symbol)

            print("\n" + "="*60)
            print(f"Timestamp: {time.ctime()}")
            print("Fetching order book...")
            book = get_order_book(symbol)
            
            if 'bids' not in book or 'asks' not in book or not book['bids'] or not book['asks']:
                print("Error: Invalid order book data received. Skipping this cycle.")
                time.sleep(interval)
                continue

            best_bid = float(book['bids'][0][0])
            best_ask = float(book['asks'][0][0])
            market_mid_price = (best_bid + best_ask) / 2
            
            # --- PNL Calculation (once at the start) ---
            if not pnl_calculated and DEMO_MODE:
                initial_portfolio_value = client.balances['USDT'] + (client.balances.get(client.base_asset, 0) * market_mid_price)
                pnl_calculated = True
                print(f"Initial Portfolio Value: ${initial_portfolio_value:.2f} USDT")

            # Check for fills before placing new orders in demo mode
            if DEMO_MODE:
                client.check_fills(book)

            # --- 2. Inventory Management & Price Skewing ---
            current_base_balance = client.balances.get(client.base_asset, 0)
            current_quote_balance = client.balances['USDT']
            total_portfolio_value = current_quote_balance + (current_base_balance * market_mid_price)

            # Calculate the current value of our base asset holdings as a percentage of the total portfolio
            current_base_asset_value_ratio = (current_base_balance * market_mid_price) / total_portfolio_value if total_portfolio_value else 0
            
            # Calculate how far we are from our target ratio
            inventory_delta = current_base_asset_value_ratio - target_base_asset_value_ratio
            
            # Skew the mid-price.
            # If we have too much base asset (delta > 0), we lower our price to encourage selling.
            # If we have too little base asset (delta < 0), we raise our price to encourage buying.
            skew = -inventory_delta * inventory_skew_intensity
            our_mid_price = market_mid_price * (1 + skew)

            # --- 3. Place new, smarter orders ---
            quantity = quote_quantity / our_mid_price
            buy_price = round(our_mid_price * (1 - spread / 2), 4)
            sell_price = round(our_mid_price * (1 + spread / 2), 4)

            print(f"Market: {symbol} | Mid: {market_mid_price:.4f}")
            print(f"Inventory: {current_base_asset_value_ratio*100:.2f}% {client.base_asset} | Target: {target_base_asset_value_ratio*100:.0f}% | Delta: {inventory_delta:+.3f}")
            print(f"Price Skew: {skew:+.4f} | Our Mid-Price: {our_mid_price:.4f}")
            print(f"Strategy: Placing orders for ~${quote_quantity} ({quantity:.6f} {client.base_asset})")
            print(f"           BUY at {buy_price}, SELL at {sell_price}")
            
            if DEMO_MODE:
                pnl = total_portfolio_value - initial_portfolio_value
                pnl_percent = (pnl / initial_portfolio_value) * 100 if initial_portfolio_value else 0
                
                print(f"Paper Balances: { {k: round(v, 5) for k, v in client.balances.items()} }")
                print(f"Open Simulated Orders: {len(client.open_orders)}")
                print(f"Session PNL: ${pnl:+.2f} USDT ({pnl_percent:+.2f}%)")
            
            print("="*60)

            # Place orders using the selected client
            client.place_order(symbol, 'BUY', buy_price, quantity)
            client.place_order(symbol, 'SELL', sell_price, quantity)

            print(f"\n--- Waiting for {interval} seconds before next cycle ---")
            time.sleep(interval)

        except KeyboardInterrupt:
            print("\nBot stopped by user.")
            if DEMO_MODE:
                client.cancel_all_orders(symbol) # Clean up simulated orders on exit
                
                # --- Final PNL Calculation ---
                # Use the last known mid-price to value the final portfolio
                if pnl_calculated and market_mid_price > 0:
                    final_portfolio_value = client.balances['USDT'] + (client.balances.get(client.base_asset, 0) * market_mid_price)
                    pnl = final_portfolio_value - initial_portfolio_value
                    pnl_percent = (pnl / initial_portfolio_value) * 100 if initial_portfolio_value else 0
                    print(f"\n--- Session Summary ---")
                    print(f"Final Balances: { {k: round(v, 5) for k, v in client.balances.items()} }")
                    print(f"Final Portfolio Value (at last price {market_mid_price:.4f}): ${final_portfolio_value:.2f} USDT")
                    print(f"Session PNL: ${pnl:+.2f} USDT ({pnl_percent:+.2f}%)")
                    print("-----------------------")
                else:
                    # Fallback if bot is stopped before first PNL calculation
                    print("\n--- Session Summary ---")
                    print("Final Balances:", client.balances)
                    print("PNL not calculated as the first cycle did not complete.")
                    print("-----------------------")

            else:
                # For live mode, it's crucial to cancel dangling orders
                print("\n--- Session Summary ---")
                print("Cancelling all live orders...")
                client.cancel_all_orders(symbol)
                print("Live PNL must be checked on the exchange.")
                print("-----------------------")
            break # Exit the while loop
        except Exception as e:
            print(f"An error occurred: {e}")
            print("Continuing in 10 seconds...")
            time.sleep(10)

# --- START THE BOT ---
if __name__ == "__main__":
    # Increased spread to cover fees (0.1% maker fee * 2 = 0.2%)
    market_make('LTCUSDT', spread=0.003, quote_quantity=5, interval=10)