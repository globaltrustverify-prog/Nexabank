import os

class CryptoConfig:
    # Supported cryptocurrencies
    SUPPORTED_CRYPTO = ['BTC', 'ETH', 'USDT']
    
    # API endpoints for live prices (using CoinGecko free API)
    COINGECKO_API = 'https://api.coingecko.com/api/v3/simple/price'
    
    # Crypto symbols for API
    CRYPTO_IDS = {
        'BTC': 'bitcoin',
        'ETH': 'ethereum', 
        'USDT': 'tether'
    }
    
    # Mock exchange rates (fallback if API fails)
    MOCK_RATES = {
        'BTC': 45000.00,
        'ETH': 3000.00,
        'USDT': 1.00
    }
    
    # Network fees (approximate)
    NETWORK_FEES = {
        'BTC': 0.0005,  # ~$22.50
        'ETH': 0.003,   # ~$9.00
        'USDT': 1.00    # $1.00 (ERC-20)
    }
    
    # Minimum withdrawal amounts
    MIN_WITHDRAWAL = {
        'BTC': 0.001,   # ~$45
        'ETH': 0.01,    # ~$30
        'USDT': 10.00   # $10
    }
