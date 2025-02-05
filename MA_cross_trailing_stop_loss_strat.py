# -*- coding: utf-8 -*-
"""
Created on Tue Jan 21 11:50:33 2025
 
@author: Sean Spencer
"""
 
 # Importing libraries
import requests
import pandas as pd
import pandas_ta as ta
from time import sleep, time
 
# Session & API Configuration
# API key was obtained from RIT (Rotman Interactive Trader) trading simulator endpoint
API_KEY = "APIKEY"
BASE_URL = "http://localhost:9999/v1"
s = requests.Session()
s.headers.update({'X-API-key': API_KEY})
 
# Strategy Parameters
TICKERS = ["OWL", "CROW", "DOVE", "DUCK"]
SHORT_WINDOW = 6   # for short MA
LONG_WINDOW = 15    # for long MA
SPREAD_OFFSET = 0.02
ORDER_SIZE = 2500
MAX_LONG_POSITION = 5000   # per ticker
MAX_SHORT_POSITION = -5000 # per ticker
 
 
# Fetching & Prepping Historical Data
 
def fetch_historical_prices(ticker, period=None, lookback=100):
    """
    Fetches OHLC historical data for 'ticker' from the /securities/ohlc endpoint.
    Returns a DataFrame with columns:
      - 'timestamp' (datetime)
      - 'open' (float)
      - 'high' (float)
      - 'low' (float)
      - 'close' (float)
    """
    # Prepare query parameters
    params = {
        'ticker': ticker,
        'limit': lookback
    }

    # If period is provided, include it
    if period is not None:
        params['period'] = period
 
    # Make the request to the OHLC endpoint
    resp = s.get(f"{BASE_URL}/securities/history", params=params)
    if not resp.ok:
        print(f"Error fetching OHLC data for {ticker}. Status code: {resp.status_code}")
        return pd.DataFrame()  # Return empty DataFrame on error
 
    data = resp.json()
    if not data:
        print(f"No data returned for {ticker} (OHLC).")
        return pd.DataFrame()
 
    # Convert the JSON list to a DataFrame
    df = pd.DataFrame(data)
 
    # Convert 'timestamp' column to datetime if it exists
    if "tick" in df.columns:
        df["tick"] = pd.to_datetime(df["tick"], unit='ms', errors='coerce')
        df.sort_values("tick", inplace=True)
    else:
        print("Warning: 'timestamp' column not found. Data may be missing time info.")
 
    # Check if the basic OHLC columns exist
    expected_cols = {"open", "high", "low", "close"}
    missing = expected_cols - set(df.columns)
    if missing:
        print(f"Warning: Missing columns in OHLC data: {missing}")
 
    return df
 
 
# Calculating Moving Averages (Golden Cross / Death Cross)
 
def compute_ma_cross(df, short_window=5, long_window=10):
    """
    Given a DataFrame with a 'close' column, compute short and long SMAs
    using pandas_ta, then return the two new columns and the most recent signals.
    """
    if df.empty or "close" not in df.columns:
        return df, None, None
 
    # Using pandas_ta
    df[f"SMA_{short_window}"] = ta.sma(df["close"], length=short_window)
    df[f"SMA_{long_window}"] = ta.sma(df["close"], length=long_window)
 
    # The last row
    recent = df.iloc[-1]
    short_ma = recent[f"SMA_{short_window}"]
    long_ma = recent[f"SMA_{long_window}"]
 
    return df, short_ma, long_ma


# Computing ADX (Average Directional Index) - use is optional
def compute_adx(df):
    adx_df = ta.adx(df["high"], df["low"], df["close"], length=4)
    adx_now = adx_df['ADX_4'].iloc[-1]
    print(adx_now)
    return adx_df, adx_now
 
# Simple Decision Logic Based on Crossover
 
def get_trade_signal(short_ma, long_ma):
    """
    Returns 'BUY', 'SELL', or 'NONE' based on a simple golden/death cross logic.
    - Golden cross: short_ma > long_ma => bullish => 'BUY'
    - Death cross: short_ma < long_ma => bearish => 'SELL'
    """
    if pd.isna(short_ma) or pd.isna(long_ma):
        return "NONE"  # Not enough data
    if short_ma > long_ma:
        return "BUY"
    elif short_ma < long_ma:
        return "SELL"
    return "NONE"
 
 
# Helper: Get best bid/ask
 
def get_best_bid_ask(ticker):
    resp = s.get(f"{BASE_URL}/securities/book", params={"ticker": ticker})
    if not resp.ok:
        print(f"Error fetching bid/ask for {ticker}")
        return None, None
    book = resp.json()
    bids = book.get("bids", [])
    asks = book.get("asks", [])
    if not bids or not asks:
        return None, None
    best_bid = bids[0]["price"]
    best_ask = asks[0]["price"]
    return best_bid, best_ask
 
 
# Helper: Fetches current position for a given ticker symbol
 
def get_current_position(ticker):
    """
    Returns the current position for a given ticker.
    """
    resp = s.get(f"{BASE_URL}/securities", params={"ticker": ticker})
    if not resp.ok:
        return 0
    data = resp.json()
    if not data:
        return 0
    # data might be a list with one item if you used the ticker param
    return data[0].get("position", 0)
 
 
# Placing Orders
 
def place_limit_order(ticker, action, limit_price, quantity):
    """
    Places a limit order; returns order_id if successful.
    """
    params = {
        "ticker": ticker,
        "type": "LIMIT",
        "quantity": quantity,
        "price": limit_price,
        "action": action
    }
    resp = s.post(f"{BASE_URL}/orders", params=params)
    if resp.ok:
        order_info = resp.json()
        order_id = order_info.get("order_id")
        print(f"Placed {action} order for {ticker} at {limit_price}. OrderID: {order_id}")
        return order_id
    else:
        print(f"Failed to place {action} order. {resp.text}")
    return None
 
 
