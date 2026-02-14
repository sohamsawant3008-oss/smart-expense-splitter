# Quick Reference Guide - Improved Functions

## 📚 Utility Functions (utils.py)

### Export Functions
```python
from utils import export_expenses_to_csv, export_settlements_to_csv

# Export expenses to CSV
csv_data = export_expenses_to_csv(group)

# Export settlements to CSV
csv_data = export_settlements_to_csv(settlements)
```

### Analysis Functions
```python
from utils import (
    calculate_expense_summary,
    get_expense_by_category,
    get_user_spending,
    get_user_share,
    calculate_percentage
)

# Get expense statistics
summary = calculate_expense_summary(group)
# Returns: total_expenses, total_amount, average_expense, highest_expense, lowest_expense

# Group expenses by category
categories = get_expense_by_category(group)
# Returns: dict with category -> {count, total}

# Get user's total spending
spending = get_user_spending(group, user_id)

# Get user's total share (what they owe)
share = get_user_share(group, user_id)

# Calculate percentage
percentage = calculate_percentage(part, whole)
```

### Duplicate Detection
```python
from utils import is_duplicate_expense, generate_expense_hash

# Check if expenses are duplicates
if is_duplicate_expense(exp1, exp2, threshold=0.01):
    print("Possible duplicate")

# Generate hash for deduplication
hash_val = generate_expense_hash(expense)
```

### Formatting Functions
```python
from utils import format_currency, format_date

# Format currency
currency_str = format_currency(99.5)  # Returns: "$99.50"

# Format date
formatted = format_date("2024-01-28")  # Returns: "January 28, 2024"
```

### Validation Functions
```python
from utils import validate_email, sanitize_filename

# Validate email
try:
    email = validate_email("user@example.com")
except ValidationError as e:
    print(f"Invalid: {e}")

# Sanitize filename
clean_name = sanitize_filename("file<>name.txt")
```

### Date Functions
```python
from utils import get_date_range_expenses

# Get expenses in date range
expenses = get_date_range_expenses(group, "2024-01-01", "2024-01-31")
```

---

## 🔒 Authentication (auth.py)

### User Registration
```python
from auth import register_user

success, msg = register_user("username", "password")
if success:
    print("User registered")
else:
    print(f"Error: {msg}")
```

### User Verification
```python
from auth import verify_user

is_valid, msg = verify_user("username", "password")
if is_valid:
    print("Login successful")
else:
    print(f"Error: {msg}")
```

### Password Change
```python
from auth import change_password

success, msg = change_password("username", "old_pass", "new_pass")
if success:
    print("Password changed")
else:
    print(f"Error: {msg}")
```

### Account Management
```python
from auth import user_exists, deactivate_user

# Check if user exists
if user_exists("username"):
    print("User found")

# Deactivate user
success, msg = deactivate_user("username")
```

---

## 💰 Financial Calculations (splitter.py)

### Calculate Balances
```python
from splitter import calculate_balances
from decimal import Decimal

# Get exact balances (uses Decimal, not float!)
balances = calculate_balances(group)

for user_id, amount in balances.items():
    print(f"Balance: ${amount}")  # Exact to 2 decimal places
```

### Settle Debts
```python
from splitter import settle_debts

# Create settlement plan
settlements = settle_debts(balances, users_list)

for settlement in settlements:
    print(f"{settlement['from']} pays ${settlement['amount']} to {settlement['to']}")
```

### User Balance
```python
from splitter import get_user_balance

balance = get_user_balance(group, user_id)
print(f"Balance: ${balance}")
```

### Settlement Grouping
```python
from splitter import group_settlements_by_pair

# Combine settlements between same pair
simplified = group_settlements_by_pair(settlements)
```

---

## 📊 Data Storage (storage.py)

### Load Data
```python
from storage import load_group

# Load with automatic validation
group = load_group("data/expenses.json")
# Invalid data is skipped with warnings
```

### Save Data
```python
from storage import save_group

# Save with automatic backup
try:
    save_group(group, "data/expenses.json")
except StorageError as e:
    print(f"Save failed: {e}")
```

---

## 📋 Data Models (models.py)

### Create User
```python
from models import User

try:
    user = User("Alice")
    # User validated automatically
except ValueError as e:
    print(f"Error: {e}")
```

### Create Expense
```python
from models import Expense

try:
    expense = Expense(
        description="Dinner",
        amount=50.00,
        payer=user1,
        participants=[user1, user2],
        category="Food",
        notes="Restaurant"
    )
except ValueError as e:
    print(f"Error: {e}")
```

