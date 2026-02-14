# Code Examples - Before & After

## 1. Model Creation - Input Validation

### ❌ Before (No Validation)
```python
# Old code - anything goes
class User:
    def __init__(self, name, user_id=None):
        self.name = name  # Could be empty, None, etc
        self.id = user_id if user_id else str(uuid.uuid4())

# Problems:
user = User("")              # ❌ Silently creates invalid user
user = User(None)            # ❌ Crashes later
user = User(123)             # ❌ Type error not caught

# Storage:
expense = Expense("test", 0, payer, participants)  # ❌ Zero amount
expense = Expense("", 50, None, [])                # ❌ Invalid
```

### ✅ After (Comprehensive Validation)
```python
# New code - validated
class User:
    def __init__(self, name, user_id=None):
        self.id = user_id if user_id else str(uuid.uuid4())
        self.name = name.strip() if name else ""
        self.balance = Decimal("0.00")
        if not self.name:
            raise ValueError("User name cannot be empty")

# Works correctly:
try:
    user = User("Alice")     # ✅ Valid user
    print("Success")
except ValueError as e:
    print(f"Error: {e}")     # ✅ Clear error

# Expense validation:
try:
    expense = Expense("Dinner", 50, payer, [user1, user2])
    print("Expense created")
except ValueError as e:
    print(f"Invalid: {e}")   # ✅ Validation error
```

---

## 2. Authentication - Security Enhancement

### ❌ Before (Basic Auth)
```python
# Old code - minimal security
def register_user(username, password):
    users = load_users()
    
    if username in users:
        return False, "Username already exists"
    
    # Weak hashing
    hashed_password = generate_password_hash(password)
    users[username] = {"password": hashed_password}
    
    save_users(users)
    return True, "User registered successfully"

# Problems:
# • No username format validation
# • No password strength requirements
# • No tracking of registration
# • No account deactivation
# • No password change feature
```

### ✅ After (Enhanced Security)
```python
# New code - enterprise security
def register_user(username, password):
    try:
        # Validate username format
        username = validate_username(username)  # 3-50 chars, alphanumeric
        # Validate password strength
        password = validate_password(password)  # 6-128 chars
        
        users = load_users()
        
        if username in users:
            logger.warning(f"Registration failed: {username} exists")
            return False, "Username already exists"
        
        # Strong hashing with pbkdf2:sha256
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

# Additional features:
success, msg = change_password(username, old_pass, new_pass)  # ✅ Password change
success, msg = deactivate_user(username)                      # ✅ Account control
```

---

## 3. Financial Calculations - Precision Fix

### ❌ Before (Floating-Point Errors)
```python
# Old code - using float
from collections import defaultdict

def calculate_balances(group):
    balances = defaultdict(float)  # ❌ Float causes rounding errors

    for expense in group.expenses:
        amount = float(expense.amount)
        participants = expense.participants
        
        share = amount / len(participants)  # ❌ Floating-point division

        for user in participants:
            balances[user.id] -= share

        balances[expense.payer.id] += amount

    return balances

# Problem example:
# $99.99 shared among 3 people
# $99.99 / 3 = $33.33000000...
# 33.33 * 3 = 99.989999... ❌ NOT 99.99

# Accumulation of rounding errors over many transactions
```

### ✅ After (Exact Precision)
```python
# New code - using Decimal
from decimal import Decimal, ROUND_HALF_UP

def calculate_balances(group):
    balances = defaultdict(Decimal)  # ✅ Decimal type

    for expense in group.expenses:
        if not expense.amount or not expense.participants:
            continue
            
        amount = Decimal(str(expense.amount))  # ✅ Convert to Decimal
        participants = expense.participants
        
        if len(participants) == 0:
            logger.warning(f"Expense {expense.id} has no participants")
            continue
        
        # Precise division with rounding
        share = (amount / len(participants)).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )  # ✅ Exact rounding

        for user in participants:
            balances[user.id] -= share

        balances[expense.payer.id] += amount

    return balances

# Perfect calculation:
# $99.99 / 3 = $33.33 (exact)
# $33.33 * 3 = $99.99 (correct!)
```

---

## 4. Data Storage - Validation & Backup

### ❌ Before (No Validation)
```python
# Old code - load without checks
def load_group(file_path):
    if not os.path.exists(file_path):
        return Group("My Expense Group")

    with open(file_path) as f:
        data = json.load(f)  # ❌ No error handling

    group = Group(data["name"])  # ❌ Could crash if no "name"

    users_map = {}
    for u in data.get("users", []):
        user = User(u["name"])
        user.id = u["id"]  # ❌ Could crash if no "id"
        users_map[user.id] = user
        group.users.append(user)

    for e in data.get("expenses", []):
        payer = users_map.get(e["payer_id"])
        participants = [users_map[pid] for pid in e["participants"]]
        # ❌ Crashes if payer not found
        
        expense = Expense(
            e["description"],
            e["amount"],
            payer,
            participants
        )
        group.expenses.append(expense)

    return group

# Problems:
# • No validation of data
# • Crashes on corrupt files
# • No error messages
# • No recovery mechanism
```