def flatten_position(ticker):
    """
    Immediately close (flatten) the entire position for a 'ticker' by
    placing an offset limit order near the inside market (or a market order).
    """
    pos = get_current_position(ticker)  # e.g., +500 if you're long, -300 if short
    if pos == 0:
        return  # Already flat
 
    best_bid, best_ask = get_best_bid_ask(ticker)
    if best_bid is None or best_ask is None:
        print(f"Cannot flatten {ticker}: no market data.")
        return
 
    if pos > 0:
        # We are long => SELLING to reach zero
        if abs(pos) > 5000:
            exit_price = round(best_bid - 0.01, 2)
            place_limit_order(ticker, "SELL", exit_price, abs(pos) - (abs(pos)-4500))
        exit_price = round(best_bid - 0.01, 2)
        place_limit_order(ticker, "SELL", exit_price, abs(pos))
    else:
        # We are short => BUYING to reach zero.
        if abs(pos) > 5000:
            exit_price = round(best_ask - 0.01, 2)
            place_limit_order(ticker, "Buy", exit_price, abs(pos) - (abs(pos)-4500))
        exit_price = round(best_ask + 0.01, 2)
        place_limit_order(ticker, "BUY", exit_price, abs(pos))
 
trail_map = {}  # Dictionary to track the "anchor" price per ticker for trailing stop-loss
                # For LONG positions: highest price seen since entry
                # For SHORT positions: lowest price seen since entry
 
def update_trailing_stop(ticker, current_price, trailing_percent=0.01):
    """
    Applies a trailing stop to the given ticker based on 'trailing_percent'.
    - If 'pos' > 0 (LONG), we track the highest price since entry.
      If current_price moves below 'highest_price * (1 - trailing_percent)', flatten current position.
    - If 'pos' < 0 (SHORT), we track the lowest price since entry.
      If current_price moves above 'lowest_price * (1 + trailing_percent)', flatten current position.
    """
    pos = get_current_position(ticker)
    if pos == 0:
        # No position => no trailing stop to maintain
        if ticker in trail_map:
            del trail_map[ticker]
        return
 
    # If we haven't set an anchor price yet, initialize with current price
    if ticker not in trail_map:
        trail_map[ticker] = current_price
 
    if pos > 0:
        # Case: position is LONG:
        # 1) If we made a new high, update it
        if current_price > trail_map[ticker]:
            trail_map[ticker] = current_price
 
        # 2) Compute trailing stop level
        trailing_stop = trail_map[ticker] * (1 - trailing_percent)
 
        # 3) If current price falls below that level, flatten
        if current_price <= trailing_stop:
            print(f"Trailing stop triggered for LONG {ticker} at {current_price}")
            flatten_position(ticker)
            if ticker in trail_map:
                del trail_map[ticker]
 
    else:
        # Case: Position is SHORT:
        # If we make a new low, update it
        if current_price < trail_map[ticker]:
            trail_map[ticker] = current_price
 
        # The trailing stop is triggered if price goes UP above:
        #   lowest_price * (1 + trailing_percent)
        trailing_stop = trail_map[ticker] * (1 + trailing_percent)
 
        if current_price >= trailing_stop:
            print(f"Trailing stop triggered for SHORT {ticker} at {current_price}")
            flatten_position(ticker)
            if ticker in trail_map:
                del trail_map[ticker]
 
# Main Trading Loop
 
def main_trading_loop():
    while True:
        for ticker in TICKERS:
            # 1. Fetch historical data & compute MAs
            df = fetch_historical_prices(ticker, lookback=100)
            df, short_ma, long_ma = compute_ma_cross(df, SHORT_WINDOW, LONG_WINDOW)
            adx_df, adx_now = compute_adx(df)
           
            best_bid, best_ask = get_best_bid_ask(ticker)
           
            current_price = (best_bid + best_ask) / 2.0
            update_trailing_stop(ticker, current_price, trailing_percent=0.02)
 
            if short_ma is None or long_ma is None:
                print(f"Not enough data for MA cross on {ticker}")
                continue
           
 
            # 2. Get the trade signal, combining simple signal and ADX signal
            signal = get_trade_signal(short_ma, long_ma)
            if adx_now < 30:
                signal = 'NONE'
           
            print(f"{ticker} => Short MA: {short_ma:.2f}, Long MA: {long_ma:.2f}, Signal: {signal}")
 
            # 3. Get best bid/ask, position
            best_bid, best_ask = get_best_bid_ask(ticker)
            current_pos = get_current_position(ticker)
 
            if best_bid is None or best_ask is None:
                continue
 
            if signal == "BUY":
                # Check if within max long position
                if current_pos < MAX_LONG_POSITION:
                    # Place a BUY limit below the best bid
                    buy_price = round(best_bid - SPREAD_OFFSET, 2)
                    place_limit_order(ticker, "BUY", buy_price, (1-(short_ma-long_ma)) * ORDER_SIZE)
 
            elif signal == "SELL":
                # Check if within max short position
                if current_pos > MAX_SHORT_POSITION:
                    # Place a SELL limit above the best ask
                    sell_price = round(best_ask + SPREAD_OFFSET, 2)
                    place_limit_order(ticker, "SELL", sell_price, (1+(long_ma-short_ma)) * ORDER_SIZE)
 
            sleep(2)
 
        # Sleep between ticker cycles
        sleep(10)
 
if __name__ == "__main__":
    main_trading_loop()