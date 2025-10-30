import requests
import random
from decimal import Decimal
import logging

# Import from root
from stock_config import StockConfig

class StockService:
    def __init__(self):
        self.config = StockConfig()
    
    def get_stock_price(self, symbol):
        """Get real-time stock price from Alpha Vantage API"""
        try:
            # Using Alpha Vantage free API
            response = requests.get(
                f'{self.config.ALPHA_VANTAGE_BASE_URL}',
                params={
                    'function': 'GLOBAL_QUOTE',
                    'symbol': symbol,
                    'apikey': self.config.ALPHA_VANTAGE_API_KEY
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'Global Quote' in data and data['Global Quote']:
                    quote = data['Global Quote']
                    price = Decimal(str(quote.get('05. price', 0)))
                    change = Decimal(str(quote.get('09. change', 0)))
                    change_percent = Decimal(str(quote.get('10. change percent', '0%')).rstrip('%'))
                    
                    return {
                        'price': price,
                        'change': change,
                        'change_percent': change_percent
                    }
            
            # Fallback to mock data if API fails
            return self.get_mock_stock_price(symbol)
            
        except Exception as e:
            logging.error(f"Failed to fetch stock price for {symbol}: {e}")
            return self.get_mock_stock_price(symbol)
    
    def get_mock_stock_price(self, symbol):
        """Generate mock stock price data for demo"""
        base_price = Decimal(str(self.config.MOCK_STOCK_PRICES.get(symbol, 100.00)))
        
        # Simulate small price movement (±2%)
        change_percent = Decimal(str(random.uniform(-2.0, 2.0)))
        change = base_price * (change_percent / 100)
        price = base_price + change
        
        return {
            'price': price,
            'change': change,
            'change_percent': change_percent
        }
    
    def get_all_stock_prices(self):
        """Get prices for all supported stocks"""
        stock_prices = {}
        for stock in self.config.POPULAR_STOCKS:
            symbol = stock['symbol']
            price_data = self.get_stock_price(symbol)
            stock_prices[symbol] = {
                'symbol': symbol,
                'name': stock['name'],
                'price': float(price_data['price']),
                'change': float(price_data['change']),
                'change_percent': float(price_data['change_percent'])
            }
        return stock_prices
    
    def calculate_order_total(self, symbol, quantity):
        """Calculate total cost for a stock order"""
        price_data = self.get_stock_price(symbol)
        total = Decimal(str(quantity)) * price_data['price']
        return float(total)
    
    def initialize_stocks(self):
        """Initialize stock data in database"""
        from config import get_db_connection
        conn = get_db_connection()
        if not conn:
            return False
            
        try:
            cursor = conn.cursor()
            for stock in self.config.POPULAR_STOCKS:
                price_data = self.get_stock_price(stock['symbol'])
                cursor.execute("""
                    INSERT INTO stocks (symbol, company_name, current_price, daily_change, daily_change_percent)
                    VALUES (%s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    current_price = VALUES(current_price),
                    daily_change = VALUES(daily_change),
                    daily_change_percent = VALUES(daily_change_percent),
                    last_updated = CURRENT_TIMESTAMP
                """, (
                    stock['symbol'],
                    stock['name'],
                    float(price_data['price']),
                    float(price_data['change']),
                    float(price_data['change_percent'])
                ))
            conn.commit()
            return True
        except Exception as e:
            logging.error(f"Failed to initialize stocks: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

# Global stock service instance
stock_service = StockService()
