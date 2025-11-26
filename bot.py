import hashlib
import hmac
import requests
import time
import random
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class DeltaRestClient:
    def __init__(self, api_key, api_secret, base_url):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip('/')
        
    def generate_signature(self, secret, message):
        message = bytes(message, 'utf-8')
        secret = bytes(secret, 'utf-8')
        hash = hmac.new(secret, message, hashlib.sha256)
        return hash.hexdigest()
    
    def get_products(self):
        """Fetch all available products"""
        method = 'GET'
        timestamp = str(int(time.time()))
        path = '/v2/products'
        url = f'{self.base_url}{path}'
        query_string = ''
        payload = ''
        
        signature_data = method + timestamp + path + query_string + payload
        signature = self.generate_signature(self.api_secret, signature_data)
        
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=(3, 27))
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch products: {e}")
    
    def place_order(self, product_id, side, size, order_type='market_order', limit_price=None):
        """Place an order"""
        method = 'POST'
        timestamp = str(int(time.time()))
        path = '/v2/orders'
        url = f'{self.base_url}{path}'
        query_string = ''
        
        order_data = {
            "product_id": product_id,
            "side": side,
            "size": size,
            "order_type": order_type
        }
        
        if order_type == 'limit_order' and limit_price:
            order_data["limit_price"] = str(limit_price)
        
        payload = str(order_data).replace("'", '"')
        
        signature_data = method + timestamp + path + query_string + payload
        signature = self.generate_signature(self.api_secret, signature_data)
        
        headers = {
            'api-key': self.api_key,
            'timestamp': timestamp,
            'signature': signature,
            'User-Agent': 'python-rest-client',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(url, data=payload, headers=headers, timeout=(3, 27))
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"Failed to place order: {e}")

def pick_random_tradable_product(client):
    """Pick a random tradable product from available products"""
    logger.info("Fetching products...")
    
    try:
        products_resp = client.get_products()
        
        if not products_resp.get('success'):
            raise Exception(f"API error: {products_resp}")
            
        products = products_resp.get('result', [])
        
        # Filter for live and operational products
        tradable_products = [
            p for p in products 
            if p.get('state') == 'live' and 
               p.get('trading_status') == 'operational' and
               p.get('contract_type') in ['perpetual_futures', 'futures']  # Focus on futures
        ]
        
        if not tradable_products:
            raise Exception("No tradable products found")
        
        selected_product = random.choice(tradable_products)
        logger.info(f"Selected product: {selected_product['symbol']} (ID: {selected_product['id']})")
        
        return selected_product
        
    except Exception as e:
        logger.error(f"Error selecting product: {e}")
        raise

def execute_random_trade(client, product):
    """Execute a random trade on the selected product"""
    try:
        # Random trade parameters
        side = random.choice(['buy', 'sell'])
        size = random.randint(1, 5)  # Small size for testing
        
        logger.info(f"Placing {side} order for {size} contracts of {product['symbol']}")
        
        # Place market order
        order_resp = client.place_order(
            product_id=product['id'],
            side=side,
            size=size,
            order_type='market_order'
        )
        
        if order_resp.get('success'):
            order = order_resp.get('result', {})
            logger.info(f"Order placed successfully: {order.get('id')}")
            return order
        else:
            logger.error(f"Order failed: {order_resp}")
            return None
            
    except Exception as e:
        logger.error(f"Error executing trade: {e}")
        return None

def main():
    """Main bot execution function"""
    try:
        # Get credentials from environment variables
        api_key = os.getenv('DELTA_API_KEY')
        api_secret = os.getenv('DELTA_API_SECRET')
        base_url = os.getenv('DELTA_BASE_URL', 'https://api.india.delta.exchange')
        
        if not api_key or not api_secret:
            raise Exception("API credentials not found in environment variables")
        
        # Initialize client
        client = DeltaRestClient(api_key, api_secret, base_url)
        
        # Pick a random tradable product
        product = pick_random_tradable_product(client)
        
        # Execute a random trade
        order = execute_random_trade(client, product)
        
        if order:
            logger.info("Bot execution completed successfully")
        else:
            logger.error("Bot execution failed")
            
    except Exception as e:
        logger.error(f"Error in bot run: {e}")
        raise

if __name__ == "__main__":
    main()
