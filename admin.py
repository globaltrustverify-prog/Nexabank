from flask import request, jsonify
from flask_restful import Resource
from config import get_db_connection
import jwt
from decimal import Decimal
from passlib.hash import pbkdf2_sha256
import datetime
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

def get_admin_from_token():
    """Extract admin from authorization token - only users with is_admin=True"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    
    token = auth_header.split(' ')[1]
    user_data = verify_token(token)
    
    if not user_data:
        return None
    
    # Check if user is admin in database
    conn = get_db_connection()
    if not conn:
        return None
        
    try:
        cursor = conn.cursor(dictionary=True, buffered=True)
        cursor.execute("SELECT is_admin FROM users WHERE user_id = %s", (user_data['user_id'],))
        user = cursor.fetchone()
        
        if user and user['is_admin']:
            return user_data
        return None
    except:
        return None
    finally:
        cursor.close()
        conn.close()

def serialize_dates(obj):
    """Convert date/datetime objects to ISO format strings for JSON serialization"""
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: serialize_dates(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_dates(item) for item in obj]
    else:
        return obj

class AdminRegister(Resource):
    def post(self):
        """Register a new admin (protected endpoint)"""
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('password') or not data.get('full_name'):
            return {'error': 'Email, password, and full name are required'}, 400
        
        email = data['email']
        password = data['password']
        full_name = data['full_name']
        
        conn = get_db_connection()
        if not conn:
            return {'error': 'Database connection failed'}, 500
            
        try:
            cursor = conn.cursor(dictionary=True, buffered=True)
            
            # Check if email already exists
            cursor.execute("SELECT user_id FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                return {'error': 'Email already registered'}, 400
            
            # Hash password
            password_hash = pbkdf2_sha256.hash(password)
            
            # Insert new admin user
            cursor.execute(
                "INSERT INTO users (email, password_hash, full_name, is_admin) VALUES (%s, %s, %s, %s)",
                (email, password_hash, full_name, True)
            )
            
            user_id = cursor.lastrowid
            conn.commit()
            
            return {
                'message': 'Admin registered successfully',
                'user_id': user_id,
                'email': email,
                'is_admin': True
            }, 201
            
        except Exception as e:
            conn.rollback()
            return {'error': f'Admin registration failed: {str(e)}'}, 500
        finally:
            cursor.close()
            conn.close()

class AdminLogin(Resource):
    def post(self):
        """Admin login - only users with is_admin=True can login"""
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('password'):
            return {'error': 'Email and password are required'}, 400
        
        email = data['email']
        password = data['password']
        
        conn = get_db_connection()
        if not conn:
            return {'error': 'Database connection failed'}, 500
            
        try:
            cursor = conn.cursor(dictionary=True, buffered=True)
            
            # Get admin user by email
            cursor.execute("SELECT * FROM users WHERE email = %s AND is_admin = TRUE", (email,))
            admin = cursor.fetchone()
            
            if not admin:
                return {'error': 'Invalid email or not an admin'}, 401
            
            # Verify password
            if not pbkdf2_sha256.verify(password, admin['password_hash']):
                return {'error': 'Invalid password'}, 401
            
            # Generate JWT token
            token = jwt.encode({
                'user_id': admin['user_id'],
                'email': admin['email'],
                'is_admin': True,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
            }, 'your-secret-key-here-change-in-production', algorithm='HS256')
            
            return {
                'message': 'Admin login successful',
                'token': token,
                'admin': {
                    'user_id': admin['user_id'],
                    'email': admin['email'],
                    'full_name': admin['full_name'],
                    'is_admin': True
                }
            }
            
        except Exception as e:
            return {'error': f'Admin login failed: {str(e)}'}, 500
        finally:
            cursor.close()
            conn.close()

class AdminUsers(Resource):
    def get(self):
        """Get all users (Admin only)"""
        admin_data = get_admin_from_token()
        if not admin_data:
            return {'error': 'Admin access required'}, 403
        
        conn = get_db_connection()
        if not conn:
            return {'error': 'Database connection failed'}, 500
            
        try:
            cursor = conn.cursor(dictionary=True, buffered=True)
            
            cursor.execute("""
                SELECT 
                    user_id, email, full_name, phone, date_of_birth,
                    is_admin, created_at, updated_at
                FROM users 
                ORDER BY created_at DESC
            """)
            
            users = cursor.fetchall()
            
            # ✅ FIX: Serialize all dates to ISO format strings
            formatted_users = []
            for user in users:
                formatted_users.append({
                    'user_id': user['user_id'],
                    'email': user['email'],
                    'full_name': user['full_name'],
                    'phone': user['phone'],
                    'date_of_birth': user['date_of_birth'].isoformat() if user['date_of_birth'] else None,
                    'is_admin': bool(user['is_admin']),
                    'created_at': user['created_at'].isoformat() if user['created_at'] else None,
                    'updated_at': user['updated_at'].isoformat() if user['updated_at'] else None
                })
            
            return {
                'users': formatted_users,
                'total_users': len(users)
            }
            
        except Exception as e:
            print(f"❌ AdminUsers error: {str(e)}")
            return {'error': f'Failed to get users: {str(e)}'}, 500
        finally:
            cursor.close()
            conn.close()

class AdminUserAccounts(Resource):
    def get(self, user_id):
        """Get all accounts for a specific user (Admin only)"""
        admin_data = get_admin_from_token()
        if not admin_data:
            return {'error': 'Admin access required'}, 403
        
        conn = get_db_connection()
        if not conn:
            return {'error': 'Database connection failed'}, 500
            
        try:
            cursor = conn.cursor(dictionary=True, buffered=True)
            
            # Get user info
            cursor.execute("SELECT user_id, email, full_name FROM users WHERE user_id = %s", (user_id,))
            user = cursor.fetchone()
            
            if not user:
                return {'error': 'User not found'}, 404
            
            # Get user's accounts
            cursor.execute("""
                SELECT 
                    account_id, account_number, account_type, balance, created_at
                FROM accounts 
                WHERE user_id = %s 
                ORDER BY created_at DESC
            """, (user_id,))
            
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
                'user': {
                    'user_id': user['user_id'],
                    'email': user['email'],
                    'full_name': user['full_name']
                },
                'accounts': formatted_accounts,
                'total_balance': float(total_balance),
                'account_count': len(accounts)
            }
            
        except Exception as e:
            return {'error': f'Failed to get user accounts: {str(e)}'}, 500
        finally:
            cursor.close()
            conn.close()

class AdminAdjustBalance(Resource):
    def post(self):
        """Admin: Add or subtract from user account balance"""
        admin_data = get_admin_from_token()
        if not admin_data:
            return {'error': 'Admin access required'}, 403
        
        data = request.get_json()
        required_fields = ['user_id', 'account_type', 'amount', 'description']
        for field in required_fields:
            if not data or not data.get(field):
                return {'error': f'{field} is required'}, 400
        
        user_id = data['user_id']
        account_type = data['account_type']
        description = data['description']
        
        try:
            amount = Decimal(str(data['amount']))
        except ValueError:
            return {'error': 'Invalid amount'}, 400
        
        conn = get_db_connection()
        if not conn:
            return {'error': 'Database connection failed'}, 500
            
        try:
            cursor = conn.cursor(dictionary=True, buffered=True)
            
            # Get user account
            cursor.execute("""
                SELECT account_id, account_number, balance 
                FROM accounts 
                WHERE user_id = %s AND account_type = %s
            """, (user_id, account_type))
            
            account = cursor.fetchone()
            
            if not account:
                return {'error': 'Account not found'}, 404
            
            # Calculate new balance
            current_balance = Decimal(str(account['balance']))
            new_balance = current_balance + amount
            
            # Prevent negative balance
            if new_balance < 0:
                return {'error': 'Balance cannot be negative'}, 400
            
            # Update balance
            cursor.execute(
                "UPDATE accounts SET balance = %s WHERE account_id = %s",
                (float(new_balance), account['account_id'])
            )
            
            # Record admin transaction
            transaction_type = 'deposit' if amount > 0 else 'withdraw'
            cursor.execute(
                "INSERT INTO transactions (account_id, type, amount, balance_after, description) VALUES (%s, %s, %s, %s, %s)",
                (account['account_id'], transaction_type, float(abs(amount)), float(new_balance), f'Admin adjustment: {description}')
            )
            
            conn.commit()
            
            return {
                'message': 'Balance adjusted successfully',
                'adjustment_details': {
                    'user_id': user_id,
                    'account_number': account['account_number'],
                    'account_type': account_type,
                    'amount': float(amount),
                    'previous_balance': float(current_balance),
                    'new_balance': float(new_balance),
                    'description': description
                }
            }
            
        except Exception as e:
            conn.rollback()
            return {'error': f'Balance adjustment failed: {str(e)}'}, 500
        finally:
            cursor.close()
            conn.close()

class AdminAddStock(Resource):
    def post(self):
        """Admin: Add new stock to the system"""
        admin_data = get_admin_from_token()
        if not admin_data:
            return {'error': 'Admin access required'}, 403
        
        data = request.get_json()
        required_fields = ['symbol', 'company_name']
        for field in required_fields:
            if not data or not data.get(field):
                return {'error': f'{field} is required'}, 400
        
        symbol = data['symbol'].upper()
        company_name = data['company_name']
        initial_price = data.get('initial_price', 100.00)
        
        conn = get_db_connection()
        if not conn:
            return {'error': 'Database connection failed'}, 500
            
        try:
            cursor = conn.cursor(dictionary=True, buffered=True)
            
            # Check if stock already exists
            cursor.execute("SELECT stock_id FROM stocks WHERE symbol = %s", (symbol,))
            if cursor.fetchone():
                return {'error': 'Stock already exists'}, 400
            
            # Add new stock
            cursor.execute("""
                INSERT INTO stocks (symbol, company_name, current_price, daily_change, daily_change_percent)
                VALUES (%s, %s, %s, %s, %s)
            """, (symbol, company_name, float(initial_price), 0.0, 0.0))
            
            stock_id = cursor.lastrowid
            conn.commit()
            
            return {
                'message': 'Stock added successfully',
                'stock': {
                    'stock_id': stock_id,
                    'symbol': symbol,
                    'company_name': company_name,
                    'initial_price': float(initial_price)
                }
            }, 201
            
        except Exception as e:
            conn.rollback()
            return {'error': f'Failed to add stock: {str(e)}'}, 500
        finally:
            cursor.close()
            conn.close()

class AdminUpdateStockPrice(Resource):
    def post(self):
        """Admin: Manually update stock price"""
        admin_data = get_admin_from_token()
        if not admin_data:
            return {'error': 'Admin access required'}, 403
        
        data = request.get_json()
        required_fields = ['symbol', 'new_price']
        for field in required_fields:
            if not data or not data.get(field):
                return {'error': f'{field} is required'}, 400
        
        symbol = data['symbol'].upper()
        
        try:
            new_price = Decimal(str(data['new_price']))
            if new_price <= 0:
                return {'error': 'Price must be positive'}, 400
        except ValueError:
            return {'error': 'Invalid price'}, 400
        
        conn = get_db_connection()
        if not conn:
            return {'error': 'Database connection failed'}, 500
            
        try:
            cursor = conn.cursor(dictionary=True, buffered=True)
            
            # Get current stock price
            cursor.execute("SELECT current_price FROM stocks WHERE symbol = %s", (symbol,))
            stock = cursor.fetchone()
            
            if not stock:
                return {'error': 'Stock not found'}, 404
            
            current_price = Decimal(str(stock['current_price']))
            daily_change = new_price - current_price
            daily_change_percent = (daily_change / current_price * 100) if current_price > 0 else 0
            
            # Update stock price
            cursor.execute("""
                UPDATE stocks 
                SET current_price = %s, daily_change = %s, daily_change_percent = %s, last_updated = CURRENT_TIMESTAMP
                WHERE symbol = %s
            """, (float(new_price), float(daily_change), float(daily_change_percent), symbol))
            
            conn.commit()
            
            return {
                'message': 'Stock price updated successfully',
                'stock': {
                    'symbol': symbol,
                    'previous_price': float(current_price),
                    'new_price': float(new_price),
                    'daily_change': float(daily_change),
                    'daily_change_percent': float(daily_change_percent)
                }
            }
            
        except Exception as e:
            conn.rollback()
            return {'error': f'Failed to update stock price: {str(e)}'}, 500
        finally:
            cursor.close()
            conn.close()

class AdminAllStocks(Resource):
    def get(self):
        """Admin: Get all stocks in the system"""
        admin_data = get_admin_from_token()
        if not admin_data:
            return {'error': 'Admin access required'}, 403
        
        conn = get_db_connection()
        if not conn:
            return {'error': 'Database connection failed'}, 500
            
        try:
            cursor = conn.cursor(dictionary=True, buffered=True)
            
            cursor.execute("""
                SELECT stock_id, symbol, company_name, current_price, daily_change, daily_change_percent, last_updated
                FROM stocks 
                ORDER BY symbol
            """)
            
            stocks = cursor.fetchall()
            
            formatted_stocks = []
            for stock in stocks:
                formatted_stocks.append({
                    'stock_id': stock['stock_id'],
                    'symbol': stock['symbol'],
                    'company_name': stock['company_name'],
                    'current_price': float(stock['current_price']),
                    'daily_change': float(stock['daily_change']),
                    'daily_change_percent': float(stock['daily_change_percent']),
                    'last_updated': stock['last_updated'].isoformat() if stock['last_updated'] else None
                })
            
            return {
                'stocks': formatted_stocks,
                'total_stocks': len(stocks)
            }
            
        except Exception as e:
            return {'error': f'Failed to get stocks: {str(e)}'}, 500
        finally:
            cursor.close()
            conn.close()

class AdminStockTransactions(Resource):
    def get(self):
        """Admin: Get all stock transactions in the system"""
        admin_data = get_admin_from_token()
        if not admin_data:
            return {'error': 'Admin access required'}, 403
        
        conn = get_db_connection()
        if not conn:
            return {'error': 'Database connection failed'}, 500
            
        try:
            cursor = conn.cursor(dictionary=True, buffered=True)
            
            cursor.execute("""
                SELECT st.*, u.email, u.full_name, s.company_name
                FROM stock_transactions st
                JOIN users u ON st.user_id = u.user_id
                JOIN stocks s ON st.symbol = s.symbol
                ORDER BY st.created_at DESC
                LIMIT 100
            """)
            
            transactions = cursor.fetchall()
            
            formatted_transactions = []
            for tx in transactions:
                formatted_transactions.append({
                    'transaction_id': tx['transaction_id'],
                    'user_id': tx['user_id'],
                    'user_email': tx['email'],
                    'user_name': tx['full_name'],
                    'symbol': tx['symbol'],
                    'company_name': tx['company_name'],
                    'type': tx['type'],
                    'quantity': float(tx['quantity']),
                    'price': float(tx['price']),
                    'total_amount': float(tx['total_amount']),
                    'order_type': tx['order_type'],
                    'status': tx['status'],
                    'created_at': tx['created_at'].isoformat() if tx['created_at'] else None
                })
            
            return {
                'transactions': formatted_transactions,
                'total_transactions': len(transactions)
            }
            
        except Exception as e:
            return {'error': f'Failed to get stock transactions: {str(e)}'}, 500
        finally:
            cursor.close()
            conn.close()

class AdminCryptoFundingRequests(Resource):
    def get(self):
        """Admin: Get all pending crypto funding requests"""
        admin_data = get_admin_from_token()
        if not admin_data:
            return {'error': 'Admin access required'}, 403
        
        conn = get_db_connection()
        if not conn:
            return {'error': 'Database connection failed'}, 500
            
        try:
            cursor = conn.cursor(dictionary=True, buffered=True)
            
            cursor.execute("""
                SELECT cfr.*, u.email, u.full_name, a.account_number
                FROM crypto_funding_requests cfr
                JOIN users u ON cfr.user_id = u.user_id
                LEFT JOIN accounts a ON u.user_id = a.user_id AND a.account_type = 'checking'
                WHERE cfr.status = 'pending'
                ORDER BY cfr.created_at DESC
            """)
            
            requests = cursor.fetchall()
            
            formatted_requests = []
            for req in requests:
                formatted_requests.append({
                    'request_id': req['request_id'],
                    'user_id': req['user_id'],
                    'user_email': req['email'],
                    'user_name': req['full_name'],
                    'account_number': req['account_number'],
                    'currency': req['currency'],
                    'crypto_amount': float(req['crypto_amount']),
                    'usd_amount': float(req['usd_amount']),
                    'status': req['status'],
                    'admin_notes': req['admin_notes'],
                    'created_at': req['created_at'].isoformat() if req['created_at'] else None,
                    'updated_at': req['updated_at'].isoformat() if req['updated_at'] else None
                })
            
            return {
                'pending_requests': formatted_requests,
                'total_pending': len(requests)
            }
            
        except Exception as e:
            return {'error': f'Failed to get funding requests: {str(e)}'}, 500
        finally:
            cursor.close()
            conn.close()

class AdminApproveCryptoFunding(Resource):
    def post(self):
        """Admin: Approve a crypto funding request"""
        admin_data = get_admin_from_token()
        if not admin_data:
            return {'error': 'Admin access required'}, 403
        
        data = request.get_json()
        if not data or not data.get('request_id'):
            return {'error': 'Request ID is required'}, 400
        
        request_id = data['request_id']
        admin_notes = data.get('admin_notes', 'Approved by admin')
        target_account_type = data.get('account_type', 'checking')  # Allow override, default checking
        
        conn = get_db_connection()
        if not conn:
            return {'error': 'Database connection failed'}, 500
            
        try:
            cursor = conn.cursor(dictionary=True, buffered=True)
            
            # Get the funding request
            cursor.execute("""
                SELECT cfr.*, u.email
                FROM crypto_funding_requests cfr
                JOIN users u ON cfr.user_id = u.user_id
                WHERE cfr.request_id = %s AND cfr.status = 'pending'
            """, (request_id,))
            
            funding_request = cursor.fetchone()
            
            if not funding_request:
                return {'error': 'Pending funding request not found'}, 404
            
            user_id = funding_request['user_id']
            currency = funding_request['currency']
            crypto_amount = Decimal(str(funding_request['crypto_amount']))
            usd_amount = Decimal(str(funding_request['usd_amount']))
            
            # Get user's target bank account (flexible type)
            cursor.execute("""
                SELECT account_id, account_number, balance 
                FROM accounts 
                WHERE user_id = %s AND account_type = %s
            """, (user_id, target_account_type))
            
            account = cursor.fetchone()
            
            if not account:
                return {'error': f'User {target_account_type} account not found'}, 404
            
            # Update bank balance
            new_bank_balance = Decimal(str(account['balance'])) + usd_amount
            cursor.execute(
                "UPDATE accounts SET balance = %s WHERE account_id = %s",
                (float(new_bank_balance), account['account_id'])
            )
            
            # Get/update crypto wallet
            cursor.execute("""
                SELECT wallet_id, balance FROM crypto_wallets 
                WHERE user_id = %s AND currency = %s
            """, (user_id, currency))
            
            crypto_wallet = cursor.fetchone()
            if not crypto_wallet:
                return {'error': f'User crypto wallet for {currency} not found'}, 404
            
            new_crypto_balance = Decimal(str(crypto_wallet['balance'])) + crypto_amount
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
                account['account_id'],
                'deposit',
                float(usd_amount),
                float(new_bank_balance),
                f'Crypto funding approved: {crypto_amount:.8f} {currency} ({admin_notes})'
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
            
            # Update funding request status
            cursor.execute("""
                UPDATE crypto_funding_requests 
                SET status = 'approved', admin_notes = %s, updated_at = CURRENT_TIMESTAMP
                WHERE request_id = %s
            """, (admin_notes, request_id))
            
            conn.commit()
            
            return {
                'message': 'Crypto funding approved successfully',
                'funding_details': {
                    'request_id': request_id,
                    'user_id': user_id,
                    'user_email': funding_request['email'],
                    'currency': currency,
                    'crypto_amount': float(crypto_amount),
                    'usd_amount': float(usd_amount),
                    'account_type': target_account_type,
                    'account_number': account['account_number'],
                    'previous_bank_balance': float(account['balance']),
                    'new_bank_balance': float(new_bank_balance),
                    'previous_crypto_balance': float(crypto_wallet['balance']),
                    'new_crypto_balance': float(new_crypto_balance),
                    'admin_notes': admin_notes
                }
            }
            
        except Exception as e:
            conn.rollback()
            print(f"Approval error: {str(e)}")  # Log for debug
            return {'error': f'Failed to approve funding: {str(e)}'}, 500
        finally:
            cursor.close()
            conn.close()

class AdminRejectCryptoFunding(Resource):
    def post(self):
        """Admin: Reject a crypto funding request"""
        admin_data = get_admin_from_token()
        if not admin_data:
            return {'error': 'Admin access required'}, 403
        
        data = request.get_json()
        if not data or not data.get('request_id'):
            return {'error': 'Request ID is required'}, 400
        
        request_id = data['request_id']
        admin_notes = data.get('admin_notes', 'Rejected by admin')
        
        conn = get_db_connection()
        if not conn:
            return {'error': 'Database connection failed'}, 500
            
        try:
            cursor = conn.cursor(dictionary=True, buffered=True)
            
            # Get the funding request
            cursor.execute("""
                SELECT cfr.*, u.email
                FROM crypto_funding_requests cfr
                JOIN users u ON cfr.user_id = u.user_id
                WHERE cfr.request_id = %s AND cfr.status = 'pending'
            """, (request_id,))
            
            funding_request = cursor.fetchone()
            
            if not funding_request:
                return {'error': 'Pending funding request not found'}, 404
            
            # Update funding request status to rejected
            cursor.execute("""
                UPDATE crypto_funding_requests 
                SET status = 'rejected', admin_notes = %s, updated_at = CURRENT_TIMESTAMP
                WHERE request_id = %s
            """, (admin_notes, request_id))
            
            conn.commit()
            
            return {
                'message': 'Crypto funding rejected successfully',
                'rejection_details': {
                    'request_id': request_id,
                    'user_id': funding_request['user_id'],
                    'user_email': funding_request['email'],
                    'currency': funding_request['currency'],
                    'crypto_amount': float(funding_request['crypto_amount']),
                    'usd_amount': float(funding_request['usd_amount']),
                    'admin_notes': admin_notes
                }
            }
            
        except Exception as e:
            conn.rollback()
            return {'error': f'Failed to reject funding: {str(e)}'}, 500
        finally:
            cursor.close()
            conn.close()