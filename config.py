import os
import mysql.connector

class Config:
    DB_HOST = 'yamanote.proxy.rlwy.net'
    DB_USER = 'root'
    DB_PASSWORD = os.getenv('DB_PASSWORD')   # stored in environment
    DB_NAME = 'railway'
    DB_PORT = 51620

    SECRET_KEY = 'your-secret-key-change-in-production'

def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            port=Config.DB_PORT
        )
        print("✅ Connected to Railway MySQL successfully!")
        return conn
    except mysql.connector.Error as e:
        print(f"❌ Database connection error: {e}")
        return None
