# bot.py
import os
import time
import random
import logging

# Try to import the official client. If import fails, instruct user.
try:
    from delta_rest_client import DeltaRestClient, OrderType
except Exception as e:
    raise SystemExit("Please install 'delta-rest-client' (pip install delta-rest-client). Error: " + str(e))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

API_KEY = os.getenv("DELTA_API_KEY")
API_SECRET = os.getenv("DELTA_API_SECRET")
BASE_URL = os.getenv("DELTA_BASE_URL", "https://testnet-api.delta.exchange")  # default to testnet

if not API_KEY or not API_SECRET:
    raise SystemExit("Set DELTA_API_KEY and DELTA_API_SECRET as environment variables (use testnet keys).")

client = DeltaRestClient(base_url=BASE_URL, api_key=API_KEY, api_secret=API_SECRET)

def pick_random_tradable_product():
    """
    Fetch products and pick a random tradeable product.
    We'll filter for products that allow trading and have a reasonable 'min_size' if available.
    """
    logging.info("Fetching products...")
    products_resp = client.get_products()  # library method; returns list/dict depending on client
    # Normalize: if dict with 'result' key, handle it
    products = products_resp.get('result') if isinstance(products_resp, dict) and 'result' in products_resp else products_resp

    if not products:
        raise RuntimeError("No products returned from API.")

    # Filter: keep products with tradable == True (best-effort)
    tradable = []
    for p in products:
        try:
            # example keys: 'symbol', 'product_id', 'tradeable'
            if p.get('tradeable', True):  # if key missing, assume tradable
                tradable.append(p)
        except Exception:
            continue

    if not tradable:
        tradable = products  # fallback

    chosen = random.choice(tradable)
    logging.info(f"Chosen product: {chosen.get('symbol') or chosen.get('name') or chosen.get('product_id')}")
    return chosen

def place_market_buy_and_sell(product):
    """
    Place a market buy order of a tiny size, then place market sell to close.
    Adjust 'size' conservatively (use product['min_size'] if provided).
    """
    pid = product.get('id') or product.get('product_id') or product.get('productId')  # different clients use different keys
    symbol = product.get('symbol') or product.get('name')

    # Determine size: try min_size or use a tiny default like 1 (you should customize per product)
    size = None
    for k in ('min_size', 'minimum_order_size', 'lot_size', 'min_order_size'):
        if k in product:
            try:
                size = float(product[k])
                break
            except Exception:
                pass
    if size is None:
        size = 1  # very small default — change as required

    # To be extremely safe for testing on testnet, reduce size further
    size = max(0.0001, float(size))  # ensure a small positive size

    logging.info(f"Placing MARKET BUY for product_id={pid}, symbol={symbol}, size={size}")
    try:
        # The library method name can be place_order or place_market_order. We'll try place_order with OrderType.MARKET
        order_resp = client.place_order(
            product_id=pid,
            side='buy',
            size=size,
            order_type=OrderType.MARKET
        )
    except Exception as e:
        logging.error("Buy order failed: %s", e)
        return

    logging.info("Buy response: %s", order_resp)

    # Wait briefly then place sell to close
    time.sleep(3)

    logging.info(f"Placing MARKET SELL for product_id={pid}, size={size}")
    try:
        sell_resp = client.place_order(
            product_id=pid,
            side='sell',
            size=size,
            order_type=OrderType.MARKET
        )
    except Exception as e:
        logging.error("Sell order failed: %s", e)
        return

    logging.info("Sell response: %s", sell_resp)

def main():
    try:
        product = pick_random_tradable_product()
        place_market_buy_and_sell(product)
    except Exception as e:
        logging.exception("Error in bot run: %s", e)

if __name__ == "__main__":
    main()
