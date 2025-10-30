from flask import request, jsonify
from flask_restful import Resource
from config import get_db_connection
import jwt
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

class InternalTransfer(Resource):
    def post(self):
        user_data = get_user_from_token()
        if not user_data:
            return {'error': 'Invalid or expired token'}, 401
        
        data = request.get_json()
        if not data or not data.get('amount'):
            return {'error': 'Amount is required'}, 400
        
        # Optional: specify from_account and to_account, otherwise use defaults
        from_account_type = data.get('from_account', 'checking')
        to_account_type = data.get('to_account', 'savings')
        description = data.get('description', 'Move to savings')
        
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
            
            # Get source account (checking)
            cursor.execute("""
                SELECT account_id, account_number, balance, account_type
                FROM accounts 
                WHERE user_id = %s AND account_type = %s
            """, (user_data['user_id'], from_account_type))
            from_account = cursor.fetchone()
            
            if not from_account:
                return {'error': f'{from_account_type.title()} account not found'}, 404
            
            # Get destination account (savings)
            cursor.execute("""
                SELECT account_id, account_number, balance, account_type
                FROM accounts 
                WHERE user_id = %s AND account_type = %s
            """, (user_data['user_id'], to_account_type))
            to_account = cursor.fetchone()
            
            if not to_account:
                return {'error': f'{to_account_type.title()} account not found'}, 404
            
            # Check if transferring between same account
            if from_account['account_id'] == to_account['account_id']:
                return {'error': 'Cannot transfer to the same account'}, 400
            
            # Check sufficient funds in source account
            from_balance = Decimal(str(from_account['balance']))
            if from_balance < amount:
                return {'error': f'Insufficient funds in {from_account_type} account'}, 400
            
            # Check minimum balance for source account after transfer
            new_from_balance = from_balance - amount
            if from_account_type == 'savings' and new_from_balance < Decimal('10'):
                return {'error': 'Savings account must maintain minimum balance of $10'}, 400
            elif from_account_type == 'checking' and new_from_balance < Decimal('5'):
                return {'error': 'Checking account must maintain minimum balance of $5'}, 400
            
            # Update source account balance
            cursor.execute(
                "UPDATE accounts SET balance = %s WHERE account_id = %s",
                (float(new_from_balance), from_account['account_id'])
            )
            
            # Record withdrawal transaction for source account
            cursor.execute(
                """INSERT INTO transactions 
                (account_id, type, amount, balance_after, description) 
                VALUES (%s, %s, %s, %s, %s)""",
                (from_account['account_id'], 'withdraw', float(amount), 
                 float(new_from_balance), f'Transfer to {to_account_type}: {description}')
            )
            
            # Update destination account balance
            to_balance = Decimal(str(to_account['balance']))
            new_to_balance = to_balance + amount
            cursor.execute(
                "UPDATE accounts SET balance = %s WHERE account_id = %s",
                (float(new_to_balance), to_account['account_id'])
            )
            
            # Record deposit transaction for destination account
            cursor.execute(
                """INSERT INTO transactions 
                (account_id, type, amount, balance_after, description) 
                VALUES (%s, %s, %s, %s, %s)""",
                (to_account['account_id'], 'deposit', float(amount), 
                 float(new_to_balance), f'Transfer from {from_account_type}: {description}')
            )
            
            conn.commit()
            
            return {
                'message': 'Transfer between accounts successful',
                'transfer_details': {
                    'from_account': f"{from_account['account_number']} ({from_account_type})",
                    'to_account': f"{to_account['account_number']} ({to_account_type})",
                    'amount': float(amount),
                    'description': description,
                    'from_account_new_balance': float(new_from_balance),
                    'to_account_new_balance': float(new_to_balance)
                }
            }
            
        except Exception as e:
            conn.rollback()
            return {'error': f'Internal transfer failed: {str(e)}'}, 500
        finally:
            cursor.close()
            conn.close()

class QuickSave(Resource):
    def post(self):
        """Quick save fixed amounts from checking to savings"""
        user_data = get_user_from_token()
        if not user_data:
            return {'error': 'Invalid or expired token'}, 401
        
        data = request.get_json()
        preset_amounts = {
            'small': Decimal('10'),
            'medium': Decimal('25'), 
            'large': Decimal('50'),
            'custom': Decimal(str(data.get('amount', 0)))
        }
        
        save_type = data.get('save_type', 'small')
        if save_type not in preset_amounts:
            return {'error': 'Invalid save type. Use: small, medium, large, or custom'}, 400
        
        amount = preset_amounts[save_type]
        if save_type == 'custom' and amount <= 0:
            return {'error': 'Custom amount must be positive'}, 400
        
        # Use the internal transfer logic
        transfer_data = {
            'amount': float(amount),
            'from_account': 'checking',
            'to_account': 'savings',
            'description': f'Quick save: {save_type}'
        }
        
        # Create a new request context for the internal transfer
        from flask import has_request_context, Request
        if not has_request_context():
            return {'error': 'Request context required'}, 500
        
        original_json = request.get_json()
        try:
            request._cached_json = (transfer_data, transfer_data)
            result = InternalTransfer().post()
            request._cached_json = (original_json, original_json)
            return result
        except Exception as e:
            request._cached_json = (original_json, original_json)
            return {'error': f'Quick save failed: {str(e)}'}, 500
