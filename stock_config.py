import os

class StockConfig:
    # Popular stocks to support initially
    POPULAR_STOCKS = [
        # Tech Stocks
        {'symbol': 'AAPL', 'name': 'Apple Inc.'},
        {'symbol': 'MSFT', 'name': 'Microsoft Corporation'},
        {'symbol': 'GOOGL', 'name': 'Alphabet Inc.'},
        {'symbol': 'AMZN', 'name': 'Amazon.com Inc.'},
        {'symbol': 'TSLA', 'name': 'Tesla Inc.'},
        {'symbol': 'META', 'name': 'Meta Platforms Inc.'},
        {'symbol': 'NVDA', 'name': 'NVIDIA Corporation'},
        {'symbol': 'NFLX', 'name': 'Netflix Inc.'},
        
        # Financial Stocks
        {'symbol': 'JPM', 'name': 'JPMorgan Chase & Co.'},
        {'symbol': 'V', 'name': 'Visa Inc.'},
        {'symbol': 'MA', 'name': 'Mastercard Incorporated'},
        
        # Consumer Stocks
        {'symbol': 'WMT', 'name': 'Walmart Inc.'},
        {'symbol': 'KO', 'name': 'The Coca-Cola Company'},
        {'symbol': 'MCD', 'name': 'McDonald\'s Corporation'},
        
        # ETF and Index
        {'symbol': 'SPY', 'name': 'SPDR S&P 500 ETF Trust'},
        {'symbol': 'QQQ', 'name': 'Invesco QQQ Trust'},
        {'symbol': 'VOO', 'name': 'Vanguard S&P 500 ETF'},
        
        # International
        {'symbol': 'BABA', 'name': 'Alibaba Group Holding Limited'},
        {'symbol': 'TSM', 'name': 'Taiwan Semiconductor Manufacturing Company Limited'}
    ]
    
    # API Configuration (using Alpha Vantage free tier)
    ALPHA_VANTAGE_API_KEY = 'demo'  # Free demo key
    ALPHA_VANTAGE_BASE_URL = 'https://www.alphavantage.co/query'
    
    # Mock prices for demo (fallback)
    MOCK_STOCK_PRICES = {
        'AAPL': 185.50, 'MSFT': 375.85, 'GOOGL': 138.20, 'AMZN': 155.75,
        'TSLA': 245.60, 'META': 350.40, 'NVDA': 475.25, 'NFLX': 485.90,
        'JPM': 170.35, 'V': 250.80, 'MA': 385.45, 'WMT': 165.20,
        'KO': 59.85, 'MCD': 285.70, 'SPY': 455.30, 'QQQ': 380.45,
        'VOO': 420.15, 'BABA': 85.60, 'TSM': 95.40
    }
    
    # Trading rules
    MINIMUM_TRADE_AMOUNT = 10.00  # $10 minimum trade
    TRADING_HOURS = {
        'start': '09:30',  # EST
        'end': '16:00'     # EST
    }
