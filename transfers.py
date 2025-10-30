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

class Transfer(Resource):
    def post(self):
        user_data = get_user_from_token()
        if not user_data:
            return {'error': 'Invalid or expired token'}, 401
        
        data = request.get_json()
        required_fields = ['from_account', 'to_account', 'amount', 'description']
        for field in required_fields:
            if not data or not data.get(field):
                return {'error': f'{field.replace("_", " ").title()} is required'}, 400
        
        from_account = data['from_account'].upper()  # Convert to uppercase
        to_account = data['to_account'].upper()      # Convert to uppercase
        description = data['description']
        
        try:
            amount = Decimal(str(data['amount']))
            if amount <= 0:
                return {'error': 'Amount must be positive'}, 400
            if amount > 2500:  # Lower limit for external transfers
                return {'error': 'Transfer amount cannot exceed $2,500'}, 400
        except ValueError:
            return {'error': 'Invalid amount'}, 400
        
        conn = get_db_connection()
        if not conn:
            return {'error': 'Database connection failed'}, 500
            
        try:
            cursor = conn.cursor(dictionary=True, buffered=True)
            
            # Get sender's account with balance check
            cursor.execute("""
                SELECT a.account_id, a.balance, a.account_number, a.user_id, u.full_name, u.email
                FROM accounts a 
                JOIN users u ON a.user_id = u.user_id 
                WHERE a.account_number = %s AND a.user_id = %s
            """, (from_account, user_data['user_id']))
            sender_account = cursor.fetchone()
            
            if not sender_account:
                return {'error': f'Sender account {from_account} not found'}, 404
            
            # Check if sender has sufficient funds
            sender_balance = Decimal(str(sender_account['balance']))
            if sender_balance < amount:
                return {'error': 'Insufficient funds'}, 400
            
            # Check minimum balance after transfer
            new_sender_balance = sender_balance - amount
            min_balance = Decimal('10') if sender_account['account_number'].startswith('NBS') else Decimal('5')
            if new_sender_balance < min_balance:
                return {'error': f'Account must maintain minimum balance of ${min_balance} after transfer'}, 400
            
            # Get recipient's account by account number (CASE INSENSITIVE)
            cursor.execute("""
                SELECT a.account_id, a.balance, a.account_number, a.user_id, u.full_name, u.email
                FROM accounts a 
                JOIN users u ON a.user_id = u.user_id 
                WHERE UPPER(a.account_number) = UPPER(%s)
            """, (to_account,))
            recipient_account = cursor.fetchone()
            
            if not recipient_account:
                return {'error': f'Recipient account {to_account} not found'}, 404
            
            # Prevent self-transfer
            if recipient_account['user_id'] == user_data['user_id']:
                return {'error': 'Cannot transfer to your own account'}, 400
            
            # Update sender's balance
            cursor.execute(
                "UPDATE accounts SET balance = %s WHERE account_id = %s",
                (float(new_sender_balance), sender_account['account_id'])
            )
            
            # Record sender's transaction (withdrawal)
            cursor.execute(
                """INSERT INTO transactions 
                (account_id, type, amount, balance_after, description) 
                VALUES (%s, %s, %s, %s, %s)""",
                (sender_account['account_id'], 'withdraw', float(amount), 
                 float(new_sender_balance), f'Transfer to {recipient_account["full_name"]}: {description}')
            )
            
            sender_transaction_id = cursor.lastrowid
            
            # Update recipient's balance
            recipient_balance = Decimal(str(recipient_account['balance']))
            new_recipient_balance = recipient_balance + amount
            cursor.execute(
                "UPDATE accounts SET balance = %s WHERE account_id = %s",
                (float(new_recipient_balance), recipient_account['account_id'])
            )
            
            # Record recipient's transaction (deposit)
            cursor.execute(
                """INSERT INTO transactions 
                (account_id, type, amount, balance_after, description) 
                VALUES (%s, %s, %s, %s, %s)""",
                (recipient_account['account_id'], 'deposit', float(amount), 
                 float(new_recipient_balance), f'Transfer from {sender_account["full_name"]}: {description}')
            )
            
            recipient_transaction_id = cursor.lastrowid
            
            # Commit changes
            conn.commit()
            
            return {
                'message': 'Transfer successful',
                'transfer_details': {
                    'from_account': sender_account['account_number'],
                    'to_account': recipient_account['account_number'],
                    'recipient_name': recipient_account['full_name'],
                    'amount': float(amount),
                    'description': description,
                    'sender_new_balance': float(new_sender_balance),
                    'transaction_id': sender_transaction_id
                }
            }
            
        except Exception as e:
            # Rollback in case of error
            try:
                conn.rollback()
            except:
                pass
            return {'error': f'Transfer failed: {str(e)}'}, 500
        finally:
            cursor.close()
            conn.close()

