import os
from models import User, Expense, Group
from splitter import split_expense, minimize_transactions
from storage import save_group, load_group
from decimal import Decimal, InvalidOperation
from splitter import calculate_balances, simplify_settlements

FILE_PATH = os.path.join("data", "expenses.json")

try:
    group = load_group(FILE_PATH)
    print("✅ Loaded saved data.")
except Exception as e:
    print("❌ Load failed:", e)
    group = Group("Trip to Goa")
    save_group(group, FILE_PATH)

def normalize_name(name: str) -> str:
    return name.strip().lower()

def user_exists(name: str) -> bool:
    norm = normalize_name(name)
    return any(normalize_name(u.name) == norm for u in group.users)


def get_index(max_value, prompt):
    try:
        idx = int(input(prompt)) - 1
        if 0 <= idx < max_value:
            return idx
        raise ValueError
    except ValueError:
        print("❌ Invalid selection.")
        return None


def get_amount():
    raw = input("Amount: ").strip()
    try:
        amount = Decimal(raw)
        if amount <= 0:
            raise InvalidOperation
        return amount
    except InvalidOperation:
        print("❌ Enter a valid positive amount.")
        return None

def add_user():
    name = input("Enter user name: ").strip()

    if not name:
        print("❌ Name cannot be empty.")
        return

    if user_exists(name):
        print("⚠️ User already exists.")
        return

    group.add_user(User(name))
    save_group(group, FILE_PATH)
    print("✅ User added.")

def edit_user():
    if not group.users:
        print("📭 No users to edit.")
        return

    print("\n--- Users ---")
    for i, u in enumerate(group.users, start=1):
        print(f"{i}. {u.name}")

    idx = get_index(len(group.users), "Select user number to edit: ")
    if idx is None:
        return

    user = group.users[idx]

    new_name = input(f"New name for '{user.name}': ").strip()

    if not new_name:
        print("❌ Name cannot be empty.")
        return

    if user_exists(new_name):
        print("⚠️ A user with this name already exists.")
        return

    old_name = user.name
    user.name = new_name

    save_group(group, FILE_PATH)

    print(f"✏️ User '{old_name}' renamed to '{new_name}'.")

def delete_user():
    if not group.users:
        print("📭 No users to delete.")
        return

    print("\n--- Users ---")
    for i, u in enumerate(group.users, start=1):
        print(f"{i}. {u.name}")

    idx = get_index(len(group.users), "Select user number to delete: ")
    if idx is None:
        return

    user = group.users[idx]

    # Check if user is used in any expense
    used_in_expenses = False
    for e in group.expenses:
        if e.payer_id == user.id or user.id in e.participant_ids:
            used_in_expenses = True
            break

    if used_in_expenses:
        print(
            f"❌ Cannot delete '{user.name}'. "
            "User is linked to existing expenses."
        )
        return

    confirm = input(
        f"Are you sure you want to delete user '{user.name}'? (y/n): "
    ).strip().lower()

    if confirm != "y":
        print("❎ Deletion cancelled.")
        return

    group.users.pop(idx)
    save_group(group, FILE_PATH)

    print(f"🗑️ User '{user.name}' deleted successfully.")




def add_expense():
    desc = input("Description: ").strip()
    amount = get_amount()
    if amount is None:
        return

    payer_name = input("Paid by: ").strip()

    payer = next(
        (
            u for u in group.users
            if normalize_name(u.name) == normalize_name(payer_name)
        ),
        None
    )

    if not payer:
        print("❌ User not found.")
        return

    print("Participants (comma-separated):")
    names = input().split(",")

    normalized_names = [normalize_name(n) for n in names]

    participants = [
        u for u in group.users
        if normalize_name(u.name) in normalized_names
    ]

    if not participants:
        print("❌ No valid participants.")
        return

    category = input("Category (Food/Travel/Hotel/etc): ").strip()
    if not category:
        category = "General"

    expense = Expense(desc, amount, payer, participants, category)

    group.add_expense(expense)
    split_expense(expense, group)
    save_group(group, FILE_PATH)

    print("✅ Expense added successfully.")


def show_balances():
    for u in group.users:
        print(u)

def show_settlements():
    for t in minimize_transactions(group.users):
        print(t)

def show_expenses():
    if not group.expenses:
        print("📭 No expenses found.")
        return

    print("\n--- Expense History ---")
    for i, e in enumerate(group.expenses, start=1):
        payer = group.get_user_by_id(e.payer_id)
        participants = group.get_users_by_ids(e.participant_ids)

        payer_name = payer.name if payer else "Unknown"
        participant_names = ", ".join(
            u.name for u in participants
        ) if participants else "Unknown"

        print(
            f"{i}. {e.description} | "
            f"₹{e.amount:.2f} | "
            f"Paid by {payer_name} | "
            f"Participants: [{participant_names}] | "
            f"{e.date}"
        )

def save_data():
    save_group(group, FILE_PATH)
    print("💾 Data saved successfully.")

