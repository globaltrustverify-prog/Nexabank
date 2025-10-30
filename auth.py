from flask import request, jsonify
from flask_restful import Resource
from config import get_db_connection
from passlib.hash import pbkdf2_sha256
import re
import jwt
import datetime

class Register(Resource):
    def post(self):
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'password', 'full_name', 'phone', 'date_of_birth', 'address']
        for field in required_fields:
            if not data or not data.get(field):
                return {'error': f'{field.replace("_", " ").title()} is required'}, 400
        
        email = data['email']
        password = data['password']
        full_name = data['full_name']
        phone = data['phone']
        date_of_birth = data['date_of_birth']
        address = data['address']
        
        # Validate email format
        if not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            return {'error': 'Invalid email format'}, 400
        
        # Validate password strength
        if len(password) < 6:
            return {'error': 'Password must be at least 6 characters'}, 400
        
        # Validate date of birth (must be 18+ years)
        try:
            dob = datetime.datetime.strptime(date_of_birth, '%Y-%m-%d')
            age = (datetime.datetime.now() - dob).days // 365
            if age < 18:
                return {'error': 'You must be at least 18 years old to register'}, 400
        except ValueError:
            return {'error': 'Invalid date format. Use YYYY-MM-DD'}, 400
        
        conn = get_db_connection()
        if not conn:
            return {'error': 'Database connection failed'}, 500
            
        try:
            cursor = conn.cursor()
            
            # Check if email already exists
            cursor.execute("SELECT user_id FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                return {'error': 'Email already registered'}, 400
            
            # Hash password
            password_hash = pbkdf2_sha256.hash(password)
            
            # Insert new user with all fields
            cursor.execute(
                """INSERT INTO users 
                (email, password_hash, full_name, phone, date_of_birth, address) 
                VALUES (%s, %s, %s, %s, %s, %s)""",
                (email, password_hash, full_name, phone, date_of_birth, address)
            )
            
            user_id = cursor.lastrowid
            conn.commit()
            
            return {
                'message': 'User registered successfully',
                'user_id': user_id,
                'email': email
            }, 201
            
        except Exception as e:
            conn.rollback()
            return {'error': f'Registration failed: {str(e)}'}, 500
        finally:
            cursor.close()
            conn.close()

class Login(Resource):
    def post(self):
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('password'):
            return {'error': 'Email and password are required'}, 400
        
        email = data['email']
        password = data['password']
        
        conn = get_db_connection()
        if not conn:
            return {'error': 'Database connection failed'}, 500
            
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Get user by email
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            
            if not user:
                return {'error': 'Invalid email or password'}, 401
            
            # Verify password
            if not pbkdf2_sha256.verify(password, user['password_hash']):
                return {'error': 'Invalid email or password'}, 401
            
            # Check if user is admin
            is_admin = bool(user.get('is_admin', 0))
            
            # Generate JWT token
            token = jwt.encode({
                'user_id': user['user_id'],
                'email': user['email'],
                'is_admin': is_admin,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
            }, 'your-secret-key-here-change-in-production', algorithm='HS256')
            
            return {
                'message': 'Login successful',
                'token': token,
                'user': {
                    'user_id': user['user_id'],
                    'email': user['email'],
                    'full_name': user['full_name'],
                    'is_admin': is_admin
                }
            }
            
        except Exception as e:
            return {'error': f'Login failed: {str(e)}'}, 500
        finally:
            cursor.close()
            conn.close()
