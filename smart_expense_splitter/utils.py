# utils.py - Utility functions for the expense splitter
import os
import csv
import logging
from datetime import datetime
from decimal import Decimal
from io import StringIO, BytesIO
from hashlib import md5

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Custom validation error"""
    pass

def sanitize_filename(filename):
    """Sanitize filename to prevent security issues"""
    if not filename:
        raise ValidationError("Filename cannot be empty")
    
    # Remove path separators and special characters
    filename = os.path.basename(filename)
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    return filename.strip()

def export_expenses_to_csv(group):
    """Export expenses to CSV format"""
    try:
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Date', 'Description', 'Amount', 'Payer', 'Participants',
            'Category', 'Notes', 'Status'
        ])
        
        # Write expense data
        for expense in group.expenses:
            participants = ', '.join(p.name for p in expense.participants)
            status = 'Paid' if expense.paid else 'Pending'
            
            writer.writerow([
                expense.date,
                expense.description,
                f"${expense.amount:.2f}",
                expense.payer.name,
                participants,
                expense.category,
                expense.notes,
                status
            ])
        
        return output.getvalue()
    
    except Exception as e:
        logger.error(f"Error exporting expenses to CSV: {e}")
        raise ValidationError(f"Failed to export expenses: {e}")

def export_settlements_to_csv(settlements):
    """Export settlement summary to CSV"""
    try:
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['From', 'To', 'Amount'])
        
        # Write settlement data
        for settlement in settlements:
            writer.writerow([
                settlement['from'],
                settlement['to'],
                f"${settlement['amount']:.2f}"
            ])
        
        return output.getvalue()
    
    except Exception as e:
        logger.error(f"Error exporting settlements to CSV: {e}")
        raise ValidationError(f"Failed to export settlements: {e}")

def format_currency(amount):
    """Format amount as currency"""
    try:
        decimal_amount = Decimal(str(amount))
        return f"${decimal_amount:.2f}"
    except (ValueError, TypeError):
        return "$0.00"

def calculate_expense_summary(group):
    """Calculate summary statistics for expenses"""
    try:
        if not group.expenses:
            return {
                'total_expenses': 0,
                'total_amount': Decimal('0.00'),
                'average_expense': Decimal('0.00'),
                'highest_expense': Decimal('0.00'),
                'lowest_expense': Decimal('0.00'),
                'expense_count': 0
            }
        
        amounts = [Decimal(str(e.amount)) for e in group.expenses]
        total_amount = sum(amounts)
        
        return {
            'total_expenses': len(group.expenses),
            'total_amount': total_amount,
            'average_expense': total_amount / len(group.expenses),
            'highest_expense': max(amounts),
            'lowest_expense': min(amounts),
            'expense_count': len(group.expenses)
        }
    
    except Exception as e:
        logger.error(f"Error calculating summary: {e}")
        return {}

def get_expense_by_category(group):
    """Group expenses by category"""
    categories = {}
    
    for expense in group.expenses:
        category = expense.category or 'Other'
        if category not in categories:
            categories[category] = {'count': 0, 'total': Decimal('0.00')}
        
        categories[category]['count'] += 1
        categories[category]['total'] += Decimal(str(expense.amount))
    
    return categories

def get_user_spending(group, user_id):
    """Get total spending for a specific user"""
    total = Decimal('0.00')
    
    for expense in group.expenses:
        if expense.payer.id == user_id:
            total += Decimal(str(expense.amount))
    
    return total

def get_user_share(group, user_id):
    """Get total share (what user owes) for a specific user"""
    total = Decimal('0.00')
    
    for expense in group.expenses:
        if any(p.id == user_id for p in expense.participants):
            amount = Decimal(str(expense.amount))
            share = amount / len(expense.participants)
            total += share
    
    return total

def is_duplicate_expense(expense1, expense2, threshold=0.01):
    """Check if two expenses are likely duplicates"""
    # Same description and amount within threshold
    if expense1.description.lower() != expense2.description.lower():
        return False
    
    diff = abs(Decimal(str(expense1.amount)) - Decimal(str(expense2.amount)))
    return diff <= Decimal(str(threshold))

def validate_email(email):
    """Basic email validation"""
    if not email or '@' not in email or '.' not in email.split('@')[-1]:
        raise ValidationError("Invalid email format")
    return email.strip().lower()

def generate_expense_hash(expense):
    """Generate a hash for duplicate detection"""
    key = f"{expense.description}{expense.amount}{expense.payer.id}"
    return md5(key.encode()).hexdigest()

def format_date(date_string):
    """Format date string for display"""
    try:
        date_obj = datetime.strptime(date_string, "%Y-%m-%d")
        return date_obj.strftime("%B %d, %Y")
    except (ValueError, TypeError):
        return date_string

def get_date_range_expenses(group, start_date, end_date):
    """Get expenses within a date range"""
    expenses = []
    
    for expense in group.expenses:
        exp_date = expense.date
        if start_date <= exp_date <= end_date:
            expenses.append(expense)
    
    return expenses

def calculate_percentage(part, whole):
    """Calculate percentage safely"""
    if whole == 0:
        return 0
    return round((Decimal(str(part)) / Decimal(str(whole))) * 100, 2)
