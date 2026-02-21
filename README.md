# Smart Expense Splitter

Smart Expense Splitter is a Python-based web application designed to simplify shared expenses among groups. It features an intuitive dashboard, expense tracking, and smart settlement algorithms.

## Features

-   **Dashboard**: Overview of total expenses, user balances, and activity.
-   **Expense Management**: Add, edit, and delete shared expenses.
-   **Smart Settlements**: Automatically calculate who owes whom to minimize transactions.
-   **Group Management**: Create user groups and manage participants.
-   **Reports**: View monthly reports, category breakdowns, and export data (CSV/PDF).
-   **Responsive UI**: Modern interface with dark mode support.

## Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/yourusername/smart-expense-splitter.git
    cd smart-expense-splitter
    ```

2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3.  Run the application:
    ```bash
    python app.py
    ```

4.  Open your browser and navigate to:
    `http://127.0.0.1:5000`

## Deployment

### Deploying to Platforms (Render, Heroku, etc.)
Since this is a Flask application, it requires a backend server. Recommended platforms:
-   **Render**: Create a Web Service, link your repo, and set the Start Command to `gunicorn app:app` (ensure `gunicorn` is in `requirements.txt`).
-   **Heroku**: Similar process using a `Procfile`.

### GitHub Pages (Static Only)
GitHub Pages hosts static content and cannot run Python/Flask code directly. To deploy a static version or documentation:
1.  Go to `Settings` > `Pages`.
2.  Select the branch (e.g., `main` or `gh-pages`) and folder (e.g., `/docs`).

## License

MIT License. See [LICENSE](LICENSE) for details.
