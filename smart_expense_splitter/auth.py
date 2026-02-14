# auth.py - User authentication management
import json
import os
import logging
import re
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

AUTH_FILE = "data/users.json"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AuthError(Exception):
    """Custom exception for auth operations"""
    pass

def validate_username(username):
    """Validate username format"""
    if not username or not isinstance(username, str):
        raise AuthError("Username must be a non-empty string")
    
    username = username.strip()
    if len(username) < 3:
        raise AuthError("Username must be at least 3 characters long")
    if len(username) > 50:
        raise AuthError("Username must be at most 50 characters long")
    
    # Allow alphanumeric, underscore, and hyphen
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        raise AuthError("Username can only contain letters, numbers, underscore, and hyphen")
    
    return username.strip()

def validate_password(password):
    """Validate password strength"""
    if not password or not isinstance(password, str):
        raise AuthError("Password must be a non-empty string")
    
    if len(password) < 6:
        raise AuthError("Password must be at least 6 characters long")
    if len(password) > 128:
        raise AuthError("Password must be at most 128 characters long")
    
    return password

def load_users():
    """Load users from JSON file with error handling"""
    if not os.path.exists(AUTH_FILE):
        logger.info("Auth file does not exist, creating new")
        return {}
    
    try:
        if os.path.getsize(AUTH_FILE) == 0:
            logger.warning("Auth file is empty")
            return {}
        
        with open(AUTH_FILE, "r", encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                return {}
            return json.loads(content)
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in auth file: {e}")
        return {}
    except Exception as e:
        logger.error(f"Error loading users: {e}")
        return {}

def save_users(users):
    """Save users to JSON file with backup"""
    try:
        os.makedirs("data", exist_ok=True)
        
        # Create backup before saving
        if os.path.exists(AUTH_FILE):
            backup_path = f"{AUTH_FILE}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            try:
                with open(AUTH_FILE, 'r', encoding='utf-8') as src:
                    with open(backup_path, 'w', encoding='utf-8') as dst:
                        dst.write(src.read())
                logger.info(f"Backup created: {backup_path}")
            except Exception as e:
                logger.warning(f"Could not create backup: {e}")
        
        with open(AUTH_FILE, "w", encoding='utf-8') as f:
            json.dump(users, f, indent=2, ensure_ascii=False)
        
        logger.info("Users saved successfully")
    except Exception as e:
        logger.error(f"Failed to save users: {e}")
        raise AuthError(f"Failed to save users: {e}")

def register_user(username, password):
    """Register a new user with hashed password and validation"""
    try:
        # Validate inputs
        username = validate_username(username)
        password = validate_password(password)
        
        users = load_users()
        
        if username in users:
            logger.warning(f"Registration failed: Username '{username}' already exists")
            return False, "Username already exists"
        
        # Hash the password with method='pbkdf2:sha256'
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        users[username] = {
            "password": hashed_password,
            "created_at": datetime.now().isoformat(),
            "last_login": None,
            "is_active": True
        }
        
        save_users(users)
        logger.info(f"User '{username}' registered successfully")
        return True, "User registered successfully"
    
    except AuthError as e:
        logger.warning(f"Registration validation error: {e}")
        return False, str(e)
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return False, "An error occurred during registration"

def verify_user(username, password):
    """Verify user credentials with enhanced security"""
    try:
        if not username or not password:
            return False, "Username and password are required"
        
        users = load_users()
        
        if username not in users:
            logger.warning(f"Login attempt with non-existent username: {username}")
            return False, "Invalid username or password"
        
        user_data = users[username]
        
        # Check if user is active
        if not user_data.get("is_active", True):
            logger.warning(f"Login attempt for inactive user: {username}")
            return False, "This account is inactive"
        
        # Check password hash
        if check_password_hash(user_data["password"], password):
            # Update last login
            users[username]["last_login"] = datetime.now().isoformat()
            save_users(users)
            logger.info(f"User '{username}' logged in successfully")
            return True, "Login successful"
        else:
            logger.warning(f"Failed login attempt for user: {username}")
            return False, "Invalid username or password"
    
    except Exception as e:
        logger.error(f"Verification error: {e}")
        return False, "An error occurred during login"

def user_exists(username):
    """Check if user exists"""
    users = load_users()
    return username in users

def change_password(username, old_password, new_password):
    """Change user password"""
    try:
        # Verify old password first
        is_valid, msg = verify_user(username, old_password)
        if not is_valid:
            return False, "Current password is incorrect"
        
        # Validate new password
        new_password = validate_password(new_password)
        
        if old_password == new_password:
            return False, "New password must be different from current password"
        
        users = load_users()
        users[username]["password"] = generate_password_hash(new_password, method='pbkdf2:sha256')
        save_users(users)
        
        logger.info(f"Password changed for user: {username}")
        return True, "Password changed successfully"
    
    except AuthError as e:
        return False, str(e)
    except Exception as e:
        logger.error(f"Password change error: {e}")
        return False, "An error occurred while changing password"

def deactivate_user(username):
    """Deactivate a user account"""
    try:
        users = load_users()
        
        if username not in users:
            return False, "User not found"
        
        users[username]["is_active"] = False
        save_users(users)
        
        logger.info(f"User deactivated: {username}")
        return True, "User deactivated successfully"
    
    except Exception as e:
        logger.error(f"Error deactivating user: {e}")
        return False, "An error occurred while deactivating user"
