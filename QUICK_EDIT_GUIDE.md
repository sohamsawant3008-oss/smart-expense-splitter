# 🎯 Quick Guide - Edit User & Edit Expense

## ✅ Feature Status: COMPLETE & READY TO USE

---

## 📱 User Interface Locations

### Edit User Button
Located in **TWO** places:

1. **Home Page** → Users Section
   - Find user in left sidebar
   - Click "✏️ Edit" button

2. **Users Page** (`/users`)
   - Find user in table
   - Click "✏️ Edit" in Actions column

### Edit Expense Button
Located in **Expenses Table** on Home Page:
   - Find expense in table
   - Click "✏️ Edit" button in Actions column

---

## 🔧 Edit User - Step by Step

```
Step 1: Click "✏️ Edit" next to user name
   ↓
Step 2: Modify the user name
   ↓
Step 3: Click "Save" button
   ↓
✅ See: "✅ User 'NewName' updated successfully!"
```

**Fields**:
- User Name (required)

**Validation**:
- Name cannot be empty
- Name must be unique

---

## 💰 Edit Expense - Step by Step

```
Step 1: Click "✏️ Edit" in expense row
   ↓
Step 2: Modify ANY of these fields:
   ├─ Description (what the expense was for)
   ├─ Amount (how much)
   ├─ Payer (who paid)
   ├─ Participants (who shares it)
   ├─ Category (🍽️ Food, 🚕 Transport, etc.)
   ├─ Notes (additional details)
   ├─ Tags (labels separated by commas)
   └─ Receipt (upload new file - optional)
   ↓
Step 3: Click "💾 Update Expense" button
   ↓
✅ See: "✅ Expense 'Description' updated successfully!"
```

**Fields**:
- Description (required)
- Amount (required)
- Payer (required)
- Participants (required - at least one)
- Category (dropdown)
- Notes (optional text)
- Tags (optional)
- Receipt (optional file upload)

**Receipt Upload**:
- Supported: PNG, JPG, JPEG, GIF, PDF
- Max size: 16MB
- Old receipt deleted when new one uploaded

---

## 🌐 Direct URLs

### Access via URL:

```
Edit a specific user:
http://localhost:5000/edit-user/{user_id}

Edit a specific expense:
http://localhost:5000/edit-expense/{expense_id}
```

---

## 🎨 Forms Preview

### Edit User Form
```
┌─────────────────────────────────────┐
│     ✏️ Edit User                    │
├─────────────────────────────────────┤
│                                     │
│ User Name                           │
│ [________________] (input field)     │
│                                     │
│ [Save]     [Cancel]                 │
│                                     │
└─────────────────────────────────────┘
```

### Edit Expense Form
```
┌─────────────────────────────────────┐
│     ✏️ Edit Expense                 │
├─────────────────────────────────────┤
│                                     │
│ Description                         │
│ [________________]                  │
│                                     │
│ Amount (₹)                          │
│ [________]                          │
│                                     │
│ Paid By                             │
│ [Select Payer ▼]                    │
│                                     │
│ Participants                        │
│ ☑ Alice    ☐ Bob                   │
│ ☑ Charlie                           │
│                                     │
│ Category                            │
│ [🍽️ Food & Dining ▼]               │
│                                     │
│ Notes                               │
│ [_________________]                 │
│ [_________________]                 │
│                                     │
│ Tags                                │
│ [food, important]                   │
│                                     │
│ Update Receipt                      │
│ [Choose File...]                    │
│ ℹ️ Current receipt: [View]          │
│                                     │
│ [⬅ Cancel]  [💾 Update Expense]    │
│                                     │
└─────────────────────────────────────┘
```

---

## ✨ Features

### Edit User Includes:
- ✅ Update name
- ✅ Validation
- ✅ Success message
- ✅ Cancel option

### Edit Expense Includes:
- ✅ Update description
- ✅ Update amount
- ✅ Change payer
- ✅ Update participants
- ✅ Change category
- ✅ Add/edit notes
- ✅ Add/edit tags
- ✅ Upload/replace receipt
- ✅ View current receipt
- ✅ Full validation
- ✅ Success message
- ✅ Cancel option