class Beneficiaries(Resource):
    def get(self):
        """Get user's saved beneficiaries"""
        user_data = get_user_from_token()
        if not user_data:
            return {'error': 'Invalid or expired token'}, 401
        
        conn = get_db_connection()
        if not conn:
            return {'error': 'Database connection failed'}, 500
            
        try:
            cursor = conn.cursor(dictionary=True, buffered=True)
            
            cursor.execute("""
                SELECT beneficiary_id, account_number, name, bank_name, created_at
                FROM beneficiaries 
                WHERE user_id = %s 
                ORDER BY name
            """, (user_data['user_id'],))
            
            beneficiaries = cursor.fetchall()
            
            formatted_beneficiaries = []
            for beneficiary in beneficiaries:
                formatted_beneficiaries.append({
                    'id': beneficiary['beneficiary_id'],
                    'account_number': beneficiary['account_number'],
                    'name': beneficiary['name'],
                    'bank_name': beneficiary['bank_name'],
                    'created_at': beneficiary['created_at'].isoformat() if beneficiary['created_at'] else None
                })
            
            return {'beneficiaries': formatted_beneficiaries}
            
        except Exception as e:
            return {'error': f'Failed to get beneficiaries: {str(e)}'}, 500
        finally:
            cursor.close()
            conn.close()
    
    def post(self):
        """Add a new beneficiary"""
        user_data = get_user_from_token()
        if not user_data:
            return {'error': 'Invalid or expired token'}, 401
        
        data = request.get_json()
        if not data or not data.get('account_number') or not data.get('name'):
            return {'error': 'Account number and name are required'}, 400
        
        account_number = data['account_number'].upper()  # Convert to uppercase
        name = data['name']
        bank_name = data.get('bank_name', 'NexaBank')
        
        conn = get_db_connection()
        if not conn:
            return {'error': 'Database connection failed'}, 500
            
        try:
            cursor = conn.cursor(dictionary=True, buffered=True)
            
            # Verify account exists (CASE INSENSITIVE)
            cursor.execute("""
                SELECT account_number, user_id 
                FROM accounts 
                WHERE UPPER(account_number) = UPPER(%s)
            """, (account_number,))
            account = cursor.fetchone()
            
            if not account:
                return {'error': f'Account {account_number} not found'}, 404
            
            # Check if beneficiary already exists
            cursor.execute("""
                SELECT beneficiary_id 
                FROM beneficiaries 
                WHERE user_id = %s AND UPPER(account_number) = UPPER(%s)
            """, (user_data['user_id'], account_number))
            
            if cursor.fetchone():
                return {'error': 'Beneficiary already exists'}, 400
            
            # Add beneficiary
            cursor.execute("""
                INSERT INTO beneficiaries (user_id, account_number, name, bank_name)
                VALUES (%s, %s, %s, %s)
            """, (user_data['user_id'], account_number, name, bank_name))
            
            beneficiary_id = cursor.lastrowid
            conn.commit()
            
            return {
                'message': 'Beneficiary added successfully',
                'beneficiary_id': beneficiary_id
            }
            
        except Exception as e:
            conn.rollback()
            return {'error': f'Failed to add beneficiary: {str(e)}'}, 500
        finally:
            cursor.close()
            conn.close()