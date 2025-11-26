import os
import random
import logging
from delta_rest_client import DeltaRestClient

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s"
)

# Load API credentials
API_KEY = os.getenv("DELTA_API_KEY")
API_SECRET = os.getenv("DELTA_API_SECRET")
BASE_URL = os.getenv("DELTA_BASE_URL", "https://api.deltaex.org")

client = DeltaRestClient(
    api_key=API_KEY,
    api_secret=API_SECRET,
    base_url=BASE_URL
)


# ---------------------------
# Fetch a random active product
# ---------------------------
def pick_random_product():
    logging.info("Fetching products...")

    try:
        response = client.list_products()  # CORRECT METHOD
    except Exception as e:
        logging.error(f"API error while fetching products: {e}")
        raise

    products = response.get("result", [])

    if not products:
        raise Exception("No products returned by API")

    active = [p for p in products if p.get("is_active")]

    if not active:
        raise Exception("No active tradable products found")

    chosen = random.choice(active)
    logging.info(f"Selected product: {chosen['symbol']}")

    return chosen


# ---------------------------
# Test BUY order
# ---------------------------
def place_buy(product):
    logging.info("Placing TEST BUY order...")

    payload = {
        "product_id": product["id"],
        "order_type": "market",
        "side": "buy",
        "size": 1  # test size
    }

    try:
        resp = client.create_order(payload)
        logging.info(f"BUY ORDER RESPONSE: {resp}")
        return resp
    except Exception as e:
        logging.error(f"Error placing BUY order: {e}")
        raise


# ---------------------------
# Test SELL order
# ---------------------------
def place_sell(product):
    logging.info("Placing TEST SELL order...")

    payload = {
        "product_id": product["id"],
        "order_type": "market",
        "side": "sell",
        "size": 1
    }

    try:
        resp = client.create_order(payload)
        logging.info(f"SELL ORDER RESPONSE: {resp}")
        return resp
    except Exception as e:
        logging.error(f"Error placing SELL order: {e}")
        raise


# ---------------------------
# Main bot logic
# ---------------------------
def main():
    logging.info("Bot started.")

    try:
        product = pick_random_product()

        # Test orders
        buy = place_buy(product)
        sell = place_sell(product)

        logging.info("Bot cycle complete.")

    except Exception as e:
        logging.error(f"Bot error: {e}", exc_info=True)


if __name__ == "__main__":
    main()
