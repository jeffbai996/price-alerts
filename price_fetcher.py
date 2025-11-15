"""
Simple price fetcher using yfinance.
Gets the current stock price for a given ticker.
"""

import yfinance as yf


def get_current_price(ticker):
    """
    Get the current price for a stock ticker.

    Args:
        ticker: Stock symbol like 'SPY', 'AAPL', etc.

    Returns:
        Current price as a float, or None if it fails
    """
    try:
        stock = yf.Ticker(ticker)
        price = stock.fast_info.get('lastPrice')
        return price
    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return None


if __name__ == "__main__":
    # Test it with SPY
    ticker = "SPY"
    price = get_current_price(ticker)

    if price:
        print(f"{ticker}: ${price:.2f}")
    else:
        print(f"Failed to get price for {ticker}")
