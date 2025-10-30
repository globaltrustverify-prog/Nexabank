from flask import request, jsonify
from flask_restful import Resource
from config import get_db_connection
import jwt
from decimal import Decimal
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import from services
from services.stock_service import stock_service

def verify_token(token):
    """Verify JWT token and return user data"""
    try:
        payload = jwt.decode(token, 'your-secret-key-here-change-in-production', algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def get_user_from_token():
    """Extract user from authorization token"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    
    token = auth_header.split(' ')[1]
    user_data = verify_token(token)
    return user_data

class StockMarket(Resource):
    def get(self):
        """Get all available stocks with current prices"""
        user_data = get_user_from_token()
        if not user_data:
            return {'error': 'Invalid or expired token'}, 401
        
        # Initialize stocks in database
        stock_service.initialize_stocks()
        
        # Get all stock prices
        stock_prices = stock_service.get_all_stock_prices()
        
        return {
            'stocks': list(stock_prices.values()),
            'count': len(stock_prices)
        }

class StockDetail(Resource):
    def get(self, symbol):
        """Get detailed information for a specific stock"""
        user_data = get_user_from_token()
        if not user_data:
            return {'error': 'Invalid or expired token'}, 401
        
        symbol = symbol.upper()
        price_data = stock_service.get_stock_price(symbol)
        
        # Get stock info from database
        conn = get_db_connection()
        if not conn:
            return {'error': 'Database connection failed'}, 500
            
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM stocks WHERE symbol = %s", (symbol,))
            stock_info = cursor.fetchone()
            
            if not stock_info:
                return {'error': 'Stock not found'}, 404
            
            return {
                'stock': {
                    'symbol': stock_info['symbol'],
                    'company_name': stock_info['company_name'],
                    'current_price': float(price_data['price']),
                    'daily_change': float(price_data['change']),
                    'daily_change_percent': float(price_data['change_percent'])
                }
            }
        except Exception as e:
            return {'error': f'Failed to get stock details: {str(e)}'}, 500
        finally:
            cursor.close()
            conn.close()

class BuyStock(Resource):
    def post(self):
        """Buy stocks using bank account funds"""
        user_data = get_user_from_token()
        if not user_data:
            return {'error': 'Invalid or expired token'}, 401
        
        data = request.get_json()
        if not data or not data.get('symbol') or not data.get('quantity'):
            return {'error': 'Symbol and quantity are required'}, 400
        
        symbol = data['symbol'].upper()
        account_type = data.get('account_type', 'savings')
        
        try:
            quantity = Decimal(str(data['quantity']))
            if quantity <= 0:
                return {'error': 'Quantity must be positive'}, 400
        except ValueError:
            return {'error': 'Invalid quantity'}, 400
        
        # Calculate total cost
        total_cost = stock_service.calculate_order_total(symbol, quantity)
        
        # Check minimum trade amount
        if total_cost < 10.00:
            return {'error': 'Minimum trade amount is $10.00'}, 400
        
        conn = get_db_connection()
        if not conn:
            return {'error': 'Database connection failed'}, 500
            
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Get bank account
            cursor.execute("""
                SELECT account_id, balance FROM accounts 
                WHERE user_id = %s AND account_type = %s
            """, (user_data['user_id'], account_type))
            
            bank_account = cursor.fetchone()
            if not bank_account:
                return {'error': f'{account_type.title()} account not found'}, 404
            
            # Check sufficient funds
            if Decimal(str(bank_account['balance'])) < total_cost:
                return {'error': f'Insufficient funds in {account_type} account'}, 400
            
            # Get current stock price
            price_data = stock_service.get_stock_price(symbol)
            current_price = price_data['price']
            
            # Update bank account balance
            new_bank_balance = Decimal(str(bank_account['balance'])) - Decimal(str(total_cost))
            cursor.execute(
                "UPDATE accounts SET balance = %s WHERE account_id = %s",
                (float(new_bank_balance), bank_account['account_id'])
            )
            
            # Get or create stock portfolio entry
            cursor.execute("""
                SELECT * FROM stock_portfolios 
                WHERE user_id = %s AND symbol = %s
            """, (user_data['user_id'], symbol))
            
            portfolio = cursor.fetchone()
            
            if portfolio:
                # Update existing portfolio
                new_quantity = Decimal(str(portfolio['quantity'])) + quantity
                new_total_invested = Decimal(str(portfolio['total_invested'])) + Decimal(str(total_cost))
                new_avg_price = new_total_invested / new_quantity
                
                cursor.execute("""
                    UPDATE stock_portfolios 
                    SET quantity = %s, average_price = %s, total_invested = %s,
                        current_value = %s, unrealized_pnl = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE portfolio_id = %s
                """, (
                    float(new_quantity),
                    float(new_avg_price),
                    float(new_total_invested),
                    float(new_quantity * current_price),
                    float((new_quantity * current_price) - new_total_invested),
                    portfolio['portfolio_id']
                ))
            else:
                # Create new portfolio entry
                cursor.execute("""
                    INSERT INTO stock_portfolios 
                    (user_id, symbol, quantity, average_price, total_invested, current_value, unrealized_pnl)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    user_data['user_id'],
                    symbol,
                    float(quantity),
                    float(current_price),
                    float(total_cost),
                    float(quantity * current_price),
                    float(0)  # No PnL initially
                ))
            
            # Record stock transaction
            cursor.execute("""
                INSERT INTO stock_transactions 
                (user_id, symbol, type, quantity, price, total_amount, order_type, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                user_data['user_id'],
                symbol,
                'buy',
                float(quantity),
                float(current_price),
                float(total_cost),
                'market',
                'completed'
            ))
            
            # Record bank withdrawal transaction
            cursor.execute("""
                INSERT INTO transactions 
                (account_id, type, amount, balance_after, description)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                bank_account['account_id'],
                'withdraw',
                float(total_cost),
                float(new_bank_balance),
                f'Stock purchase: {quantity} shares of {symbol}'
            ))
            
            conn.commit()
            
            return {
                'message': 'Stock purchase successful',
                'order_details': {
                    'symbol': symbol,
                    'quantity': float(quantity),
                    'price_per_share': float(current_price),
                    'total_cost': float(total_cost),
                    'from_account': account_type,
                    'new_bank_balance': float(new_bank_balance)
                }
            }
            
        except Exception as e:
            conn.rollback()
            return {'error': f'Stock purchase failed: {str(e)}'}, 500
        finally:
            cursor.close()
            conn.close()