def recalculate_balances():
    for u in group.users:
        u.balance = Decimal("0.00")

    for e in group.expenses:
        split_expense(e, group)


def edit_expense():
    if not group.expenses:
        print("📭 No expenses to edit.")
        return

    show_expenses()

    idx = get_index(len(group.expenses), "Enter expense number to edit: ")
    if idx is None:
        return

    expense = group.expenses[idx]

    payer = group.get_user_by_id(expense.payer_id)
    participants = group.get_users_by_ids(expense.participant_ids)

    print("\nPress Enter to keep current value")

    # Description
    new_desc = input(f"Description ({expense.description}): ").strip()
    if new_desc:
        expense.description = new_desc

    # Amount
    new_amount = input(f"Amount ({expense.amount:.2f}): ").strip()
    if new_amount:
        try:
            amt = Decimal(new_amount)
            if amt <= 0:
                raise InvalidOperation
            expense.amount = amt
        except InvalidOperation:
            print("❌ Invalid amount. Keeping old value.")

    # Category
    new_category = input(
        f"Category ({getattr(expense, 'category', 'General')}): "
    ).strip()
    if new_category:
        expense.category = new_category

    # Payer
    new_payer = input(f"Payer ({payer.name}): ").strip()
    if new_payer:
        new_payer_obj = next(
            (
                u for u in group.users
                if normalize_name(u.name) == normalize_name(new_payer)
            ),
            None
        )
        if new_payer_obj:
            expense.payer_id = new_payer_obj.id
        else:
            print("❌ User not found. Payer unchanged.")

    # Participants
    names = input(
        "Participants (comma-separated) or Enter to keep: "
    ).strip()

    if names:
        normalized_names = [normalize_name(n) for n in names.split(",")]

        new_participants = [
            u for u in group.users
            if normalize_name(u.name) in normalized_names
        ]

        if new_participants:
            expense.participant_ids = [u.id for u in new_participants]
        else:
            print("❌ No valid participants. Keeping old list.")

    # Recalculate balances & save
    recalculate_balances()
    save_group(group, FILE_PATH)

    print("✏️ Expense updated successfully.")

  
def delete_expense():
    if not group.expenses:
        print("📭 No expenses to delete.")
        return

    show_expenses()

    idx = get_index(len(group.expenses), "Enter expense number to delete: ")
    if idx is None:
        return

    expense = group.expenses[idx]

    confirm = input(
        f"Are you sure you want to delete '{expense.description}'? (y/n): "
    ).strip().lower()

    if confirm != "y":
        print("❎ Deletion cancelled.")
        return

    group.expenses.pop(idx)
    recalculate_balances()
    save_group(group, FILE_PATH)

    print("🗑️ Expense deleted successfully.")

def analytics_spending_per_user():
    print("\n📊 Total Spending Per User")
    totals = {}

    for e in group.expenses:
        payer = group.get_user_by_id(e.payer_id)
        totals[payer.name] = totals.get(payer.name, Decimal("0.00")) + e.amount

    for name, amt in totals.items():
        print(f"{name}: ₹{amt:.2f}")

def analytics_by_category():
    print("\n📊 Spending By Category")
    categories = {}

    for e in group.expenses:
        category = getattr(e, "category", "General")
        categories[category] = categories.get(
            category, Decimal("0.00")
) + e.amount

    for cat, amt in categories.items():
        print(f"{cat}: ₹{amt:.2f}")

def analytics_who_owes():
    print("\n📊 Net Position")
    for u in group.users:
        status = "gets back" if u.balance > 0 else "owes"
        print(f"{u.name}: {status} ₹{abs(u.balance):.2f}")
        
@app.route("/balances")
def balances():
    calculate_balances(group)
    settlements = simplify_settlements(group)

    return render_template(
        "balances.html",
        users=group.users,
        settlements=settlements
    )

while True:
    print("\n--- Smart Expense Splitter ---")
    print("1. Add User")
    print("2. Add Expense")
    print("3. Show Balances")
    print("4. Show Settlements")
    print("5. View Expense History")
    print("6. Save Data")
    print("7. Exit")
    print("8. Edit Expense")
    print("9. Delete Expense")
    print("10. Analytics")
    print("11. Edit User")
    print("12. Delete User")

    choice = input("Choose an option: ").strip()

    if choice == "1":
        add_user()
    elif choice == "2":
        add_expense()
    elif choice == "3":
        show_balances()
    elif choice == "4":
        show_settlements()
    elif choice == "5":
        show_expenses()
    elif choice == "6":
        save_data()          # ✅ manual save
    elif choice == "7":
        save_group(group, FILE_PATH)
        print("Data saved. Goodbye!")
        break
    elif choice == "8":
        edit_expense()
    elif choice == "9":
        delete_expense()
    elif choice == "10":
        analytics_spending_per_user()
        analytics_by_category()
        analytics_who_owes()
    elif choice == "11":
        edit_user()
    elif choice == "12":
        delete_user()
    else:
        print("Invalid choice.")
