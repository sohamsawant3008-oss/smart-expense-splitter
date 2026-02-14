# config.py - Configuration settings for the application
import os
from datetime import timedelta

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Upload configuration
    UPLOAD_FOLDER = 'static/receipts'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
    
    # Database
    DATA_FOLDER = 'data'
    EXPENSES_FILE = os.path.join(DATA_FOLDER, 'expenses.json')
    USERS_FILE = os.path.join(DATA_FOLDER, 'users.json')
    
    # Logging
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'app.log'
    
    # Security
    PASSWORD_MIN_LENGTH = 6
    PASSWORD_MAX_LENGTH = 128
    USERNAME_MIN_LENGTH = 3
    USERNAME_MAX_LENGTH = 50
    
    # Features
    ENABLE_EMAIL_NOTIFICATIONS = False
    ENABLE_DUPLICATE_DETECTION = True
    DUPLICATE_THRESHOLD = 0.01  # $0.01
    
    # Export
    EXPORT_FORMAT_CSV = 'csv'
    EXPORT_FORMAT_PDF = 'pdf'
    EXPORT_FORMAT_JSON = 'json'

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    SESSION_COOKIE_SECURE = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    ENABLE_EMAIL_NOTIFICATIONS = True

class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    DATA_FOLDER = 'test_data'
    EXPENSES_FILE = os.path.join(DATA_FOLDER, 'expenses_test.json')
    USERS_FILE = os.path.join(DATA_FOLDER, 'users_test.json')

# Get config based on environment
env = os.environ.get('FLASK_ENV', 'development')
if env == 'production':
    app_config = ProductionConfig
elif env == 'testing':
    app_config = TestingConfig
else:
    app_config = DevelopmentConfig