class SellStock(Resource):
    def post(self):
        """Sell stocks and deposit proceeds to bank account"""
        user_data = get_user_from_token()
        if not user_data:
            return {'error': 'Invalid or expired token'}, 401
        
        data = request.get_json()
        if not data or not data.get('symbol') or not data.get('quantity'):
            return {'error': 'Symbol and quantity are required'}, 400
        
        symbol = data['symbol'].upper()
        account_type = data.get('account_type', 'savings')
        
        try:
            quantity = Decimal(str(data['quantity']))
            if quantity <= 0:
                return {'error': 'Quantity must be positive'}, 400
        except ValueError:
            return {'error': 'Invalid quantity'}, 400
        
        conn = get_db_connection()
        if not conn:
            return {'error': 'Database connection failed'}, 500
            
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Check if user owns the stock
            cursor.execute("""
                SELECT * FROM stock_portfolios 
                WHERE user_id = %s AND symbol = %s
            """, (user_data['user_id'], symbol))
            
            portfolio = cursor.fetchone()
            if not portfolio:
                return {'error': f'You do not own any shares of {symbol}'}, 400
            
            # Check if user has enough shares to sell
            if Decimal(str(portfolio['quantity'])) < quantity:
                return {'error': f'Insufficient shares. You own {portfolio["quantity"]} shares of {symbol}'}, 400
            
            # Get current stock price
            price_data = stock_service.get_stock_price(symbol)
            current_price = price_data['price']
            sale_proceeds = Decimal(str(quantity)) * current_price
            
            # Get bank account
            cursor.execute("""
                SELECT account_id, balance FROM accounts 
                WHERE user_id = %s AND account_type = %s
            """, (user_data['user_id'], account_type))
            
            bank_account = cursor.fetchone()
            if not bank_account:
                return {'error': f'{account_type.title()} account not found'}, 404
            
            # Calculate realized P&L
            cost_basis = (Decimal(str(portfolio['total_invested'])) / Decimal(str(portfolio['quantity']))) * quantity
            realized_pnl = sale_proceeds - cost_basis
            
            # Update bank account balance (deposit sale proceeds)
            new_bank_balance = Decimal(str(bank_account['balance'])) + sale_proceeds
            cursor.execute(
                "UPDATE accounts SET balance = %s WHERE account_id = %s",
                (float(new_bank_balance), bank_account['account_id'])
            )
            
            # Update stock portfolio
            new_quantity = Decimal(str(portfolio['quantity'])) - quantity
            
            if new_quantity > 0:
                # Update remaining shares
                new_total_invested = Decimal(str(portfolio['total_invested'])) - cost_basis
                new_avg_price = new_total_invested / new_quantity
                
                cursor.execute("""
                    UPDATE stock_portfolios 
                    SET quantity = %s, average_price = %s, total_invested = %s,
                        current_value = %s, unrealized_pnl = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE portfolio_id = %s
                """, (
                    float(new_quantity),
                    float(new_avg_price),
                    float(new_total_invested),
                    float(new_quantity * current_price),
                    float((new_quantity * current_price) - new_total_invested),
                    portfolio['portfolio_id']
                ))
            else:
                # Delete portfolio entry if no shares left
                cursor.execute("DELETE FROM stock_portfolios WHERE portfolio_id = %s", (portfolio['portfolio_id'],))
            
            # Record stock transaction
            cursor.execute("""
                INSERT INTO stock_transactions 
                (user_id, symbol, type, quantity, price, total_amount, order_type, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                user_data['user_id'],
                symbol,
                'sell',
                float(quantity),
                float(current_price),
                float(sale_proceeds),
                'market',
                'completed'
            ))
            
            # Record bank deposit transaction
            cursor.execute("""
                INSERT INTO transactions 
                (account_id, type, amount, balance_after, description)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                bank_account['account_id'],
                'deposit',
                float(sale_proceeds),
                float(new_bank_balance),
                f'Stock sale: {quantity} shares of {symbol}'
            ))
            
            conn.commit()
            
            return {
                'message': 'Stock sale successful',
                'sale_details': {
                    'symbol': symbol,
                    'quantity': float(quantity),
                    'price_per_share': float(current_price),
                    'sale_proceeds': float(sale_proceeds),
                    'realized_pnl': float(realized_pnl),
                    'to_account': account_type,
                    'new_bank_balance': float(new_bank_balance),
                    'shares_remaining': float(new_quantity) if new_quantity > 0 else 0
                }
            }
            
        except Exception as e:
            conn.rollback()
            return {'error': f'Stock sale failed: {str(e)}'}, 500
        finally:
            cursor.close()
            conn.close()

