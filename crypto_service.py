import requests
import time
from decimal import Decimal
import logging

# Import from root
from crypto_config import CryptoConfig

class CryptoService:
    def __init__(self):
        self.config = CryptoConfig()
    
    def get_live_prices(self):
        """Get live cryptocurrency prices from CoinGecko API"""
        try:
            # Prepare cryptocurrency IDs for API
            ids = ','.join([self.config.CRYPTO_IDS[currency] for currency in self.config.SUPPORTED_CRYPTO])
            
            # Make API request
            response = requests.get(
                f'{self.config.COINGECKO_API}?ids={ids}&vs_currencies=usd',
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                rates = {}
                
                for currency in self.config.SUPPORTED_CRYPTO:
                    crypto_id = self.config.CRYPTO_IDS[currency]
                    if crypto_id in data and 'usd' in data[crypto_id]:
                        rates[currency] = Decimal(str(data[crypto_id]['usd']))
                    else:
                        # Fallback to mock rates
                        rates[currency] = Decimal(str(self.config.MOCK_RATES[currency]))
                
                return rates
            else:
                # Fallback to mock rates if API fails
                return {currency: Decimal(str(rate)) for currency, rate in self.config.MOCK_RATES.items()}
                
        except Exception as e:
            logging.error(f"Failed to fetch crypto prices: {e}")
            # Fallback to mock rates
            return {currency: Decimal(str(rate)) for currency, rate in self.config.MOCK_RATES.items()}
    
    def convert_crypto_to_usd(self, crypto_amount, currency):
        """Convert cryptocurrency amount to USD"""
        rates = self.get_live_prices()
        if currency in rates:
            return Decimal(str(crypto_amount)) * rates[currency]
        return Decimal('0')
    
    def convert_usd_to_crypto(self, usd_amount, currency):
        """Convert USD amount to cryptocurrency"""
        rates = self.get_live_prices()
        if currency in rates and rates[currency] > 0:
            return Decimal(str(usd_amount)) / rates[currency]
        return Decimal('0')
    
    def get_network_fee(self, currency):
        """Get network fee for a cryptocurrency"""
        return Decimal(str(self.config.NETWORK_FEES.get(currency, 0)))
    
    def get_min_withdrawal(self, currency):
        """Get minimum withdrawal amount for a cryptocurrency"""
        return Decimal(str(self.config.MIN_WITHDRAWAL.get(currency, 0)))
    
    def generate_mock_address(self, user_id, currency):
        """Generate a mock crypto address (in real app, use proper wallet generation)"""
        import hashlib
        base_string = f"{user_id}_{currency}_{time.time()}"
        address = hashlib.sha256(base_string.encode()).hexdigest()[:34]
        
        # Add currency-specific prefixes
        if currency == 'BTC':
            return f"bc1{address}"
        elif currency == 'ETH':
            return f"0x{address}"
        elif currency == 'USDT':
            return f"0x{address}"  # USDT typically uses ETH addresses
        
        return address

# Global crypto service instance
crypto_service = CryptoService()
