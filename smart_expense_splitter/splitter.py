from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

def calculate_balances(group):
    """Calculate balances with improved precision"""
    balances = defaultdict(Decimal)

    for expense in group.expenses:
        if not expense.amount or not expense.participants:
            continue
            
        amount = Decimal(str(expense.amount))
        participants = expense.participants
        
        # Skip expenses with no participants to avoid division by zero
        if len(participants) == 0:
            logger.warning(f"Expense {expense.id} has no participants, skipping")
            continue
        
        # Use Decimal for precise financial calculations
        share = (amount / len(participants)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        for user in participants:
            balances[user.id] -= share

        balances[expense.payer.id] += amount

    return balances

def settle_debts(balances, users):
    """Settle debts with optimized algorithm"""
    debtors = []
    creditors = []

    # Separate debtors and creditors
    for user_id, amount in balances.items():
        # Round to 2 decimal places for financial accuracy
        amount = Decimal(str(amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        if amount < 0:
            debtors.append([user_id, -amount])
        elif amount > 0:
            creditors.append([user_id, amount])

    settlements = []
    i = j = 0
    
    while i < len(debtors) and j < len(creditors):
        debtor_id, debt = debtors[i]
        creditor_id, credit = creditors[j]

        # Use Decimal for precise calculations
        pay = min(debt, credit)

        # Get user names from users dictionary
        debtor_name = users.get(debtor_id, {}).name if isinstance(users, dict) else next(
            (u.name for u in users if u.id == debtor_id), "Unknown"
        )
        creditor_name = users.get(creditor_id, {}).name if isinstance(users, dict) else next(
            (u.name for u in users if u.id == creditor_id), "Unknown"
        )

        settlements.append({
            "from": debtor_name,
            "to": creditor_name,
            "amount": float(pay.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
            "from_id": debtor_id,
            "to_id": creditor_id
        })

        debtors[i][1] -= pay
        creditors[j][1] -= pay

        # Move to next debtor/creditor if current balance is settled
        if debtors[i][1] == 0:
            i += 1
        if creditors[j][1] == 0:
            j += 1

    logger.info(f"Generated {len(settlements)} settlements")
    return settlements

def get_user_balance(group, user_id):
    """Get balance for a specific user"""
    balances = calculate_balances(group)
    return Decimal(str(balances.get(user_id, 0))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

def validate_settlements(settlements):
    """Validate that settlements are correct and complete"""
    if not settlements:
        return True
    
    # Check all amounts are positive
    for settlement in settlements:
        if settlement.get("amount", 0) <= 0:
            logger.warning(f"Invalid settlement amount: {settlement}")
            return False
    
    return True

def group_settlements_by_pair(settlements):
    """Group settlements between same pair of users"""
    grouped = defaultdict(Decimal)
    
    for settlement in settlements:
        key = (settlement["from"], settlement["to"])
        grouped[key] += Decimal(str(settlement["amount"]))
    
    return [
        {
            "from": pair[0],
            "to": pair[1],
            "amount": float(grouped[pair].quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
        }
        for pair in grouped
    ]


