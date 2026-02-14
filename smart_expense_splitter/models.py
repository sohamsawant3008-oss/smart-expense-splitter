import uuid
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

class User:
    def __init__(self, name, user_id=None):
        self.id = user_id if user_id else str(uuid.uuid4())
        self.name = name.strip() if name else ""
        self.balance = Decimal("0.00")
        if not self.name:
            raise ValueError("User name cannot be empty")


class Expense:
    def __init__(self, description, amount, payer, participants, receipt_filename=None, category="Other", notes="", tags=None):
        if not description or not description.strip():
            raise ValueError("Expense description cannot be empty")
        
        try:
            amount_decimal = Decimal(str(amount))
            if amount_decimal <= 0:
                raise ValueError("Amount must be greater than 0")
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid amount: {e}")
        
        if not payer:
            raise ValueError("Payer must be specified")
        
        if not participants or len(participants) == 0:
            raise ValueError("At least one participant is required")
        
        self.id = str(uuid.uuid4())
        self.description = description.strip()
        self.amount = float(amount_decimal)
        self.payer = payer
        self.participants = participants
        self.date = datetime.now().strftime("%Y-%m-%d")
        self.receipt_filename = receipt_filename
        self.paid = False
        self.paid_date = None
        self.category = category if category else "Other"
        self.notes = notes if notes else ""
        self.tags = tags if tags else []
        self.is_recurring = False
        self.recurrence_type = None
        self.custom_splits = {}


class Budget:
    def __init__(self, user_id, amount, period="monthly"):
        try:
            amount_decimal = Decimal(str(amount))
            if amount_decimal <= 0:
                raise ValueError("Budget amount must be greater than 0")
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid budget amount: {e}")
        
        self.id = str(uuid.uuid4())
        self.user_id = user_id
        self.amount = float(amount_decimal)
        self.period = period if period in ["monthly", "yearly"] else "monthly"
        self.created_date = datetime.now().strftime("%Y-%m-%d")


class ExpenseGroup:
    def __init__(self, group_id, name, description=""):
        if not name or not name.strip():
            raise ValueError("Group name cannot be empty")
        
        self.id = group_id if group_id else str(uuid.uuid4())
        self.name = name.strip()
        self.description = description if description else ""
        self.created_date = datetime.now().strftime("%Y-%m-%d")
        self.is_active = True


class Group:
    def __init__(self, name):
        if not name or not name.strip():
            raise ValueError("Group name cannot be empty")
        
        self.name = name.strip()
        self.users = []
        self.expenses = []
        self.budgets = []
        self.groups = []
        self.active_group = None

    def get_user_by_id(self, user_id):
        if not user_id:
            return None
        return next((u for u in self.users if u.id == user_id), None)

    def add_user(self, user):
        if not user or not user.name:
            raise ValueError("Cannot add invalid user")
        if any(u.id == user.id for u in self.users):
            raise ValueError(f"User with id {user.id} already exists")
        self.users.append(user)
        return user

    def add_expense(self, expense):
        if not expense:
            raise ValueError("Cannot add invalid expense")
        self.expenses.append(expense)
        return expense
    
    def add_budget(self, budget):
        if not budget:
            raise ValueError("Cannot add invalid budget")
        self.budgets.append(budget)
        return budget
    
    def get_budget_by_user(self, user_id):
        if not user_id:
            return None
        return next((b for b in self.budgets if b.user_id == user_id), None)
    
    def add_group(self, group):
        if not group:
            raise ValueError("Cannot add invalid group")
        self.groups.append(group)
        return group
    
    def get_group_by_id(self, group_id):
        if not group_id:
            return None
        return next((g for g in self.groups if g.id == group_id), None)
    
    def remove_expense(self, expense_id):
        """Remove an expense by ID"""
        self.expenses = [e for e in self.expenses if e.id != expense_id]
    
    def remove_user(self, user_id):
        """Remove a user by ID"""
        self.users = [u for u in self.users if u.id != user_id]
    
    def get_total_expenses(self):
        """Get total of all expenses"""
        return sum(Decimal(str(e.amount)) for e in self.expenses)
    
    def get_expense_by_id(self, expense_id):
        """Get expense by ID"""
        if not expense_id:
            return None
        return next((e for e in self.expenses if e.id == expense_id), None)