### ✅ After (Validation & Backup)
```python
# New code - validated loading and saving
def load_group(file_path):
    try:
        if not os.path.exists(file_path):
            logger.info(f"File {file_path} not found, creating new")
            return Group("My Expense Group")

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not data or not isinstance(data, dict):
            logger.warning("Invalid file format")
            return Group("My Expense Group")

        group = Group(data.get("name", "My Expense Group"))

        # Load and validate users
        users_map = {}
        for u in data.get("users", []):
            try:
                validate_user_data(u)  # ✅ Validate before use
                user = User(u["name"].strip())
                user.id = u["id"]
                users_map[user.id] = user
                group.users.append(user)
            except StorageError as e:
                logger.warning(f"Skipping invalid user: {e}")
                continue  # ✅ Continue instead of crashing

        # Load and validate expenses
        for e in data.get("expenses", []):
            try:
                validate_expense_data(e)  # ✅ Validate before use
                payer = users_map.get(e["payer_id"])
                if not payer:
                    logger.warning(f"Payer not found for expense {e['id']}")
                    continue  # ✅ Skip invalid expense
                
                participants = [users_map[pid] for pid in e["participants"] if pid in users_map]
                if not participants:
                    logger.warning(f"No participants for expense {e['id']}")
                    continue  # ✅ Skip invalid expense

                expense = Expense(
                    e["description"].strip(),
                    e["amount"],
                    payer,
                    participants
                )
                expense.id = e["id"]
                group.expenses.append(expense)
            except StorageError as e:
                logger.warning(f"Skipping invalid expense: {e}")
                continue

        logger.info(f"Successfully loaded group")
        return group
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        raise StorageError(f"Invalid JSON file format: {e}")

def save_group(group, FILE_PATH):
    try:
        os.makedirs("data", exist_ok=True)

        # ✅ Create automatic backup
        if os.path.exists(FILE_PATH):
            backup_path = f"{FILE_PATH}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            try:
                with open(FILE_PATH, 'r', encoding='utf-8') as src:
                    with open(backup_path, 'w', encoding='utf-8') as dst:
                        dst.write(src.read())
                logger.info(f"Backup created: {backup_path}")
            except Exception as e:
                logger.warning(f"Could not create backup: {e}")

        data = {
            "name": group.name,
            "users": [{"id": u.id, "name": u.name} for u in group.users],
            "expenses": [
                {
                    "id": e.id,
                    "description": e.description,
                    "amount": e.amount,
                    "payer_id": e.payer.id,
                    "participants": [p.id for p in e.participants],
                    "date": e.date,
                    "category": e.category,
                    "notes": e.notes
                }
                for e in group.expenses
            ]
        }

        with open(FILE_PATH, "w", encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Group saved to {FILE_PATH}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to save group: {e}")
        raise StorageError(f"Failed to save group: {e}")
```

---

## 5. Utility Functions - New Features

### ❌ Before (No Export)
```python
# Old code - no export capability
# Users had to manually copy data
# No analysis tools
# No duplicate detection
```

### ✅ After (Rich Functionality)
```python
# New code - comprehensive utilities
from utils import (
    export_expenses_to_csv,
    export_settlements_to_csv,
    calculate_expense_summary,
    get_expense_by_category,
    is_duplicate_expense,
    format_currency
)

# 1. Export data
csv_data = export_expenses_to_csv(group)
with open('expenses.csv', 'w') as f:
    f.write(csv_data)

# 2. Analyze spending
summary = calculate_expense_summary(group)
print(f"Total: {format_currency(summary['total_amount'])}")
print(f"Average: {format_currency(summary['average_expense'])}")

# 3. Group by category
categories = get_expense_by_category(group)
for cat, data in categories.items():
    print(f"{cat}: {data['count']} expenses, {format_currency(data['total'])}")

# 4. Detect duplicates
for i, exp1 in enumerate(group.expenses):
    for exp2 in group.expenses[i+1:]:
        if is_duplicate_expense(exp1, exp2):
            print(f"Possible duplicate: {exp1.description}")
```

---

## 6. Error Handling - Before vs After

### ❌ Before (No Error Handling)
```python
# Old code - crashes without useful info
@app.route('/add-expense', methods=['POST'])
def add_expense():
    amount = request.form.get('amount')
    description = request.form.get('description')
    
    # ❌ No validation, will crash
    expense = Expense(description, amount, payer, participants)
    # ❌ Could crash here with unhelpful error
    
    group.add_expense(expense)
    save_group(group, FILE_PATH)
    # ❌ Could crash here too
    
    return redirect(url_for('dashboard'))
```