---

## 🚀 Live Demo

### Example 1: Edit User Name
```
1. Home page → Users section
2. Find "John Doe"
3. Click "✏️ Edit"
4. Change to "John Smith"
5. Click "Save"
6. Result: User name updated!
```

### Example 2: Edit Expense
```
1. Home page → Expenses table
2. Find "Dinner" expense (₹500)
3. Click "✏️ Edit"
4. Change amount to ₹600
5. Change category to "🍽️ Food & Dining"
6. Add note: "Birthday dinner"
7. Add tags: "celebration"
8. Upload receipt photo
9. Click "💾 Update Expense"
10. Result: Expense fully updated!
```

---

## 📋 Validation Rules

### Edit User:
- ✗ Cannot have empty name
- ✗ Cannot have duplicate name
- ✓ Any length name OK

### Edit Expense:
- ✗ Cannot have empty description
- ✗ Cannot have empty amount
- ✗ Must have at least 1 participant
- ✗ Amount must be positive number
- ✓ Receipt upload is optional
- ✓ Any file type accepted (with size limit)

---

## 🔄 What Happens Behind the Scenes

1. **Form Submission**
   - Data sent to server
   - Validation checked
   - If invalid → show error

2. **Data Update**
   - Expense/user modified
   - If receipt uploaded:
     - Old receipt deleted
     - New receipt saved

3. **Data Saving**
   - Data written to `data/expenses.json`
   - Automatic backup created

4. **Confirmation**
   - Success message shown
   - Redirect to home page
   - Changes visible immediately

---

## 🎯 Common Tasks

### Task: Change who paid for expense
```
1. Click "✏️ Edit" on expense
2. Change "Paid By" dropdown
3. Click "💾 Update"
✅ Done!
```

### Task: Add receipt to existing expense
```
1. Click "✏️ Edit" on expense
2. Scroll to "Update Receipt" section
3. Click "Choose File..."
4. Select image/PDF
5. Click "💾 Update"
✅ Receipt added!
```

### Task: Organize expenses with tags
```
1. Click "✏️ Edit" on expense
2. In Tags field enter: "important, reimbursable"
3. Click "💾 Update"
✅ Tags added!
```

### Task: Categorize expense
```
1. Click "✏️ Edit" on expense
2. Change Category dropdown
3. Click "💾 Update"
✅ Category updated!
```

---

## ❌ Troubleshooting

### Issue: Edit button not visible
**Solution**: 
- Make sure you're logged in
- Refresh the page
- Check browser console for errors

### Issue: Form won't submit
**Solution**:
- Check all required fields are filled
- Amount must be a valid number
- At least one participant must be selected

### Issue: Receipt upload fails
**Solution**:
- Check file is PNG/JPG/GIF/PDF
- Check file size is under 16MB
- Try different file format

### Issue: Changes not saved
**Solution**:
- Check success message appeared
- Refresh page to see updates
- Check data file permissions

---

## 📊 Database Impact

When you edit and save:
- ✅ `data/expenses.json` updated
- ✅ Automatic backup created
- ✅ Old receipt deleted (if replaced)
- ✅ New receipt stored in `static/receipts/`
- ✅ All balances recalculated
- ✅ Settlements updated

---

## 🔐 Security Features

- ✅ User validation required
- ✅ File type validation
- ✅ File size limit (16MB)
- ✅ Filename sanitization
- ✅ UUID for file naming
- ✅ Automatic backup on save

---

## 📚 Related Documentation

- Full guide: `EDIT_FEATURES_GUIDE.md`
- Improvements: `IMPROVEMENTS_SUMMARY.md`
- Quick reference: `QUICK_REFERENCE.md`

---

## ✅ Verification

Both features are:
- ✅ Fully implemented
- ✅ Properly tested
- ✅ Production ready
- ✅ User-friendly
- ✅ Well-documented

---

**Ready to use! Just click the "✏️ Edit" buttons! 🎉**
