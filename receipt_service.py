import random
import string
from datetime import datetime
from config import get_db_connection

class ReceiptService:
    def __init__(self):
        pass
    
    def generate_receipt_number(self, prefix='RCP'):
        """Generate unique receipt number"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_str = ''.join(random.choices(string.digits, k=6))
        return f"{prefix}{timestamp}{random_str}"
    
    def create_deposit_receipt(self, user_id, amount, account_number, description, transaction_id=None):
        """Create receipt for deposit transaction"""
        conn = get_db_connection()
        if not conn:
            return None
            
        try:
            cursor = conn.cursor(dictionary=True, buffered=True)
            
            receipt_number = self.generate_receipt_number('DEP')
            
            cursor.execute("""
                INSERT INTO transaction_receipts 
                (transaction_id, user_id, receipt_type, receipt_number, amount, description, to_account, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                transaction_id,
                user_id,
                'deposit',
                receipt_number,
                float(amount),
                description,
                account_number,
                '{"type": "cash_deposit", "status": "completed"}'
            ))
            
            receipt_id = cursor.lastrowid
            conn.commit()
            
            return self.get_receipt_by_id(receipt_id)
            
        except Exception as e:
            conn.rollback()
            print(f"Failed to create deposit receipt: {e}")
            return None
        finally:
            cursor.close()
            conn.close()
    
    def create_withdrawal_receipt(self, user_id, amount, account_number, description, transaction_id=None):
        """Create receipt for withdrawal transaction"""
        conn = get_db_connection()
        if not conn:
            return None
            
        try:
            cursor = conn.cursor(dictionary=True, buffered=True)
            
            receipt_number = self.generate_receipt_number('WDL')
            
            cursor.execute("""
                INSERT INTO transaction_receipts 
                (transaction_id, user_id, receipt_type, receipt_number, amount, description, from_account, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                transaction_id,
                user_id,
                'withdrawal',
                receipt_number,
                float(amount),
                description,
                account_number,
                '{"type": "cash_withdrawal", "status": "completed"}'
            ))
            
            receipt_id = cursor.lastrowid
            conn.commit()
            
            return self.get_receipt_by_id(receipt_id)
            
        except Exception as e:
            conn.rollback()
            print(f"Failed to create withdrawal receipt: {e}")
            return None
        finally:
            cursor.close()
            conn.close()
    
    def create_transfer_receipt(self, user_id, amount, from_account, to_account, description, transaction_id=None):
        """Create receipt for transfer transaction"""
        conn = get_db_connection()
        if not conn:
            return None
            
        try:
            cursor = conn.cursor(dictionary=True, buffered=True)
            
            receipt_number = self.generate_receipt_number('TRF')
            
            cursor.execute("""
                INSERT INTO transaction_receipts 
                (transaction_id, user_id, receipt_type, receipt_number, amount, description, from_account, to_account, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                transaction_id,
                user_id,
                'transfer',
                receipt_number,
                float(amount),
                description,
                from_account,
                to_account,
                '{"type": "account_transfer", "status": "completed"}'
            ))
            
            receipt_id = cursor.lastrowid
            conn.commit()
            
            return self.get_receipt_by_id(receipt_id)
            
        except Exception as e:
            conn.rollback()
            print(f"Failed to create transfer receipt: {e}")
            return None
        finally:
            cursor.close()
            conn.close()
    
    def create_crypto_funding_receipt(self, user_id, crypto_amount, usd_amount, currency, account_number, request_id=None):
        """Create receipt for crypto funding"""
        conn = get_db_connection()
        if not conn:
            return None
            
        try:
            cursor = conn.cursor(dictionary=True, buffered=True)
            
            receipt_number = self.generate_receipt_number('CRP')
            
            cursor.execute("""
                INSERT INTO transaction_receipts 
                (user_id, receipt_type, receipt_number, amount, currency, description, to_account, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                user_id,
                'crypto_funding',
                receipt_number,
                float(usd_amount),
                'USD',
                f'Crypto funding: {crypto_amount} {currency}',
                account_number,
                f'{{"type": "crypto_funding", "crypto_amount": {crypto_amount}, "currency": "{currency}", "request_id": {request_id}, "status": "completed"}}'
            ))
            
            receipt_id = cursor.lastrowid
            conn.commit()
            
            return self.get_receipt_by_id(receipt_id)
            
        except Exception as e:
            conn.rollback()
            print(f"Failed to create crypto funding receipt: {e}")
            return None
        finally:
            cursor.close()
            conn.close()
    
    def create_stock_trade_receipt(self, user_id, symbol, quantity, price, total_amount, trade_type, transaction_id=None):
        """Create receipt for stock trade"""
        conn = get_db_connection()
        if not conn:
            return None
            
        try:
            cursor = conn.cursor(dictionary=True, buffered=True)
            
            receipt_number = self.generate_receipt_number('STK')
            
            cursor.execute("""
                INSERT INTO transaction_receipts 
                (transaction_id, user_id, receipt_type, receipt_number, amount, description, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                transaction_id,
                user_id,
                'stock_trade',
                receipt_number,
                float(total_amount),
                f'Stock {trade_type}: {quantity} shares of {symbol}',
                f'{{"type": "stock_trade", "symbol": "{symbol}", "quantity": {quantity}, "price_per_share": {price}, "trade_type": "{trade_type}", "status": "completed"}}'
            ))
            
            receipt_id = cursor.lastrowid
            conn.commit()
            
            return self.get_receipt_by_id(receipt_id)
            
        except Exception as e:
            conn.rollback()
            print(f"Failed to create stock trade receipt: {e}")
            return None
        finally:
            cursor.close()
            conn.close()
    
    def get_receipt_by_id(self, receipt_id):
        """Get receipt details by ID"""
        conn = get_db_connection()
        if not conn:
            return None
            
        try:
            cursor = conn.cursor(dictionary=True, buffered=True)
            
            cursor.execute("""
                SELECT r.*, u.email, u.full_name 
                FROM transaction_receipts r
                JOIN users u ON r.user_id = u.user_id
                WHERE r.receipt_id = %s
            """, (receipt_id,))
            
            receipt = cursor.fetchone()
            return receipt
            
        except Exception as e:
            print(f"Failed to get receipt: {e}")
            return None
        finally:
            cursor.close()
            conn.close()
    
    def get_user_receipts(self, user_id, limit=50):
        """Get all receipts for a user"""
        conn = get_db_connection()
        if not conn:
            return None
            
        try:
            cursor = conn.cursor(dictionary=True, buffered=True)
            
            cursor.execute("""
                SELECT r.*, u.email, u.full_name 
                FROM transaction_receipts r
                JOIN users u ON r.user_id = u.user_id
                WHERE r.user_id = %s
                ORDER BY r.created_at DESC
                LIMIT %s
            """, (user_id, limit))
            
            receipts = cursor.fetchall()
            return receipts
            
        except Exception as e:
            print(f"Failed to get user receipts: {e}")
            return None
        finally:
            cursor.close()
            conn.close()

# Global receipt service instance
receipt_service = ReceiptService()