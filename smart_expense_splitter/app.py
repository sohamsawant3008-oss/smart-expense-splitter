from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from functools import wraps
from models import User, Expense, Budget, ExpenseGroup
from storage import load_group, save_group
from models import User, Group
from splitter import calculate_balances, settle_debts
from auth import register_user, verify_user, user_exists
import os
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import csv
import io
from io import BytesIO
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

app = Flask(__name__)
# Configure upload folder
UPLOAD_FOLDER = 'static/receipts'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
# Secret key for session management - in production, use a secure random key
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production-2024')

FILE_PATH = "data/expenses.json"
group = load_group(FILE_PATH)
# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ---------------- HOME ----------------
@app.route("/")
def home_redirect():
    return redirect(url_for("dashboard"))

@app.route("/dashboard")
@login_required
def dashboard():
    search_query = request.args.get('search', '').strip().lower()
    filter_payer = request.args.get('filter_payer', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')

    expenses = group.expenses

    # --- SEARCH ---
    if search_query:
        expenses = [e for e in expenses if search_query in e.description.lower()]

    # --- FILTER BY PAYER ---
    if filter_payer:
        expenses = [e for e in expenses if e.payer.id == filter_payer]

    # --- DATE FILTER ---
    if start_date:
        expenses = [e for e in expenses if e.date >= start_date]
    if end_date:
        expenses = [e for e in expenses if e.date <= end_date]

    # --- STATS (always from ALL expenses) ---
    total_amount = sum(float(e.amount) for e in group.expenses)
    expense_count = len(group.expenses)
    user_count = len(group.users)
    avg_expense = total_amount / expense_count if expense_count else 0

    # --- TOP SPENDER ---
    spent_map = {}
    for e in group.expenses:
        spent_map[e.payer.name] = spent_map.get(e.payer.name, 0) + float(e.amount)

    if spent_map:
        top_spender = max(spent_map, key=spent_map.get)
        top_amount = spent_map[top_spender]
    else:
        top_spender = "N/A"
        top_amount = 0


    return render_template(
        "index.html",
        group=group,
        expenses=expenses,   # ✅ IMPORTANT
        total_amount=round(total_amount, 2),
        avg_expense=round(avg_expense, 2),
        user_count=user_count,
        expense_count=expense_count,
        top_spender=top_spender,
        top_amount=round(top_amount, 2),
        username=session.get('username')
    )

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    # If already logged in, redirect to home
    if 'username' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        
        if not username:
            return render_template("login.html", error="Please enter a username")
        
        if not password:
            return render_template("login.html", error="Please enter a password")
        
        # Verify credentials
        success, message = verify_user(username, password)
        
        if success:
            session['username'] = username
            flash("Login successful! Welcome back.", "success")
            return redirect(url_for('dashboard'))
        else:
            return render_template("login.html", error=message)
    
    return render_template("login.html")

# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    # If already logged in, redirect to home
    if 'username' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        
        # Validation
        if not username or len(username) < 3:
            return render_template("register.html", error="Username must be at least 3 characters long")
        
        if not password or len(password) < 4:
            return render_template("register.html", error="Password must be at least 4 characters long")
        
        if password != confirm_password:
            return render_template("register.html", error="Passwords do not match")
        
        # Register user
        success, message = register_user(username, password)
        
        if success:
            flash("Registration successful! Please login.", "success")
            return redirect(url_for('login'))
        else:
            return render_template("register.html", error=message)
    
    return render_template("register.html")

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.pop('username', None)
    flash("You have been logged out successfully.", "info")
    return redirect(url_for('login'))


# ---------------- ADD USER ----------------
@app.route("/add-user", methods=["POST"])
@login_required
def add_user():
    name = request.form["name"].strip()
    if not name:
        return redirect(url_for("dashboard"))

    user = User(name)
    group.users.append(user)
    save_group(group, FILE_PATH)
    return redirect(url_for("dashboard"))

# ---------------- ADD EXPENSE ----------------
@app.route("/add-expense", methods=["GET", "POST"])
@login_required
def add_expense():
    if request.method == "POST":
        desc = request.form.get("description")
        amount = request.form.get("amount")
        payer_id = request.form.get("payer")
        participant_ids = request.form.getlist("participants")

        payer = group.get_user_by_id(payer_id)
        if not payer:
            return redirect(url_for("dashboard"))

        participants = [
            group.get_user_by_id(pid)
            for pid in participant_ids
            if group.get_user_by_id(pid)
        ]

        # Handle receipt upload
        receipt_filename = None
        if 'receipt' in request.files:
            file = request.files['receipt']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(f"{Expense.__init__.__code__.co_names[0]}_{file.filename}")
                # Use expense ID-based naming
                import uuid
                receipt_filename = f"receipt_{uuid.uuid4()}_{secure_filename(file.filename)}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], receipt_filename))

        # Get category and notes
        category = request.form.get("category", "Other")
        notes = request.form.get("notes", "")
        tags = [t.strip() for t in request.form.get("tags", "").split(",") if t.strip()]

        expense = Expense(desc, amount, payer, participants, receipt_filename, category, notes, tags)
        group.expenses.append(expense)

        save_group(group, FILE_PATH)
        flash("Expense added successfully!", "success")
        return redirect("/")

    return render_template("add_expense.html", group=group)

# ---------------- DELETE USER ----------------
@app.route("/delete-user/<user_id>", methods=["POST"])
@login_required
def delete_user(user_id):
    user = group.get_user_by_id(user_id)

    if not user:
        return redirect(url_for("dashboard"))

    # 🚫 Prevent delete if user is used in any expense
    for e in group.expenses:
        if e.payer.id == user_id or user in e.participants:
            return "❌ Cannot delete user. User is used in expenses."

    group.users = [u for u in group.users if u.id != user_id]
    save_group(group, FILE_PATH)
    return redirect(url_for("dashboard"))

# ---------------- DELETE EXPENSE ----------------
@app.route("/delete-expense/<expense_id>", methods=["POST"])
@login_required
def delete_expense(expense_id):
    group.expenses = [e for e in group.expenses if e.id != expense_id]
    save_group(group, FILE_PATH)
    return redirect(url_for("dashboard"))

# ---------------- EDIT USER  AND EDIT EXPENSE ----------------
@app.route("/edit-user/<user_id>", methods=["GET", "POST"])
@login_required
def edit_user(user_id):
    user = group.get_user_by_id(user_id)

    if not user:
        flash("❌ User not found", "danger")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        new_name = request.form.get("name", "").strip()

        # ❌ Validation
        if not new_name:
            flash("⚠️ User name cannot be empty", "warning")
            return render_template("edit_user.html", user=user)

        if len(new_name) < 2:
            flash("⚠️ User name must be at least 2 characters", "warning")
            return render_template("edit_user.html", user=user)

        # ❌ Duplicate name check
        for u in group.users:
            if u.id != user.id and u.name.lower() == new_name.lower():
                flash("⚠️ A user with this name already exists", "warning")
                return render_template("edit_user.html", user=user)

        # ✅ Update
        user.name = new_name
        save_group(group, FILE_PATH)

        flash("✅ User updated successfully", "success")
        return redirect(url_for("dashboard"))

    return render_template("edit_user.html", user=user)


@app.route("/edit-expense/<expense_id>", methods=["GET", "POST"])
@login_required
def edit_expense(expense_id):
    expense = next((e for e in group.expenses if e.id == expense_id), None)

    if not expense:
        flash("❌ Expense not found", "danger")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        description = request.form.get("description", "").strip()
        amount = request.form.get("amount", "").strip()

        # ❌ Validation
        if not description:
            flash("⚠️ Description cannot be empty", "warning")
            return render_template("edit_expense.html", expense=expense)

        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError
        except ValueError:
            flash("⚠️ Amount must be a positive number", "warning")
            return render_template("edit_expense.html", expense=expense)

        # ✅ Update
        expense.description = description
        expense.amount = amount
        save_group(group, FILE_PATH)

        flash("✅ Expense updated successfully", "success")
        return redirect(url_for("dashboard"))

    return render_template("edit_expense.html", expense=expense)


# ---------------- TOGGLE PAYMENT STATUS ----------------
@app.route("/toggle-payment/<expense_id>", methods=["POST"])
@login_required
def toggle_payment(expense_id):
    expense = next((e for e in group.expenses if e.id == expense_id), None)
    if expense:
        expense.paid = not expense.paid
        if expense.paid:
            expense.paid_date = datetime.now().strftime("%Y-%m-%d %H:%M")
            flash(f"✅ Expense '{expense.description}' marked as PAID", "success")
        else:
            expense.paid_date = None
            flash(f"⏳ Expense '{expense.description}' marked as UNPAID", "info")
        save_group(group, FILE_PATH)
    return redirect(url_for("dashboard"))

# ---------------- ANALYTICS ----------------
@app.route("/analytics")
@login_required
def analytics():
    # Data source: group.expenses (dynamic data from storage)
    
    # 1. Total paid per user (amount)
    totals = {}
    # 2. Expense count per user
    expense_counts = {}
    # 3. Expenses over time (by date)
    expenses_by_date = {}
    # 4. All expense amounts for distribution analysis
    all_amounts = []
    
    for e in group.expenses:
        payer_name = e.payer.name
        
        # Total amount paid per user
        totals[payer_name] = totals.get(payer_name, 0) + float(e.amount)
        
        # Count of expenses per user
        expense_counts[payer_name] = expense_counts.get(payer_name, 0) + 1
        
        # Expenses by date
        date = getattr(e, 'date', None)
        if date:
            expenses_by_date[date] = expenses_by_date.get(date, 0) + float(e.amount)
        
        # Collect all amounts
        all_amounts.append(float(e.amount))
    
    # Sort dates chronologically
    sorted_dates = sorted(expenses_by_date.keys())
    date_labels = sorted_dates
    date_values = [expenses_by_date[d] for d in sorted_dates]
    
    # Calculate statistics
    total_expenses = sum(totals.values())
    avg_expense = total_expenses / len(group.expenses) if group.expenses else 0
    
    labels = list(totals.keys())
    values = list(totals.values())
    count_values = [expense_counts.get(name, 0) for name in labels]

    return render_template(
        "analytics.html",
        labels=labels,
        values=values,
        count_values=count_values,
        date_labels=date_labels,
        date_values=date_values,
        total_expenses=total_expenses,
        avg_expense=avg_expense,
        expense_count=len(group.expenses)
    )

@app.route("/settlements")
@login_required
def settlements():
    try:
        balances = calculate_balances(group)

        users_map = {u.id: u for u in group.users}
        settlements_list = settle_debts(balances, users_map)

        return render_template(
            "settlements.html",
            settlements=settlements_list
        )
    except Exception as e:
        # Handle any errors gracefully
        return f"Error calculating settlements: {str(e)}", 500



# ============ SETTLEMENT ROUTES ============

@app.route("/settle-full/<from_id>/<to_id>/<amount>", methods=["POST"])
@login_required
def settle_full(from_id, to_id, amount):
    """Settle the full debt amount"""
    try:
        payer = group.get_user_by_id(from_id)
        # In settlement context: 'recipient' of payment is the one who was owed money
        # But for Expense object: Payer is the one paying (debtor), Participant is the one receiving (creditor)
        recipient = group.get_user_by_id(to_id)
        
        if not payer or not recipient:
            flash("❌ User not found", "danger")
            return redirect("/settlements")

        # Create a settlement expense
        expense = Expense(
            description=f"Settlement to {recipient.name}",
            amount=amount,
            payer=payer,
            participants=[recipient],
            receipt_filename=None,
            category="Settlement",
            tags=None
        )
        expense.paid = True
        expense.notes = "Full settlement"
        expense.paid_date = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        group.expenses.append(expense)
        save_group(group, FILE_PATH)
        
        flash(f"✅ Full settlement recorded: {payer.name} paid {recipient.name} ₹{amount}", "success")
        
    except Exception as e:
        flash(f"❌ Error recording settlement: {e}", "danger")
        
    return redirect("/settlements")

@app.route("/settle-partial/<from_id>/<to_id>/<amount>", methods=["GET", "POST"])
@login_required
def settle_partial(from_id, to_id, amount):
    """Settle a partial debt amount"""
    payer = group.get_user_by_id(from_id)
    recipient = group.get_user_by_id(to_id)
    
    if not payer or not recipient:
        flash("❌ User not found", "danger")
        return redirect("/settlements")

    if request.method == "POST":
        pay_amount = request.form.get("amount")
        try:
            pay_amount = float(pay_amount)
            if pay_amount <= 0:
                raise ValueError
        except ValueError:
            flash("⚠️ Invalid amount", "warning")
            return render_template("settle_partial.html", from_user=payer, to_user=recipient, amount=amount)

        # Create partial settlement expense
        expense = Expense(
            description=f"Partial Settlement to {recipient.name}",
            amount=pay_amount,
            payer=payer,
            participants=[recipient],
            receipt_filename=None,
            category="Settlement",
            tags=None
        )
        expense.paid = True
        expense.notes = "Partial settlement"
        expense.paid_date = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        group.expenses.append(expense)
        save_group(group, FILE_PATH)
        
        flash(f"✅ Partial settlement recorded: {payer.name} paid {recipient.name} ₹{pay_amount}", "success")
        return redirect("/settlements")

    return render_template("settle_partial.html", from_user=payer, to_user=recipient, amount=amount)


# ============ EXPORT ROUTES ============

@app.route("/export-csv")
@login_required
def export_csv():
    """Export expenses as CSV"""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Description', 'Amount', 'Payer', 'Date', 'Category', 'Status'])
    
    for e in group.expenses:
        writer.writerow([
            e.description,
            e.amount,
            e.payer.name,
            e.date,
            getattr(e, 'category', 'N/A'),
            'PAID' if e.paid else 'UNPAID'
        ])
    
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'expenses_{datetime.now().strftime("%Y%m%d")}.csv'
    )

