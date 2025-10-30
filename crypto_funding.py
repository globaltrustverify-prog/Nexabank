from flask import request, jsonify
from flask_restful import Resource
from config import get_db_connection
import jwt
from decimal import Decimal
from services.crypto_service import crypto_service

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

class CryptoToBankDeposit(Resource):
    def post(self):
        """Calculate how much crypto to send to fund bank account"""
        user_data = get_user_from_token()
        if not user_data:
            return {'error': 'Invalid or expired token'}, 401
        
        data = request.get_json()
        if not data or not data.get('usd_amount') or not data.get('currency'):
            return {'error': 'USD amount and currency are required'}, 400
        
        currency = data['currency'].upper()
        target_account_type = data.get('account_type', 'savings')  # savings or checking
        
        if currency not in crypto_service.config.SUPPORTED_CRYPTO:
            return {'error': f'Unsupported currency. Supported: {", ".join(crypto_service.config.SUPPORTED_CRYPTO)}'}, 400
        
        if target_account_type not in ['savings', 'checking']:
            return {'error': 'Account type must be savings or checking'}, 400
        
        try:
            usd_amount = Decimal(str(data['usd_amount']))
            if usd_amount <= 0:
                return {'error': 'Amount must be positive'}, 400
            
            # Check minimum deposit for account type
            if target_account_type == 'savings' and usd_amount < 100:
                return {'error': 'Minimum deposit for savings account is $100'}, 400
            elif target_account_type == 'checking' and usd_amount < 50:
                return {'error': 'Minimum deposit for checking account is $50'}, 400
                
        except ValueError:
            return {'error': 'Invalid amount'}, 400
        
        # Convert USD to crypto amount
        crypto_amount = crypto_service.convert_usd_to_crypto(usd_amount, currency)
        
        # Get crypto wallet address
        conn = get_db_connection()
        if not conn:
            return {'error': 'Database connection failed'}, 500
            
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Get crypto wallet address
            cursor.execute("""
                SELECT address FROM crypto_wallets 
                WHERE user_id = %s AND currency = %s
            """, (user_data['user_id'], currency))
            
            wallet = cursor.fetchone()
            if not wallet:
                return {'error': 'Crypto wallet not found'}, 404
            
            # Get target bank account
            cursor.execute("""
                SELECT account_number FROM accounts 
                WHERE user_id = %s AND account_type = %s
            """, (user_data['user_id'], target_account_type))
            
            bank_account = cursor.fetchone()
            if not bank_account:
                return {'error': f'{target_account_type.title()} account not found'}, 404
            
            return {
                'message': 'Crypto funding instructions',
                'funding_details': {
                    'fund_usd_amount': float(usd_amount),
                    'send_crypto_amount': float(crypto_amount),
                    'crypto_currency': currency,
                    'to_crypto_address': wallet['address'],
                    'to_bank_account': bank_account['account_number'],
                    'bank_account_type': target_account_type,
                    'exchange_rate': float(crypto_service.get_live_prices()[currency]),
                    'note': f'Send exactly {crypto_amount:.8f} {currency} to fund your {target_account_type} account with ${usd_amount:.2f} USD'
                }
            }
            
        except Exception as e:
            return {'error': f'Funding calculation failed: {str(e)}'}, 500
        finally:
            cursor.close()
            conn.close()

