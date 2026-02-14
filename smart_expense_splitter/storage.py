# storage.py
import json
import os
import logging
from models import Group, User, Expense
from datetime import datetime

FILE_PATH = "data/expenses.json"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StorageError(Exception):
    """Custom exception for storage operations"""
    pass

def validate_expense_data(expense_data):
    """Validate expense data before loading"""
    required_fields = ["id", "description", "amount", "payer_id", "participants"]
    for field in required_fields:
        if field not in expense_data:
            raise StorageError(f"Missing required field: {field}")
    
    # Validate amount is positive
    try:
        amount = float(expense_data["amount"])
        if amount <= 0:
            raise StorageError(f"Amount must be positive, got: {amount}")
    except (ValueError, TypeError):
        raise StorageError(f"Invalid amount format: {expense_data['amount']}")
    
    return True

def validate_user_data(user_data):
    """Validate user data before loading"""
    if "id" not in user_data or "name" not in user_data:
        raise StorageError("User must have id and name")
    if not user_data["name"].strip():
        raise StorageError("User name cannot be empty")
    return True

def load_group(file_path):
    """Load group data from JSON file with validation"""
    try:
        if not os.path.exists(file_path):
            logger.info(f"File {file_path} not found, creating new group")
            return Group("My Expense Group")

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not data or not isinstance(data, dict):
            logger.warning("Invalid file format, creating new group")
            return Group("My Expense Group")

        group = Group(data.get("name", "My Expense Group"))

        # Load users with validation
        users_map = {}
        for u in data.get("users", []):
            try:
                validate_user_data(u)
                user = User(u["name"].strip())
                user.id = u["id"]
                users_map[user.id] = user
                group.users.append(user)
            except StorageError as e:
                logger.warning(f"Skipping invalid user: {e}")
                continue

        # Load expenses with validation
        for e in data.get("expenses", []):
            try:
                validate_expense_data(e)
                payer = users_map.get(e["payer_id"])
                if not payer:
                    logger.warning(f"Payer not found for expense {e['id']}, skipping")
                    continue
                
                participants = [users_map[pid] for pid in e["participants"] if pid in users_map]
                if not participants:
                    logger.warning(f"No valid participants for expense {e['id']}, skipping")
                    continue

                expense = Expense(
                    e["description"].strip(),
                    e["amount"],
                    payer,
                    participants,
                    receipt_filename=e.get("receipt_filename"),
                    category=e.get("category", "Other"),
                    notes=e.get("notes", ""),
                    tags=e.get("tags", [])
                )
                expense.id = e["id"]
                expense.date = e.get("date", expense.date)
                expense.paid = e.get("paid", False)
                expense.paid_date = e.get("paid_date")
                group.expenses.append(expense)
            except StorageError as e:
                logger.warning(f"Skipping invalid expense: {e}")
                continue

        logger.info(f"Successfully loaded group with {len(group.users)} users and {len(group.expenses)} expenses")
        return group
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        raise StorageError(f"Invalid JSON file format: {e}")
    except Exception as e:
        logger.error(f"Unexpected error loading group: {e}")
        raise StorageError(f"Failed to load group: {e}")

def save_group(group, FILE_PATH):
    """Save group data to JSON file with backup"""
    try:
        os.makedirs("data", exist_ok=True)

        # Create backup before saving
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
            "users": [
                {"id": u.id, "name": u.name}
                for u in group.users
            ],
            "expenses": [
                {
                    "id": e.id,
                    "description": e.description,
                    "amount": e.amount,
                    "payer_id": e.payer.id,
                    "participants": [p.id for p in e.participants],
                    "date": e.date,
                    "receipt_filename": e.receipt_filename,
                    "category": e.category,
                    "notes": e.notes,
                    "tags": e.tags,
                    "paid": e.paid,
                    "paid_date": e.paid_date
                }
                for e in group.expenses
            ]
        }

        with open(FILE_PATH, "w", encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Group saved successfully to {FILE_PATH}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to save group: {e}")
        raise StorageError(f"Failed to save group: {e}")
