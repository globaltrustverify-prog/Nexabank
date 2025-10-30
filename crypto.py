from flask import request, jsonify
from flask_restful import Resource
from config import get_db_connection
import jwt
from decimal import Decimal
from services.crypto_service import crypto_service
import datetime

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

def serialize_datetime(obj):
    """Convert datetime objects to ISO format strings for JSON serialization"""
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

class CryptoWallets(Resource):
    def get(self):
        """Get user's crypto wallets and balances"""
        user_data = get_user_from_token()
        if not user_data:
            return {'error': 'Invalid or expired token'}, 401
        
        conn = get_db_connection()
        if not conn:
            return {'error': 'Database connection failed'}, 500
            
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Get or create wallets for user
            wallets = []
            for currency in crypto_service.config.SUPPORTED_CRYPTO:
                cursor.execute("""
                    SELECT * FROM crypto_wallets 
                    WHERE user_id = %s AND currency = %s
                """, (user_data['user_id'], currency))
                
                wallet = cursor.fetchone()
                
                if not wallet:
                    # Create new wallet if doesn't exist
                    address = crypto_service.generate_mock_address(user_data['user_id'], currency)
                    cursor.execute("""
                        INSERT INTO crypto_wallets (user_id, currency, address, balance)
                        VALUES (%s, %s, %s, %s)
                    """, (user_data['user_id'], currency, address, 0.00000000))
                    
                    wallet_id = cursor.lastrowid
                    wallet = {
                        'wallet_id': wallet_id,
                        'currency': currency,
                        'address': address,
                        'balance': 0.00000000,
                        'created_at': datetime.datetime.now()
                    }
                else:
                    wallet = dict(wallet)
                
                # Convert balance to float for JSON
                wallet['balance'] = float(wallet['balance'])
                wallet['balance_usd'] = float(
                    crypto_service.convert_crypto_to_usd(wallet['balance'], currency)
                )
                
                # Convert datetime to string
                if 'created_at' in wallet and wallet['created_at']:
                    wallet['created_at'] = wallet['created_at'].isoformat() if hasattr(wallet['created_at'], 'isoformat') else str(wallet['created_at'])
                
                wallets.append(wallet)
            
            conn.commit()
            
            # Get live prices
            live_prices = crypto_service.get_live_prices()
            
            return {
                'wallets': wallets,
                'live_prices': {k: float(v) for k, v in live_prices.items()}
            }
            
        except Exception as e:
            conn.rollback()
            return {'error': f'Failed to get crypto wallets: {str(e)}'}, 500
        finally:
            cursor.close()
            conn.close()

class CryptoDeposit(Resource):
    def post(self):
        """Initiate crypto deposit (generate address and expected amount)"""
        user_data = get_user_from_token()
        if not user_data:
            return {'error': 'Invalid or expired token'}, 401
        
        data = request.get_json()
        if not data or not data.get('currency') or not data.get('usd_amount'):
            return {'error': 'Currency and USD amount are required'}, 400
        
        currency = data['currency'].upper()
        if currency not in crypto_service.config.SUPPORTED_CRYPTO:
            return {'error': f'Unsupported currency. Supported: {", ".join(crypto_service.config.SUPPORTED_CRYPTO)}'}, 400
        
        try:
            usd_amount = Decimal(str(data['usd_amount']))
            if usd_amount <= 0:
                return {'error': 'Amount must be positive'}, 400
        except ValueError:
            return {'error': 'Invalid amount'}, 400
        
        # Convert USD to crypto
        crypto_amount = crypto_service.convert_usd_to_crypto(usd_amount, currency)
        
        # Get wallet address
        conn = get_db_connection()
        if not conn:
            return {'error': 'Database connection failed'}, 500
            
        try:
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT address FROM crypto_wallets 
                WHERE user_id = %s AND currency = %s
            """, (user_data['user_id'], currency))
            
            wallet = cursor.fetchone()
            if not wallet:
                return {'error': 'Wallet not found'}, 404
            
            return {
                'message': 'Deposit instructions',
                'currency': currency,
                'deposit_address': wallet['address'],
                'expected_amount': float(crypto_amount),
                'usd_amount': float(usd_amount),
                'note': f'Send exactly {crypto_amount:.8f} {currency} to the address above. Deposit will be credited after 1 confirmation.'
            }
            
        except Exception as e:
            return {'error': f'Deposit failed: {str(e)}'}, 500
        finally:
            cursor.close()
            conn.close()

class CryptoWithdraw(Resource):
    def post(self):
        """Withdraw cryptocurrency to external address"""
        user_data = get_user_from_token()
        if not user_data:
            return {'error': 'Invalid or expired token'}, 401
        
        data = request.get_json()
        required_fields = ['currency', 'amount', 'to_address']
        for field in required_fields:
            if not data or not data.get(field):
                return {'error': f'{field.replace("_", " ").title()} is required'}, 400
        
        currency = data['currency'].upper()
        to_address = data['to_address']
        
        if currency not in crypto_service.config.SUPPORTED_CRYPTO:
            return {'error': f'Unsupported currency. Supported: {", ".join(crypto_service.config.SUPPORTED_CRYPTO)}'}, 400
        
        try:
            amount = Decimal(str(data['amount']))
            if amount <= 0:
                return {'error': 'Amount must be positive'}, 400
        except ValueError:
            return {'error': 'Invalid amount'}, 400
        
        # Check minimum withdrawal
        min_withdrawal = crypto_service.get_min_withdrawal(currency)
        if amount < min_withdrawal:
            return {'error': f'Minimum withdrawal for {currency} is {min_withdrawal}'}, 400
        
        conn = get_db_connection()
        if not conn:
            return {'error': 'Database connection failed'}, 500
            
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Get wallet balance
            cursor.execute("""
                SELECT wallet_id, balance FROM crypto_wallets 
                WHERE user_id = %s AND currency = %s
            """, (user_data['user_id'], currency))
            
            wallet = cursor.fetchone()
            if not wallet:
                return {'error': 'Wallet not found'}, 404
            
            # Calculate network fee
            network_fee = crypto_service.get_network_fee(currency)
            total_amount = amount + network_fee
            
            # Check sufficient balance
            if Decimal(str(wallet['balance'])) < total_amount:
                return {'error': f'Insufficient balance. Need {total_amount} {currency} (including network fee)'}, 400
            
            # Update wallet balance
            new_balance = Decimal(str(wallet['balance'])) - total_amount
            cursor.execute(
                "UPDATE crypto_wallets SET balance = %s WHERE wallet_id = %s",
                (float(new_balance), wallet['wallet_id'])
            )
            
            # Record withdrawal transaction
            cursor.execute("""
                INSERT INTO crypto_transactions 
                (wallet_id, type, amount, usd_value, address, status)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                wallet['wallet_id'], 
                'withdrawal', 
                float(amount),
                float(crypto_service.convert_crypto_to_usd(amount, currency)),
                to_address,
                'pending'  # In real app, this would wait for blockchain confirmation
            ))
            
            conn.commit()
            
            return {
                'message': 'Withdrawal initiated',
                'currency': currency,
                'amount': float(amount),
                'network_fee': float(network_fee),
                'total_deducted': float(total_amount),
                'to_address': to_address,
                'new_balance': float(new_balance),
                'status': 'pending'
            }
            
        except Exception as e:
            conn.rollback()
            return {'error': f'Withdrawal failed: {str(e)}'}, 500
        finally:
            cursor.close()
            conn.close()