class BankToCryptoWithdraw(Resource):
    def post(self):
        """Withdraw from bank account to receive cryptocurrency"""
        user_data = get_user_from_token()
        if not user_data:
            return {'error': 'Invalid or expired token'}, 401
        
        data = request.get_json()
        if not data or not data.get('usd_amount') or not data.get('currency'):
            return {'error': 'USD amount and currency are required'}, 400
        
        currency = data['currency'].upper()
        source_account_type = data.get('account_type', 'savings')  # savings or checking
        
        if currency not in crypto_service.config.SUPPORTED_CRYPTO:
            return {'error': f'Unsupported currency. Supported: {", ".join(crypto_service.config.SUPPORTED_CRYPTO)}'}, 400
        
        if source_account_type not in ['savings', 'checking']:
            return {'error': 'Account type must be savings or checking'}, 400
        
        try:
            usd_amount = Decimal(str(data['usd_amount']))
            if usd_amount <= 0:
                return {'error': 'Amount must be positive'}, 400
        except ValueError:
            return {'error': 'Invalid amount'}, 400
        
        # Convert USD to crypto amount
        crypto_amount = crypto_service.convert_usd_to_crypto(usd_amount, currency)
        
        conn = get_db_connection()
        if not conn:
            return {'error': 'Database connection failed'}, 500
            
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Get source bank account
            cursor.execute("""
                SELECT account_id, account_number, balance FROM accounts 
                WHERE user_id = %s AND account_type = %s
            """, (user_data['user_id'], source_account_type))
            
            bank_account = cursor.fetchone()
            if not bank_account:
                return {'error': f'{source_account_type.title()} account not found'}, 404
            
            # Check sufficient bank balance
            if Decimal(str(bank_account['balance'])) < usd_amount:
                return {'error': f'Insufficient balance in {source_account_type} account'}, 400
            
            # Check minimum balance after withdrawal
            new_bank_balance = Decimal(str(bank_account['balance'])) - usd_amount
            if source_account_type == 'savings' and new_bank_balance < Decimal('10'):
                return {'error': 'Savings account must maintain minimum balance of $10'}, 400
            elif source_account_type == 'checking' and new_bank_balance < Decimal('5'):
                return {'error': 'Checking account must maintain minimum balance of $5'}, 400
            
            # Get crypto wallet
            cursor.execute("""
                SELECT wallet_id, address FROM crypto_wallets 
                WHERE user_id = %s AND currency = %s
            """, (user_data['user_id'], currency))
            
            crypto_wallet = cursor.fetchone()
            if not crypto_wallet:
                return {'error': 'Crypto wallet not found'}, 404
            
            # Update bank account balance
            cursor.execute(
                "UPDATE accounts SET balance = %s WHERE account_id = %s",
                (float(new_bank_balance), bank_account['account_id'])
            )
            
            # Update crypto wallet balance
            current_crypto_balance = Decimal(str(crypto_wallet.get('balance', 0)))
            new_crypto_balance = current_crypto_balance + crypto_amount
            cursor.execute(
                "UPDATE crypto_wallets SET balance = %s WHERE wallet_id = %s",
                (float(new_crypto_balance), crypto_wallet['wallet_id'])
            )
            
            # Record bank withdrawal transaction
            cursor.execute("""
                INSERT INTO transactions 
                (account_id, type, amount, balance_after, description)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                bank_account['account_id'],
                'withdraw',
                float(usd_amount),
                float(new_bank_balance),
                f'Crypto purchase: {crypto_amount:.8f} {currency}'
            ))
            
            # Record crypto deposit transaction
            cursor.execute("""
                INSERT INTO crypto_transactions 
                (wallet_id, type, amount, usd_value, status)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                crypto_wallet['wallet_id'],
                'deposit',
                float(crypto_amount),
                float(usd_amount),
                'confirmed'
            ))
            
            conn.commit()
            
            return {
                'message': 'Bank to crypto withdrawal successful',
                'withdrawal_details': {
                    'withdrawn_usd': float(usd_amount),
                    'received_crypto': float(crypto_amount),
                    'crypto_currency': currency,
                    'to_crypto_address': crypto_wallet['address'],
                    'from_bank_account': bank_account['account_number'],
                    'bank_account_type': source_account_type,
                    'new_bank_balance': float(new_bank_balance),
                    'new_crypto_balance': float(new_crypto_balance),
                    'exchange_rate': float(crypto_service.get_live_prices()[currency])
                }
            }
            
        except Exception as e:
            conn.rollback()
            return {'error': f'Bank to crypto withdrawal failed: {str(e)}'}, 500
        finally:
            cursor.close()
            conn.close()

class SimulateCryptoDeposit(Resource):
    def post(self):
        """Simulate receiving crypto to fund bank account (for testing)"""
        user_data = get_user_from_token()
        if not user_data:
            return {'error': 'Invalid or expired token'}, 401
        
        data = request.get_json()
        if not data or not data.get('currency') or not data.get('crypto_amount'):
            return {'error': 'Currency and crypto amount are required'}, 400
        
        currency = data['currency'].upper()
        target_account_type = data.get('account_type', 'savings')
        
        if currency not in crypto_service.config.SUPPORTED_CRYPTO:
            return {'error': f'Unsupported currency. Supported: {", ".join(crypto_service.config.SUPPORTED_CRYPTO)}'}, 400
        
        try:
            crypto_amount = Decimal(str(data['crypto_amount']))
            if crypto_amount <= 0:
                return {'error': 'Amount must be positive'}, 400
        except ValueError:
            return {'error': 'Invalid amount'}, 400
        
        # Convert crypto to USD
        usd_amount = crypto_service.convert_crypto_to_usd(crypto_amount, currency)
        
        conn = get_db_connection()
        if not conn:
            return {'error': 'Database connection failed'}, 500
            
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Get target bank account
            cursor.execute("""
                SELECT account_id, account_number, balance FROM accounts 
                WHERE user_id = %s AND account_type = %s
            """, (user_data['user_id'], target_account_type))
            
            bank_account = cursor.fetchone()
            if not bank_account:
                return {'error': f'{target_account_type.title()} account not found'}, 404
            
            # Get crypto wallet
            cursor.execute("""
                SELECT wallet_id, balance FROM crypto_wallets 
                WHERE user_id = %s AND currency = %s
            """, (user_data['user_id'], currency))
            
            crypto_wallet = cursor.fetchone()
            if not crypto_wallet:
                return {'error': 'Crypto wallet not found'}, 404
            
            # Update bank account balance
            new_bank_balance = Decimal(str(bank_account['balance'])) + usd_amount
            cursor.execute(
                "UPDATE accounts SET balance = %s WHERE account_id = %s",
                (float(new_bank_balance), bank_account['account_id'])
            )
            
            # Update crypto wallet balance (simulate receiving crypto)
            current_crypto_balance = Decimal(str(crypto_wallet.get('balance', 0)))
            new_crypto_balance = current_crypto_balance + crypto_amount
            cursor.execute(
                "UPDATE crypto_wallets SET balance = %s WHERE wallet_id = %s",
                (float(new_crypto_balance), crypto_wallet['wallet_id'])
            )
            
            # Record bank deposit transaction
            cursor.execute("""
                INSERT INTO transactions 
                (account_id, type, amount, balance_after, description)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                bank_account['account_id'],
                'deposit',
                float(usd_amount),
                float(new_bank_balance),
                f'Crypto funding: {crypto_amount:.8f} {currency}'
            ))
            
            # Record crypto deposit transaction
            cursor.execute("""
                INSERT INTO crypto_transactions 
                (wallet_id, type, amount, usd_value, status)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                crypto_wallet['wallet_id'],
                'deposit',
                float(crypto_amount),
                float(usd_amount),
                'confirmed'
            ))
            
            conn.commit()
            
            return {
                'message': 'Crypto deposit simulated successfully',
                'deposit_details': {
                    'received_crypto': float(crypto_amount),
                    'credited_usd': float(usd_amount),
                    'crypto_currency': currency,
                    'to_bank_account': bank_account['account_number'],
                    'bank_account_type': target_account_type,
                    'new_bank_balance': float(new_bank_balance),
                    'new_crypto_balance': float(new_crypto_balance),
                    'exchange_rate': float(crypto_service.get_live_prices()[currency])
                }
            }
            
        except Exception as e:
            conn.rollback()
            return {'error': f'Crypto deposit simulation failed: {str(e)}'}, 500
        finally:
            cursor.close()
            conn.close()

