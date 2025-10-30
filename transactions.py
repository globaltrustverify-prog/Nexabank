from flask import request, jsonify
from flask_restful import Resource
from config import get_db_connection
import jwt

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

class TransactionHistory(Resource):
    def get(self):
        user_data = get_user_from_token()
        if not user_data:
            return {'error': 'Invalid or expired token'}, 401
        
        # Get query parameters for pagination/filtering
        limit = request.args.get('limit', 10, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        conn = get_db_connection()
        if not conn:
            return {'error': 'Database connection failed'}, 500
            
        try:
            cursor = conn.cursor(dictionary=True, buffered=True)
            
            # Get ALL user's account IDs
            cursor.execute("SELECT account_id FROM accounts WHERE user_id = %s", (user_data['user_id'],))
            accounts = cursor.fetchall()
            
            if not accounts:
                return {'error': 'No accounts found'}, 404

            # Extract account IDs
            account_ids = [acc['account_id'] for acc in accounts]
            placeholders = ', '.join(['%s'] * len(account_ids))

            # Get transaction count for pagination (ALL accounts)
            cursor.execute(f"SELECT COUNT(*) as total FROM transactions WHERE account_id IN ({placeholders})", account_ids)
            total_count = cursor.fetchone()['total']
            
            # Get transactions with pagination (ALL accounts)
            cursor.execute(f"""
                SELECT 
                    transaction_id,
                    type,
                    amount,
                    balance_after,
                    description,
                    created_at
                FROM transactions 
                WHERE account_id IN ({placeholders})
                ORDER BY created_at DESC 
                LIMIT %s OFFSET %s
            """, account_ids + [limit, offset])
            
            transactions = cursor.fetchall()
            
            # Format transactions for response
            formatted_transactions = []
            for tx in transactions:
                formatted_transactions.append({
                    'id': tx['transaction_id'],
                    'type': tx['type'],
                    'amount': float(tx['amount']),
                    'balance_after': float(tx['balance_after']),
                    'description': tx['description'],
                    'date': tx['created_at'].isoformat() if tx['created_at'] else None
                })
            
            return {
                'transactions': formatted_transactions,
                'pagination': {
                    'total': total_count,
                    'limit': limit,
                    'offset': offset,
                    'has_more': (offset + len(transactions)) < total_count
                }
            }
            
        except Exception as e:
            return {'error': f'Failed to get transaction history: {str(e)}'}, 500
        finally:
            cursor.close()
            conn.close()

class TransactionDetail(Resource):
    def get(self, transaction_id):
        user_data = get_user_from_token()
        if not user_data:
            return {'error': 'Invalid or expired token'}, 401
        
        conn = get_db_connection()
        if not conn:
            return {'error': 'Database connection failed'}, 500
            
        try:
            cursor = conn.cursor(dictionary=True, buffered=True)
            
            # Get ALL user's account IDs
            cursor.execute("SELECT account_id FROM accounts WHERE user_id = %s", (user_data['user_id'],))
            accounts = cursor.fetchall()
            
            if not accounts:
                return {'error': 'No accounts found'}, 404

            account_ids = [acc['account_id'] for acc in accounts]
            placeholders = ', '.join(['%s'] * len(account_ids))

            # Get specific transaction from ANY user account
            cursor.execute(f"""
                SELECT 
                    t.transaction_id,
                    t.type,
                    t.amount,
                    t.balance_after,
                    t.description,
                    t.created_at,
                    a.account_number
                FROM transactions t
                JOIN accounts a ON t.account_id = a.account_id
                WHERE t.transaction_id = %s AND t.account_id IN ({placeholders})
            """, [transaction_id] + account_ids)
            
            transaction = cursor.fetchone()
            
            if not transaction:
                return {'error': 'Transaction not found'}, 404
            
            return {
                'transaction': {
                    'id': transaction['transaction_id'],
                    'type': transaction['type'],
                    'amount': float(transaction['amount']),
                    'balance_after': float(transaction['balance_after']),
                    'description': transaction['description'],
                    'date': transaction['created_at'].isoformat() if transaction['created_at'] else None,
                    'account_number': transaction['account_number']
                }
            }
            
        except Exception as e:
            return {'error': f'Failed to get transaction details: {str(e)}'}, 500
        finally:
            cursor.close()
            conn.close()