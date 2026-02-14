# decorators.py - Custom decorators and middleware
from functools import wraps
from flask import session, redirect, url_for, request, flash
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Rate limiting dictionary - in production, use Redis
rate_limit_store = {}

def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('You must be logged in to access this page', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin role (can be extended)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('You must be logged in', 'error')
            return redirect(url_for('login'))
        
        # Check if user is admin (can be implemented with database)
        # For now, just check if logged in
        return f(*args, **kwargs)
    return decorated_function

def rate_limit(max_requests=10, time_window=3600):
    """Decorator to implement rate limiting per IP"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            client_ip = request.remote_addr
            current_time = datetime.now()
            
            # Initialize or get rate limit data
            if client_ip not in rate_limit_store:
                rate_limit_store[client_ip] = []
            
            # Remove old requests outside time window
            rate_limit_store[client_ip] = [
                req_time for req_time in rate_limit_store[client_ip]
                if (current_time - req_time).total_seconds() < time_window
            ]
            
            # Check if limit exceeded
            if len(rate_limit_store[client_ip]) >= max_requests:
                logger.warning(f"Rate limit exceeded for IP: {client_ip}")
                flash('Too many requests. Please try again later.', 'error')
                return redirect(url_for('dashboard'))
            
            # Add current request
            rate_limit_store[client_ip].append(current_time)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def validate_json(f):
    """Decorator to validate JSON requests"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.is_json:
            try:
                request.get_json()
            except Exception as e:
                logger.error(f"Invalid JSON request: {e}")
                flash('Invalid request format', 'error')
                return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def handle_exceptions(f):
    """Decorator to handle exceptions gracefully"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            logger.warning(f"Validation error: {e}")
            flash(f'Validation error: {str(e)}', 'error')
            return redirect(url_for('dashboard'))
        except Exception as e:
            logger.error(f"Unexpected error in {f.__name__}: {e}")
            flash('An unexpected error occurred. Please try again.', 'error')
            return redirect(url_for('dashboard'))
    return decorated_function

def require_method(*methods):
    """Decorator to require specific HTTP methods"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if request.method not in methods:
                logger.warning(f"Invalid method {request.method} for {f.__name__}")
                flash('Invalid request method', 'error')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def log_action(action_type):
    """Decorator to log user actions"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            username = session.get('username', 'anonymous')
            logger.info(f"User '{username}' performed action: {action_type}")
            return f(*args, **kwargs)
        return decorated_function
    return decorator