class RequestCryptoFunding(Resource):
    def post(self):
        """User: Request to fund account through crypto"""
        user_data = get_user_from_token()
        if not user_data:
            return {'error': 'Invalid or expired token'}, 401
        
        data = request.get_json()
        if not data or not data.get('currency') or not data.get('crypto_amount'):
            return {'error': 'Currency and crypto amount are required'}, 400
        
        currency = data['currency'].upper()
        if currency not in crypto_service.config.SUPPORTED_CRYPTO:
            return {'error': f'Unsupported currency. Supported: {", ".join(crypto_service.config.SUPPORTED_CRYPTO)}'}, 400
        
        try:
            crypto_amount = Decimal(str(data['crypto_amount']))
            if crypto_amount <= 0:
                return {'error': 'Amount must be positive'}, 400
        except ValueError:
            return {'error': 'Invalid amount'}, 400
        
        account_type = data.get('account_type', 'checking')  # NEW: Capture from frontend
        
        # Convert crypto to USD
        usd_amount = crypto_service.convert_crypto_to_usd(crypto_amount, currency)
        
        conn = get_db_connection()
        if not conn:
            return {'error': 'Database connection failed'}, 500
            
        try:
            cursor = conn.cursor(dictionary=True, buffered=True)
            
            # Create crypto funding request with account_type
            cursor.execute("""
                INSERT INTO crypto_funding_requests 
                (user_id, currency, crypto_amount, usd_amount, status, account_type)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (user_data['user_id'], currency, float(crypto_amount), float(usd_amount), 'pending', account_type))
            
            request_id = cursor.lastrowid
            conn.commit()
            
            return {
                'message': 'Crypto funding request submitted successfully',
                'request_id': request_id,
                'funding_details': {
                    'currency': currency,
                    'crypto_amount': float(crypto_amount),
                    'usd_amount': float(usd_amount),
                    'status': 'pending',
                    'account_type': account_type,
                    'note': 'Your request is pending admin approval. You will be notified once processed.'
                }
            }, 201
            
        except Exception as e:
            conn.rollback()
            return {'error': f'Failed to submit funding request: {str(e)}'}, 500
        finally:
            cursor.close()
            conn.close()

# NEW: User Pending Requests Endpoint
class GetUserPendingFundingRequests(Resource):
    def get(self):
        """Get user's pending crypto funding requests"""
        user_data = get_user_from_token()
        if not user_data:
            return {'error': 'Invalid or expired token'}, 401
        
        conn = get_db_connection()
        if not conn:
            return {'error': 'Database connection failed'}, 500
            
        try:
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT request_id, currency, crypto_amount, usd_amount, status, created_at, account_type
                FROM crypto_funding_requests 
                WHERE user_id = %s AND status = 'pending'
                ORDER BY created_at DESC
                LIMIT 5
            """, (user_data['user_id'],))
            
            requests = cursor.fetchall()
            
            formatted_requests = []
            for req in requests:
                formatted_requests.append({
                    'request_id': req['request_id'],
                    'currency': req['currency'],
                    'crypto_amount': float(req['crypto_amount']),
                    'usd_amount': float(req['usd_amount']),
                    'status': req['status'],
                    'created_at': req['created_at'].isoformat() if req['created_at'] else None,
                    'account_type': req['account_type']
                })
            
            return {
                'pending_requests': formatted_requests,
                'total_pending': len(requests)
            }
            
        except Exception as e:
            return {'error': f'Failed to get pending requests: {str(e)}'}, 500
        finally:
            cursor.close()
            conn.close()