class StockPortfolio(Resource):
    def get(self):
        """Get user's stock portfolio"""
        user_data = get_user_from_token()
        if not user_data:
            return {'error': 'Invalid or expired token'}, 401
        
        conn = get_db_connection()
        if not conn:
            return {'error': 'Database connection failed'}, 500
            
        try:
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT sp.*, s.company_name 
                FROM stock_portfolios sp
                JOIN stocks s ON sp.symbol = s.symbol
                WHERE sp.user_id = %s
            """, (user_data['user_id'],))
            
            portfolio = cursor.fetchall()
            
            # Convert Decimal to float for JSON serialization
            formatted_portfolio = []
            for item in portfolio:
                formatted_item = {
                    'portfolio_id': item['portfolio_id'],
                    'user_id': item['user_id'],
                    'symbol': item['symbol'],
                    'company_name': item['company_name'],
                    'quantity': float(item['quantity']),
                    'average_price': float(item['average_price']),
                    'total_invested': float(item['total_invested']),
                    'current_value': float(item['current_value']),
                    'unrealized_pnl': float(item['unrealized_pnl']),
                    'created_at': item['created_at'].isoformat() if item['created_at'] else None,
                    'updated_at': item['updated_at'].isoformat() if item['updated_at'] else None
                }
                formatted_portfolio.append(formatted_item)
            
            # Calculate totals
            total_invested = 0
            total_current_value = 0
            
            for item in portfolio:
                total_invested += item['total_invested']
                total_current_value += item['current_value']
            
            total_pnl = total_current_value - total_invested
            total_pnl_percent = (total_pnl / total_invested * 100) if total_invested > 0 else 0
            
            return {
                'portfolio': formatted_portfolio,
                'summary': {
                    'total_invested': float(total_invested),
                    'total_current_value': float(total_current_value),
                    'total_unrealized_pnl': float(total_pnl),
                    'total_pnl_percent': float(total_pnl_percent),
                    'stock_count': len(portfolio)
                }
            }
            
        except Exception as e:
            return {'error': f'Failed to get portfolio: {str(e)}'}, 500
        finally:
            cursor.close()
            conn.close()

class StockTransactions(Resource):
    def get(self):
        """Get user's stock transaction history"""
        user_data = get_user_from_token()
        if not user_data:
            return {'error': 'Invalid or expired token'}, 401
        
        conn = get_db_connection()
        if not conn:
            return {'error': 'Database connection failed'}, 500
            
        try:
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT st.*, s.company_name 
                FROM stock_transactions st
                JOIN stocks s ON st.symbol = s.symbol
                WHERE st.user_id = %s 
                ORDER BY st.created_at DESC
                LIMIT 50
            """, (user_data['user_id'],))
            
            transactions = cursor.fetchall()
            
            # Convert Decimal to float for JSON serialization
            formatted_transactions = []
            for tx in transactions:
                formatted_tx = {
                    'transaction_id': tx['transaction_id'],
                    'user_id': tx['user_id'],
                    'symbol': tx['symbol'],
                    'company_name': tx['company_name'],
                    'type': tx['type'],
                    'quantity': float(tx['quantity']),
                    'price': float(tx['price']),
                    'total_amount': float(tx['total_amount']),
                    'order_type': tx['order_type'],
                    'status': tx['status'],
                    'created_at': tx['created_at'].isoformat() if tx['created_at'] else None
                }
                formatted_transactions.append(formatted_tx)
            
            return {
                'transactions': formatted_transactions,
                'count': len(transactions)
            }
            
        except Exception as e:
            return {'error': f'Failed to get transactions: {str(e)}'}, 500
        finally:
            cursor.close()
            conn.close()