### Create Budget
```python
from models import Budget

try:
    budget = Budget(user_id, amount=500, period="monthly")
except ValueError as e:
    print(f"Error: {e}")
```

### Group Methods
```python
from models import Group

group = Group("My Group")

# Add user (validated)
group.add_user(user)

# Add expense (validated)
group.add_expense(expense)

# Get total expenses
total = group.get_total_expenses()

# Find expense by ID
expense = group.get_expense_by_id(expense_id)

# Remove expense
group.remove_expense(expense_id)

# Remove user
group.remove_user(user_id)
```

---

## ⚙️ Configuration (config.py)

### Use Config
```python
from config import app_config

# In your Flask app
app.config.from_object(app_config)

# Now use configured values
upload_folder = app.config['UPLOAD_FOLDER']
max_size = app.config['MAX_CONTENT_LENGTH']
```

### Available Config
```python
# Security
app.config['SECRET_KEY']
app.config['SESSION_COOKIE_SECURE']
app.config['SESSION_COOKIE_HTTPONLY']

# Upload
app.config['UPLOAD_FOLDER']
app.config['MAX_CONTENT_LENGTH']
app.config['ALLOWED_EXTENSIONS']

# Data
app.config['EXPENSES_FILE']
app.config['USERS_FILE']

# Features
app.config['ENABLE_DUPLICATE_DETECTION']
app.config['DUPLICATE_THRESHOLD']
```

---

## 🎯 Decorators (decorators.py)

### Login Required
```python
from decorators import login_required

@app.route('/dashboard')
@login_required
def dashboard():
    # Only accessible to logged-in users
    pass
```

### Rate Limiting
```python
from decorators import rate_limit

@app.route('/api/data')
@rate_limit(max_requests=10, time_window=3600)
def get_data():
    # Max 10 requests per hour per IP
    pass
```

### Exception Handling
```python
from decorators import handle_exceptions

@app.route('/add')
@handle_exceptions
def add_expense():
    # Exceptions automatically caught and logged
    pass
```

### Action Logging
```python
from decorators import log_action

@app.route('/add')
@log_action("add_expense")
def add_expense():
    # Action automatically logged
    pass
```

---

## 🚨 Error Handling

### Storage Errors
```python
from storage import StorageError

try:
    save_group(group, filepath)
except StorageError as e:
    print(f"Storage error: {e}")
```

### Auth Errors
```python
from auth import AuthError

try:
    # Auth operations can raise AuthError
    pass
except AuthError as e:
    print(f"Auth error: {e}")
```

### Validation Errors
```python
from utils import ValidationError

try:
    # Validation operations can raise ValidationError
    pass
except ValidationError as e:
    print(f"Validation error: {e}")
```

---

## 💡 Common Patterns

### Add New Expense Safely
```python
from models import Expense
from storage import save_group, StorageError

try:
    expense = Expense("Dinner", 100, payer, participants)
    group.add_expense(expense)
    save_group(group, filepath)
    print("Success!")
except ValueError as e:
    print(f"Invalid expense: {e}")
except StorageError as e:
    print(f"Save failed: {e}")
```

### Export and Analyze
```python
from utils import (
    export_expenses_to_csv,
    calculate_expense_summary,
    get_expense_by_category
)

# Get statistics
summary = calculate_expense_summary(group)
categories = get_expense_by_category(group)

# Export
csv_data = export_expenses_to_csv(group)

# Save export
with open('export.csv', 'w') as f:
    f.write(csv_data)
```

### User Settlement
```python
from splitter import calculate_balances, settle_debts

# Calculate who owes who
balances = calculate_balances(group)
settlements = settle_debts(balances, users_dict)

# Display settlements
for s in settlements:
    print(f"{s['from']} -> {s['to']}: ${s['amount']}")
```

---

## 📌 Important Notes

✅ Always use Decimal for money calculations, not float
✅ Always validate input before creating objects
✅ Always use try-except with StorageError
✅ Always check for errors when saving data
✅ Use format_currency() for display
✅ Use the provided utility functions
✅ Check logs for debugging
✅ Backups are automatic

---

## 🔗 Related Files

- **Full documentation**: `IMPROVEMENTS.md`
- **Summary**: `IMPROVEMENTS_SUMMARY.md`
- **Config options**: `config.py`
- **All utilities**: `utils.py`