@app.route("/export-pdf")
@login_required
def export_pdf():
    """Export expenses as PDF"""
    if not HAS_REPORTLAB:
        flash("PDF export requires reportlab. Install with: pip install reportlab", "warning")
        return redirect("/")
    
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    # Title
    styles = getSampleStyleSheet()
    title = Paragraph("<b>Smart Expense Splitter Report</b>", styles['Heading1'])
    elements.append(title)
    elements.append(Spacer(1, 0.5*inch))

    # Data table
    data = [['Description', 'Amount', 'Payer', 'Date', 'Category', 'Status']]
    for e in group.expenses:
        data.append([
            e.description[:20],
            f"₹{e.amount:.2f}",
            e.payer.name,
            e.date,
            getattr(e, 'category', 'N/A'),
            'PAID' if e.paid else 'UNPAID'
        ])
    
    table = Table(data, colWidths=[1.2*inch, 1*inch, 1*inch, 1*inch, 1*inch, 1*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    
    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'expenses_{datetime.now().strftime("%Y%m%d")}.pdf'
    )

# ============ BUDGET ROUTES ============

@app.route("/set-budget/<user_id>", methods=["GET", "POST"])
@login_required
def set_budget(user_id):
    """Set budget for a user"""
    user = group.get_user_by_id(user_id)
    if not user:
        flash("User not found!", "danger")
        return redirect("/")
    
    if request.method == "POST":
        amount = request.form.get("amount")
        period = request.form.get("period", "monthly")
        
        # Remove existing budget for this user
        group.budgets = [b for b in group.budgets if b.user_id != user_id]
        
        # Add new budget
        budget = Budget(user_id, amount, period)
        group.add_budget(budget)
        save_group(group, FILE_PATH)
        
        flash(f"✅ Budget set for {user.name}: ₹{amount}/{period}", "success")
        return redirect("/")
    
    return render_template("set_budget.html", user=user, group=group)

@app.route("/view-budgets")
@login_required
def view_budgets():
    """View budget vs actual spending"""
    budget_data = []
    
    for budget in group.budgets:
        user = group.get_user_by_id(budget.user_id)
        if user:
            # Calculate spending for the period
            if budget.period == "monthly":
                current_month = datetime.now().strftime("%Y-%m")
                spent = sum(float(e.amount) for e in group.expenses 
                           if e.payer.id == budget.user_id and e.date.startswith(current_month))
            else:
                current_year = datetime.now().strftime("%Y")
                spent = sum(float(e.amount) for e in group.expenses 
                           if e.payer.id == budget.user_id and e.date.startswith(current_year))
            
            budget_data.append({
                'user': user.name,
                'budget': budget.amount,
                'spent': spent,
                'remaining': budget.amount - spent,
                'percentage': round((spent / budget.amount * 100) if budget.amount > 0 else 0, 1)
            })
    
    return render_template("view_budgets.html", budget_data=budget_data)

# ============ CATEGORIES ROUTES ============

@app.route("/categories")
@login_required
def categories():
    """View and manage categories"""
    categories_list = set(getattr(e, 'category', 'Other') for e in group.expenses)
    
    # Calculate spending by category
    category_spending = {}
    for e in group.expenses:
        cat = getattr(e, 'category', 'Other')
        category_spending[cat] = category_spending.get(cat, 0) + float(e.amount)
    
    return render_template("categories.html", categories=categories_list, spending=category_spending)

# ============ MONTHLY REPORTS ============

@app.route("/monthly-report")
@login_required
def monthly_report():
    """View monthly expense reports"""
    monthly_data = {}
    
    for e in group.expenses:
        month = e.date[:7]  # YYYY-MM
        if month not in monthly_data:
            monthly_data[month] = {'total': 0, 'count': 0, 'expenses': []}
        
        monthly_data[month]['total'] += float(e.amount)
        monthly_data[month]['count'] += 1
        monthly_data[month]['expenses'].append(e)
    
    # Sort by month
    monthly_data = dict(sorted(monthly_data.items(), reverse=True))
    
    return render_template("monthly_report.html", monthly_data=monthly_data)

# ============ TRIP/EVENT GROUPS ============

@app.route("/create-group", methods=["GET", "POST"])
@login_required
def create_group_route():
    """Create a new trip/event group"""
    if request.method == "POST":
        name = request.form.get("name")
        description = request.form.get("description", "")
        
        new_group = ExpenseGroup(None, name, description)
        group.add_group(new_group)
        save_group(group, FILE_PATH)
        
        flash(f"✅ Group '{name}' created!", "success")
        return redirect("/")
    
    return render_template("create_group.html")

@app.route("/switch-group/<group_id>")
@login_required
def switch_group(group_id):
    """Switch to a different trip/event group"""
    target_group = group.get_group_by_id(group_id)
    if target_group:
        group.active_group = group_id
        save_group(group, FILE_PATH)
        flash(f"✅ Switched to group: {target_group.name}", "success")
    return redirect("/")

@app.route("/view-groups")
@login_required
def view_groups():
    """View all trip/event groups"""
    return render_template("view_groups.html", groups=group.groups, active_group=group.active_group)

# ============ RECURRING EXPENSES ============

@app.route("/recurring-expenses")
@login_required
def recurring_expenses():
    """View and manage recurring expenses"""
    recurring = [e for e in group.expenses if getattr(e, 'is_recurring', False)]
    return render_template("recurring_expenses.html", expenses=recurring)

@app.route("/add-recurring/<expense_id>", methods=["POST"])
@login_required
def add_recurring(expense_id):
    """Mark expense as recurring"""
    expense = next((e for e in group.expenses if e.id == expense_id), None)
    if expense:
        expense.is_recurring = True
        expense.recurrence_type = request.form.get("recurrence_type", "monthly")
        save_group(group, FILE_PATH)
        flash(f"✅ Expense marked as {expense.recurrence_type} recurring", "success")
    
    return redirect("/recurring-expenses")

# ============ ADVANCED ANALYTICS ============

@app.route("/advanced-analytics")
@login_required
def advanced_analytics():
    """Advanced analytics dashboard"""
    # Category distribution
    category_data = {}
    for e in group.expenses:
        cat = getattr(e, 'category', 'Other')
        category_data[cat] = category_data.get(cat, 0) + float(e.amount)
    
    # Monthly trends
    monthly_data = {}
    for e in group.expenses:
        month = e.date[:7]
        monthly_data[month] = monthly_data.get(month, 0) + float(e.amount)
    
    # Top expenses
    top_expenses = sorted(group.expenses, key=lambda x: float(x.amount), reverse=True)[:5]
    
    # Paid vs unpaid
    paid_total = sum(float(e.amount) for e in group.expenses if e.paid)
    unpaid_total = sum(float(e.amount) for e in group.expenses if not e.paid)
    
    return render_template(
        "advanced_analytics.html",
        category_data=category_data,
        monthly_data=monthly_data,
        top_expenses=top_expenses,
        paid_total=paid_total,
        unpaid_total=unpaid_total
    )

print("REGISTERED ROUTES:")
for rule in app.url_map.iter_rules():
    print(rule)

# ✅ THIS MUST BE LAST
if __name__ == "__main__":
    app.run(debug=True)