class CryptoSell(Resource):
    def post(self):
        """Sell cryptocurrency for USD (deposit to bank account)"""
        user_data = get_user_from_token()
        if not user_data:
            return {'error': 'Invalid or expired token'}, 401
        
        data = request.get_json()
        if not data or not data.get('currency') or not data.get('amount'):
            return {'error': 'Currency and amount are required'}, 400
        
        currency = data['currency'].upper()
        if currency not in crypto_service.config.SUPPORTED_CRYPTO:
            return {'error': f'Unsupported currency. Supported: {", ".join(crypto_service.config.SUPPORTED_CRYPTO)}'}, 400
        
        try:
            crypto_amount = Decimal(str(data['amount']))
            if crypto_amount <= 0:
                return {'error': 'Amount must be positive'}, 400
        except ValueError:
            return {'error': 'Invalid amount'}, 400
        
        conn = get_db_connection()
        if not conn:
            return {'error': 'Database connection failed'}, 500
            
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Get wallet balance
            cursor.execute("""
                SELECT wallet_id, balance FROM crypto_wallets 
                WHERE user_id = %s AND currency = %s
            """, (user_data['user_id'], currency))
            
            wallet = cursor.fetchone()
            if not wallet:
                return {'error': 'Wallet not found'}, 404
            
            # Check sufficient crypto balance
            if Decimal(str(wallet['balance'])) < crypto_amount:
                return {'error': 'Insufficient crypto balance'}, 400
            
            # Convert to USD
            usd_amount = crypto_service.convert_crypto_to_usd(crypto_amount, currency)
            
            # Get user's primary bank account
            cursor.execute("""
                SELECT account_id, balance FROM accounts 
                WHERE user_id = %s 
                ORDER BY created_at 
                LIMIT 1
            """, (user_data['user_id'],))
            
            bank_account = cursor.fetchone()
            if not bank_account:
                return {'error': 'Bank account not found'}, 404
            
            # Update crypto wallet balance
            new_crypto_balance = Decimal(str(wallet['balance'])) - crypto_amount
            cursor.execute(
                "UPDATE crypto_wallets SET balance = %s WHERE wallet_id = %s",
                (float(new_crypto_balance), wallet['wallet_id'])
            )
            
            # Update bank account balance
            new_bank_balance = Decimal(str(bank_account['balance'])) + usd_amount
            cursor.execute(
                "UPDATE accounts SET balance = %s WHERE account_id = %s",
                (float(new_bank_balance), bank_account['account_id'])
            )
            
            # Record crypto transaction
            cursor.execute("""
                INSERT INTO crypto_transactions 
                (wallet_id, type, amount, usd_value, status)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                wallet['wallet_id'], 
                'withdrawal', 
                float(crypto_amount),
                float(usd_amount),
                'confirmed'
            ))
            
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
                f'Crypto sale: {crypto_amount} {currency}'
            ))
            
            conn.commit()
            
            return {
                'message': 'Crypto sold successfully',
                'sold': float(crypto_amount),
                'currency': currency,
                'received_usd': float(usd_amount),
                'new_crypto_balance': float(new_crypto_balance),
                'new_bank_balance': float(new_bank_balance)
            }
            
        except Exception as e:
            conn.rollback()
            return {'error': f'Sell failed: {str(e)}'}, 500
        finally:
            cursor.close()
            conn.close()
