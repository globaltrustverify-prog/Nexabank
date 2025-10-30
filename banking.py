from flask import request, jsonify
from flask_restful import Resource
from config import get_db_connection
import jwt
import datetime
from decimal import Decimal

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

class Balance(Resource):
    def get(self):
        user_data = get_user_from_token()
        if not user_data:
            return {'error': 'Invalid or expired token'}, 401
        
        # Get specific account or default to first account
        account_number = request.args.get('account_number')
        
        conn = get_db_connection()
        if not conn:
            return {'error': 'Database connection failed'}, 500
            
        try:
            cursor = conn.cursor(dictionary=True)
            
            if account_number:
                # Get specific account balance
                cursor.execute("""
                    SELECT a.account_number, a.balance, a.account_type, u.full_name 
                    FROM accounts a 
                    JOIN users u ON a.user_id = u.user_id 
                    WHERE a.user_id = %s AND a.account_number = %s
                """, (user_data['user_id'], account_number))
            else:
                # Get first account balance (default)
                cursor.execute("""
                    SELECT a.account_number, a.balance, a.account_type, u.full_name 
                    FROM accounts a 
                    JOIN users u ON a.user_id = u.user_id 
                    WHERE a.user_id = %s 
                    ORDER BY a.created_at 
                    LIMIT 1
                """, (user_data['user_id'],))
            
            account = cursor.fetchone()
            
            if not account:
                return {'error': 'Account not found'}, 404
            
            return {
                'account_number': account['account_number'],
                'account_type': account['account_type'],
                'balance': float(account['balance']),
                'account_holder': account['full_name'],
                'currency': 'USD'
            }
            
        except Exception as e:
            return {'error': f'Failed to get balance: {str(e)}'}, 500
        finally:
            cursor.close()
            conn.close()

class Deposit(Resource):
    def post(self):
        user_data = get_user_from_token()
        if not user_data:
            return {'error': 'Invalid or expired token'}, 401
        
        data = request.get_json()
        if not data or not data.get('amount'):
            return {'error': 'Amount is required'}, 400
        
        # Get account number from request or use default
        account_number = data.get('account_number')
        
        try:
            amount = Decimal(str(data['amount']))
            if amount <= 0:
                return {'error': 'Amount must be positive'}, 400
        except ValueError:
            return {'error': 'Invalid amount'}, 400
        
        conn = get_db_connection()
        if not conn:
            return {'error': 'Database connection failed'}, 500
            
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Get account
            if account_number:
                cursor.execute("""
                    SELECT account_id, balance, account_type, account_number 
                    FROM accounts 
                    WHERE user_id = %s AND account_number = %s
                """, (user_data['user_id'], account_number))
            else:
                # Use first account as default
                cursor.execute("""
                    SELECT account_id, balance, account_type, account_number 
                    FROM accounts 
                    WHERE user_id = %s 
                    ORDER BY created_at 
                    LIMIT 1
                """, (user_data['user_id'],))
            
            account = cursor.fetchone()
            
            if not account:
                return {'error': 'Account not found'}, 404
            
            # Different minimum deposits for account types
            cursor.execute("SELECT COUNT(*) as tx_count FROM transactions WHERE account_id = %s", (account['account_id'],))
            tx_count = cursor.fetchone()['tx_count']
            
            if tx_count == 0:
                if account['account_type'] == 'savings' and amount < 100:
                    return {'error': 'First deposit to savings account must be at least $100'}, 400
                elif account['account_type'] == 'checking' and amount < 50:
                    return {'error': 'First deposit to checking account must be at least $50'}, 400
            
            # Update balance
            current_balance = Decimal(str(account['balance']))
            new_balance = current_balance + amount
            
            cursor.execute(
                "UPDATE accounts SET balance = %s WHERE account_id = %s",
                (float(new_balance), account['account_id'])
            )
            
            # Record transaction
            cursor.execute(
                "INSERT INTO transactions (account_id, type, amount, balance_after, description) VALUES (%s, %s, %s, %s, %s)",
                (account['account_id'], 'deposit', float(amount), float(new_balance), 'Cash deposit')
            )
            
            conn.commit()
            
            return {
                'message': 'Deposit successful',
                'account_number': account['account_number'],
                'account_type': account['account_type'],
                'amount': float(amount),
                'new_balance': float(new_balance),
                'transaction_type': 'deposit'
            }
            
        except Exception as e:
            conn.rollback()
            return {'error': f'Deposit failed: {str(e)}'}, 500
        finally:
            cursor.close()
            conn.close()

class Withdraw(Resource):
    def post(self):
        user_data = get_user_from_token()
        if not user_data:
            return {'error': 'Invalid or expired token'}, 401
        
        data = request.get_json()
        if not data or not data.get('amount'):
            return {'error': 'Amount is required'}, 400
        
        # Get account number from request
        account_number = data.get('account_number')
        
        try:
            amount = Decimal(str(data['amount']))
            if amount <= 0:
                return {'error': 'Amount must be positive'}, 400
        except ValueError:
            return {'error': 'Invalid amount'}, 400
        
        conn = get_db_connection()
        if not conn:
            return {'error': 'Database connection failed'}, 500
            
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Get account
            if account_number:
                cursor.execute("""
                    SELECT account_id, balance, account_type, account_number 
                    FROM accounts 
                    WHERE user_id = %s AND account_number = %s
                """, (user_data['user_id'], account_number))
            else:
                # Use first account as default
                cursor.execute("""
                    SELECT account_id, balance, account_type, account_number 
                    FROM accounts 
                    WHERE user_id = %s 
                    ORDER BY created_at 
                    LIMIT 1
                """, (user_data['user_id'],))
            
            account = cursor.fetchone()
            
            if not account:
                return {'error': 'Account not found'}, 404
            
            # Check sufficient balance
            current_balance = Decimal(str(account['balance']))
            if current_balance < amount:
                return {'error': 'Insufficient funds'}, 400
            
            # Different minimum balances for account types
            new_balance = current_balance - amount
            if account['account_type'] == 'savings' and new_balance < Decimal('10'):
                return {'error': 'Savings account must maintain minimum balance of $10'}, 400
            elif account['account_type'] == 'checking' and new_balance < Decimal('5'):
                return {'error': 'Checking account must maintain minimum balance of $5'}, 400
            
            # Update balance
            cursor.execute(
                "UPDATE accounts SET balance = %s WHERE account_id = %s",
                (float(new_balance), account['account_id'])
            )
            
            # Record transaction
            cursor.execute(
                "INSERT INTO transactions (account_id, type, amount, balance_after, description) VALUES (%s, %s, %s, %s, %s)",
                (account['account_id'], 'withdraw', float(amount), float(new_balance), 'Cash withdrawal')
            )
            
            conn.commit()
            
            return {
                'message': 'Withdrawal successful',
                'account_number': account['account_number'],
                'account_type': account['account_type'],
                'amount': float(amount),
                'new_balance': float(new_balance),
                'transaction_type': 'withdrawal'
            }
            
        except Exception as e:
            conn.rollback()
            return {'error': f'Withdrawal failed: {str(e)}'}, 500
        finally:
            cursor.close()
            conn.close()
