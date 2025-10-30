from flask import request, jsonify
from flask_restful import Resource
from config import get_db_connection
import jwt
import random
import string

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

class Accounts(Resource):
    def get(self):
        """Get all accounts for the user"""
        user_data = get_user_from_token()
        if not user_data:
            return {'error': 'Invalid or expired token'}, 401
        
        conn = get_db_connection()
        if not conn:
            return {'error': 'Database connection failed'}, 500
            
        try:
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT 
                    account_id,
                    account_number,
                    account_type,
                    balance,
                    created_at
                FROM accounts 
                WHERE user_id = %s 
                ORDER BY created_at DESC
            """, (user_data['user_id'],))
            
            accounts = cursor.fetchall()
            
            formatted_accounts = []
            total_balance = 0
            
            for account in accounts:
                formatted_accounts.append({
                    'account_id': account['account_id'],
                    'account_number': account['account_number'],
                    'account_type': account['account_type'],
                    'balance': float(account['balance']),
                    'created_at': account['created_at'].isoformat() if account['created_at'] else None
                })
                total_balance += account['balance']
            
            return {
                'accounts': formatted_accounts,
                'total_balance': float(total_balance),
                'account_count': len(accounts)
            }
            
        except Exception as e:
            return {'error': f'Failed to get accounts: {str(e)}'}, 500
        finally:
            cursor.close()
            conn.close()

    def post(self):
        """Create a new account (checking or savings)"""
        user_data = get_user_from_token()
        if not user_data:
            return {'error': 'Invalid or expired token'}, 401
        
        data = request.get_json()
        if not data or not data.get('account_type'):
            return {'error': 'Account type is required'}, 400
        
        account_type = data['account_type']
        if account_type not in ['savings', 'checking']:
            return {'error': 'Account type must be savings or checking'}, 400
        
        conn = get_db_connection()
        if not conn:
            return {'error': 'Database connection failed'}, 500
            
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Check if user already has this account type
            cursor.execute(
                "SELECT account_id FROM accounts WHERE user_id = %s AND account_type = %s", 
                (user_data['user_id'], account_type)
            )
            existing_account = cursor.fetchone()
            
            if existing_account:
                return {'error': f'You already have a {account_type} account'}, 400
            
            # Generate UNIQUE random account number
            max_attempts = 10
            account_created = False
            account_number = None
            account_id = None
            
            for attempt in range(max_attempts):
                # Generate random 9-digit account number
                random_digits = ''.join(random.choices(string.digits, k=9))
                
                if account_type == 'savings':
                    account_prefix = 'NBS'
                else:
                    account_prefix = 'NBC'
                
                account_number = f"{account_prefix}{random_digits}"
                
                # Check if this account number already exists
                cursor.execute("SELECT account_id FROM accounts WHERE account_number = %s", (account_number,))
                existing = cursor.fetchone()
                
                if not existing:
                    # Account number is unique, create account
                    cursor.execute(
                        "INSERT INTO accounts (user_id, account_number, account_type, balance) VALUES (%s, %s, %s, %s)",
                        (user_data['user_id'], account_number, account_type, 0.00)
                    )
                    
                    account_id = cursor.lastrowid
                    conn.commit()
                    account_created = True
                    break
            
            if not account_created:
                return {'error': 'Failed to generate unique account number. Please try again.'}, 500
            
            return {
                'message': f'{account_type.title()} account created successfully',
                'account_number': account_number,
                'account_type': account_type,
                'account_id': account_id
            }, 201
            
        except Exception as e:
            conn.rollback()
            return {'error': f'Failed to create account: {str(e)}'}, 500
        finally:
            cursor.close()
            conn.close()

class AccountDetail(Resource):
    def get(self, account_number):
        """Get specific account details"""
        user_data = get_user_from_token()
        if not user_data:
            return {'error': 'Invalid or expired token'}, 401
        
        conn = get_db_connection()
        if not conn:
            return {'error': 'Database connection failed'}, 500
            
        try:
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT 
                    a.account_id,
                    a.account_number,
                    a.account_type,
                    a.balance,
                    a.created_at,
                    u.full_name
                FROM accounts a
                JOIN users u ON a.user_id = u.user_id
                WHERE a.account_number = %s AND a.user_id = %s
            """, (account_number, user_data['user_id']))
            
            account = cursor.fetchone()
            
            if not account:
                return {'error': 'Account not found'}, 404
            
            # Get recent transactions for this account
            cursor.execute("""
                SELECT 
                    transaction_id,
                    type,
                    amount,
                    balance_after,
                    description,
                    created_at
                FROM transactions 
                WHERE account_id = %s 
                ORDER BY created_at DESC 
                LIMIT 5
            """, (account['account_id'],))
            
            recent_transactions = cursor.fetchall()
            
            formatted_transactions = []
            for tx in recent_transactions:
                formatted_transactions.append({
                    'id': tx['transaction_id'],
                    'type': tx['type'],
                    'amount': float(tx['amount']),
                    'balance_after': float(tx['balance_after']),
                    'description': tx['description'],
                    'date': tx['created_at'].isoformat() if tx['created_at'] else None
                })
            
            return {
                'account': {
                    'account_number': account['account_number'],
                    'account_type': account['account_type'],
                    'balance': float(account['balance']),
                    'account_holder': account['full_name'],
                    'created_at': account['created_at'].isoformat() if account['created_at'] else None
                },
                'recent_transactions': formatted_transactions
            }
            
        except Exception as e:
            return {'error': f'Failed to get account details: {str(e)}'}, 500
        finally:
            cursor.close()
            conn.close()