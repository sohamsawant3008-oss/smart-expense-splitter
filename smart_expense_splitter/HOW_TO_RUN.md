# How to Run the Flask App in Cursor

## Method 1: Using the Debugger (Recommended)
1. Open `app.py` in Cursor
2. Press `F5` or go to Run > Start Debugging
3. Select "Python: Flask" from the configuration dropdown
4. The app will start on http://localhost:5000

## Method 2: Using Terminal
1. Open the integrated terminal in Cursor (Ctrl + `)
2. Run: `python app.py`
3. Open http://localhost:5000 in your browser

## Method 3: Using Flask CLI
1. Open terminal
2. Run: `flask run` or `python -m flask run`
3. Open http://localhost:5000 in your browser

## Troubleshooting

### If Python interpreter is not selected:
1. Press `Ctrl+Shift+P`
2. Type "Python: Select Interpreter"
3. Choose Python 3.14.2 (or your version)

### If Flask is not installed:
Run: `pip install -r requirements.txt`

### If port 5000 is already in use:
Edit `app.py` line 165 and change to:
```python
app.run(debug=True, port=5001)
```

### Common Issues:
- **Module not found**: Make sure you're in the project root directory
- **Port already in use**: Change the port number in app.py
- **Data file errors**: Ensure `data/expenses.json` exists or can be created
