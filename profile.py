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

class UserProfile(Resource):
    def get(self):
        """Get user profile information"""
        user_data = get_user_from_token()
        if not user_data:
            return {'error': 'Invalid or expired token'}, 401
        
        conn = get_db_connection()
        if not conn:
            return {'error': 'Database connection failed'}, 500
            
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Get user basic info
            cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_data['user_id'],))
            user = cursor.fetchone()
            
            # Get user profile
            cursor.execute("SELECT * FROM user_profiles WHERE user_id = %s", (user_data['user_id'],))
            profile = cursor.fetchone()
            
            # Get user address
            cursor.execute("SELECT * FROM user_addresses WHERE user_id = %s", (user_data['user_id'],))
            address = cursor.fetchone()
            
            # Get KYC documents
            cursor.execute("SELECT * FROM kyc_documents WHERE user_id = %s", (user_data['user_id'],))
            documents = cursor.fetchall()
            
            # Create or update profile if doesn't exist
            if not profile:
                cursor.execute("""
                    INSERT INTO user_profiles (user_id, daily_limit, monthly_limit)
                    VALUES (%s, %s, %s)
                """, (user_data['user_id'], 100.00, 1000.00))
                conn.commit()
                
                cursor.execute("SELECT * FROM user_profiles WHERE user_id = %s", (user_data['user_id'],))
                profile = cursor.fetchone()
            
            return {
                'user': {
                    'user_id': user['user_id'],
                    'email': user['email'],
                    'full_name': user['full_name'],
                    'phone': user.get('phone', ''),
                    'date_of_birth': user.get('date_of_birth'),
                    'address': user.get('address', '')
                },
                'profile': {
                    'kyc_tier': profile['kyc_tier'],
                    'daily_limit': float(profile['daily_limit']),
                    'monthly_limit': float(profile['monthly_limit']),
                    'phone_verified': bool(profile['phone_verified']),
                    'email_verified': bool(profile['email_verified'])
                } if profile else None,
                'address': address,
                'documents': documents,
                'verification_status': self.calculate_verification_status(profile, address, documents)
            }
            
        except Exception as e:
            return {'error': f'Failed to get profile: {str(e)}'}, 500
        finally:
            cursor.close()
            conn.close()
    
    def put(self):
        """Update user profile information"""
        user_data = get_user_from_token()
        if not user_data:
            return {'error': 'Invalid or expired token'}, 401
        
        data = request.get_json()
        if not data:
            return {'error': 'No data provided'}, 400
        
        conn = get_db_connection()
        if not conn:
            return {'error': 'Database connection failed'}, 500
            
        try:
            cursor = conn.cursor(dictionary=True)
            
            update_fields = []
            update_values = []
            
            # Allowed fields to update
            allowed_fields = ['full_name', 'phone', 'date_of_birth', 'address']
            
            for field in allowed_fields:
                if field in data:
                    update_fields.append(f"{field} = %s")
                    update_values.append(data[field])
            
            if update_fields:
                update_values.append(user_data['user_id'])
                cursor.execute(
                    f"UPDATE users SET {', '.join(update_fields)} WHERE user_id = %s",
                    update_values
                )
            
            # Update address if provided
            if 'address_line1' in data:
                cursor.execute("SELECT * FROM user_addresses WHERE user_id = %s", (user_data['user_id'],))
                existing_address = cursor.fetchone()
                
                if existing_address:
                    cursor.execute("""
                        UPDATE user_addresses 
                        SET address_line1 = %s, address_line2 = %s, city = %s, 
                            state = %s, country = %s, postal_code = %s
                        WHERE user_id = %s
                    """, (
                        data.get('address_line1'),
                        data.get('address_line2', ''),
                        data.get('city'),
                        data.get('state'),
                        data.get('country'),
                        data.get('postal_code'),
                        user_data['user_id']
                    ))
                else:
                    cursor.execute("""
                        INSERT INTO user_addresses 
                        (user_id, address_line1, address_line2, city, state, country, postal_code)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        user_data['user_id'],
                        data.get('address_line1'),
                        data.get('address_line2', ''),
                        data.get('city'),
                        data.get('state'),
                        data.get('country'),
                        data.get('postal_code')
                    ))
            
            conn.commit()
            
            return {'message': 'Profile updated successfully'}
            
        except Exception as e:
            conn.rollback()
            return {'error': f'Failed to update profile: {str(e)}'}, 500
        finally:
            cursor.close()
            conn.close()
    
    def calculate_verification_status(self, profile, address, documents):
        """Calculate current verification status"""
        status = {
            'email_verified': bool(profile and profile['email_verified']),
            'phone_verified': bool(profile and profile['phone_verified']),
            'address_verified': bool(address and address['verified']),
            'id_verified': any(doc for doc in documents if doc['document_type'] in ['id_card', 'passport', 'driver_license'] and doc['status'] == 'verified')
        }
        
        # Determine current KYC tier
        if status['id_verified'] and status['address_verified']:
            current_tier = 'full_kyc'
        elif status['id_verified']:
            current_tier = 'id_verified'
        elif status['email_verified'] and status['phone_verified']:
            current_tier = 'basic'
        else:
            current_tier = 'unverified'
        
        status['current_tier'] = current_tier
        status['next_tier'] = self.get_next_tier(current_tier)
        
        return status
    
    def get_next_tier(self, current_tier):
        """Get the next KYC tier and requirements"""
        tiers = ['unverified', 'basic', 'id_verified', 'full_kyc']
        current_index = tiers.index(current_tier)
        
        if current_index < len(tiers) - 1:
            next_tier = tiers[current_index + 1]
            requirements = {
                'basic': ['Verify email', 'Verify phone number'],
                'id_verified': ['Upload government ID'],
                'full_kyc': ['Verify address']
            }
            return {
                'tier': next_tier,
                'requirements': requirements.get(next_tier, [])
            }
        return None

class VerifyPhone(Resource):
    def post(self):
        """Initiate phone verification (mock for now)"""
        user_data = get_user_from_token()
        if not user_data:
            return {'error': 'Invalid or expired token'}, 401
        
        conn = get_db_connection()
        if not conn:
            return {'error': 'Database connection failed'}, 500
            
        try:
            cursor = conn.cursor()
            
            # In real app, send SMS verification code
            # For demo, we'll just mark as verified
            cursor.execute("""
                UPDATE user_profiles 
                SET phone_verified = TRUE 
                WHERE user_id = %s
            """, (user_data['user_id'],))
            
            conn.commit()
            
            return {'message': 'Phone verification initiated. In production, an SMS would be sent.'}
            
        except Exception as e:
            conn.rollback()
            return {'error': f'Phone verification failed: {str(e)}'}, 500
        finally:
            cursor.close()
            conn.close()

class VerifyEmail(Resource):
    def post(self):
        """Initiate email verification (mock for now)"""
        user_data = get_user_from_token()
        if not user_data:
            return {'error': 'Invalid or expired token'}, 401
        
        conn = get_db_connection()
        if not conn:
            return {'error': 'Database connection failed'}, 500
            
        try:
            cursor = conn.cursor()
            
            # In real app, send email verification link
            # For demo, we'll just mark as verified
            cursor.execute("""
                UPDATE user_profiles 
                SET email_verified = TRUE 
                WHERE user_id = %s
            """, (user_data['user_id'],))
            
            conn.commit()
            
            return {'message': 'Email verification initiated. In production, an email would be sent.'}
            
        except Exception as e:
            conn.rollback()
            return {'error': f'Email verification failed: {str(e)}'}, 500
        finally:
            cursor.close()
            conn.close()

class KYCDocuments(Resource):
    def post(self):
        """Upload KYC document (mock for now)"""
        user_data = get_user_from_token()
        if not user_data:
            return {'error': 'Invalid or expired token'}, 401
        
        data = request.get_json()
        if not data or not data.get('document_type'):
            return {'error': 'Document type is required'}, 400
        
        document_type = data['document_type']
        document_number = data.get('document_number', '')
        
        conn = get_db_connection()
        if not conn:
            return {'error': 'Database connection failed'}, 500
            
        try:
            cursor = conn.cursor()
            
            # In real app, handle file upload and storage
            # For demo, we'll just create a database entry
            cursor.execute("""
                INSERT INTO kyc_documents 
                (user_id, document_type, document_number, file_path, status)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                user_data['user_id'],
                document_type,
                document_number,
                'mock_file_path',  # In production, this would be the actual file path
                'pending'
            ))
            
            conn.commit()
            
            return {'message': 'KYC document uploaded successfully. Awaiting verification.'}
            
        except Exception as e:
            conn.rollback()
            return {'error': f'Document upload failed: {str(e)}'}, 500
        finally:
            cursor.close()
            conn.close()