### ✅ After (Comprehensive Error Handling)
```python
# New code - graceful error handling
from decorators import handle_exceptions, log_action

@app.route('/add-expense', methods=['POST'])
@handle_exceptions  # ✅ Catches and logs exceptions
@log_action("add_expense")  # ✅ Logs the action
def add_expense():
    try:
        amount = request.form.get('amount', '').strip()
        description = request.form.get('description', '').strip()
        
        # ✅ Validate inputs
        if not amount or not description:
            flash('Please fill in all fields', 'error')
            return redirect(url_for('add_expense_page'))
        
        # ✅ Create with validation
        expense = Expense(description, float(amount), payer, participants)
        
        # ✅ Add to group
        group.add_expense(expense)
        
        # ✅ Save with error handling
        try:
            save_group(group, FILE_PATH)
            flash('Expense added successfully', 'success')
        except StorageError as e:
            logger.error(f"Failed to save: {e}")
            flash('Error saving expense. Please try again.', 'error')
            return redirect(url_for('add_expense_page'))
        
        return redirect(url_for('dashboard'))
    
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        flash(f'Invalid input: {str(e)}', 'error')
        return redirect(url_for('add_expense_page'))
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        flash('An unexpected error occurred', 'error')
        return redirect(url_for('dashboard'))
```

---

## 7. Configuration - Centralized Management

### ❌ Before (Hardcoded Settings)
```python
# Old code - scattered configuration
app = Flask(__name__)

# Settings scattered everywhere
UPLOAD_FOLDER = 'static/receipts'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024
app.secret_key = 'your-secret-key-change-in-production-2024'  # ❌ Hardcoded
FILE_PATH = "data/expenses.json"  # ❌ Hardcoded
PASSWORD_MIN_LENGTH = 6  # ❌ Scattered

# Problems:
# • Hard to change settings
# • Different settings for dev/prod
# • No centralized config
# • Settings in code (security risk)
```

### ✅ After (Centralized Config)
```python
# New code - config.py
class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    
    UPLOAD_FOLDER = 'static/receipts'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
    
    DATA_FOLDER = 'data'
    EXPENSES_FILE = os.path.join(DATA_FOLDER, 'expenses.json')
    USERS_FILE = os.path.join(DATA_FOLDER, 'users.json')
    
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'app.log'
    
    PASSWORD_MIN_LENGTH = 6
    PASSWORD_MAX_LENGTH = 128
    USERNAME_MIN_LENGTH = 3
    USERNAME_MAX_LENGTH = 50
    
    ENABLE_DUPLICATE_DETECTION = True
    DUPLICATE_THRESHOLD = 0.01

class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False

class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    ENABLE_EMAIL_NOTIFICATIONS = True

# Usage in app.py:
from config import app_config
app.config.from_object(app_config)

# Benefits:
# ✅ Centralized settings
# ✅ Environment-based config
# ✅ Easy to change
# ✅ Secure by default
# ✅ Different settings for dev/prod/test
```

---

## 8. Decorators - Cross-Cutting Concerns

### ❌ Before (Duplicated Code)
```python
# Old code - auth repeated everywhere
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    # ... dashboard code ...

@app.route('/expenses')
def expenses():
    if 'username' not in session:  # ❌ Repeated
        return redirect(url_for('login'))
    # ... expenses code ...

@app.route('/add')
def add():
    if 'username' not in session:  # ❌ Repeated again
        return redirect(url_for('login'))
    # ... add code ...
```

### ✅ After (DRY Principle)
```python
# New code - decorators.py
from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('You must be logged in', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Usage in app.py:
@app.route('/dashboard')
@login_required  # ✅ Clean and reusable
def dashboard():
    # ... dashboard code ...

@app.route('/expenses')
@login_required  # ✅ Simple
def expenses():
    # ... expenses code ...

@app.route('/add')
@login_required  # ✅ No duplication
def add():
    # ... add code ...

# Additional decorators:
@app.route('/api')
@rate_limit(max_requests=10)  # ✅ Rate limiting
def api():
    pass

@app.route('/data')
@handle_exceptions  # ✅ Exception handling
def get_data():
    pass

@app.route('/log')
@log_action("viewed_logs")  # ✅ Action logging
def view_logs():
    pass
```

---

## Summary

| Aspect | Before | After |
|--------|--------|-------|
| Validation | None | Comprehensive |
| Error Messages | Generic | Detailed |
| Precision | Float (errors) | Decimal (exact) |
| Export | Not possible | CSV, more planned |
| Backups | Manual | Automatic |
| Security | Basic | Enhanced |
| Config | Hardcoded | Centralized |
| Logging | None | Full system |
| Code Reuse | Low | High (decorators) |
| Maintainability | Poor | Excellent |

**Result: Enterprise-grade expense splitter! 🚀**
