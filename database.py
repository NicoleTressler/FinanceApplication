#Finance Application - Nicole Tressler
# September 2025 - September 2026

"""
database.py
Handles all SQLite persistence for the Expense & Savings Manager:
categories, expenses, budgets, recurring payments, and savings goals.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "expenses.db"

DEFAULT_CATEGORIES = [
    ("Food & Dining", "#E74C3C"),
    ("Transportation", "#3498DB"),
    ("Housing", "#9B59B6"),
    ("Utilities", "#1ABC9C"),
    ("Entertainment", "#F39C12"),
    ("Healthcare", "#2ECC71"),
    ("Shopping", "#E67E22"),
    ("Subscriptions", "#8E44AD"),
    ("Other", "#95A5A6"),
]




class Database:
    def __init__(self, db_path=DB_PATH):
        self.db_path = str(db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
        self._seed_categories()



   
    # Setup
    
    def _create_tables(self):
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                color TEXT DEFAULT '#4C72B0'
            );

            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL NOT NULL,
                category_id INTEGER NOT NULL,
                description TEXT,
                date TEXT NOT NULL,
                source TEXT DEFAULT 'manual',
                FOREIGN KEY (category_id) REFERENCES categories(id)
            );

            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL,
                month TEXT NOT NULL,
                amount REAL NOT NULL,
                UNIQUE(category_id, month),
                FOREIGN KEY (category_id) REFERENCES categories(id)
            );

            CREATE TABLE IF NOT EXISTS recurring_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                amount REAL NOT NULL,
                category_id INTEGER NOT NULL,
                frequency TEXT NOT NULL,           -- daily | weekly | monthly | yearly
                next_due_date TEXT NOT NULL,
                active INTEGER DEFAULT 1,
                FOREIGN KEY (category_id) REFERENCES categories(id)
            );

            CREATE TABLE IF NOT EXISTS savings_goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                target_amount REAL NOT NULL,
                current_amount REAL DEFAULT 0,
                deadline TEXT,
                created_date TEXT NOT NULL
            );
            """
        )
        self.conn.commit()

    def _seed_categories(self):
        cur = self.conn.cursor()
        for name, color in DEFAULT_CATEGORIES:
            cur.execute(
                "INSERT OR IGNORE INTO categories (name, color) VALUES (?, ?)",
                (name, color),
            )
        self.conn.commit()



    
    # Categories
    
    def get_categories(self):
        return self.conn.execute("SELECT * FROM categories ORDER BY name").fetchall()

    def add_category(self, name, color="#4C72B0"):
        self.conn.execute(
            "INSERT OR IGNORE INTO categories (name, color) VALUES (?, ?)",
            (name, color),
        )
        self.conn.commit()




    # Expenses
 
    def add_expense(self, amount, category_id, description, date_str, source="manual"):
        cur = self.conn.execute(
            """INSERT INTO expenses (amount, category_id, description, date, source)
               VALUES (?, ?, ?, ?, ?)""",
            (amount, category_id, description, date_str, source),
        )
        self.conn.commit()
        return cur.lastrowid

    def get_expenses(self, month=None):
        query = """
            SELECT e.*, c.name AS category_name, c.color AS category_color
            FROM expenses e JOIN categories c ON e.category_id = c.id
        """
        params = ()
        if month:
            query += " WHERE strftime('%Y-%m', e.date) = ?"
            params = (month,)
        query += " ORDER BY e.date DESC, e.id DESC"
        return self.conn.execute(query, params).fetchall()

    def delete_expense(self, expense_id):
        self.conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        self.conn.commit()

    def get_spending_by_category(self, month):
        return self.conn.execute(
            """
            SELECT c.name AS name, c.color AS color, SUM(e.amount) AS total
            FROM expenses e JOIN categories c ON e.category_id = c.id
            WHERE strftime('%Y-%m', e.date) = ?
            GROUP BY c.id
            ORDER BY total DESC
            """,
            (month,),
        ).fetchall()

    def get_monthly_totals(self, num_months=6):
        rows = self.conn.execute(
            """
            SELECT strftime('%Y-%m', date) AS month, SUM(amount) AS total
            FROM expenses
            GROUP BY month
            ORDER BY month DESC
            LIMIT ?
            """,
            (num_months,),
        ).fetchall()
        return list(reversed(rows))  # chronological order for charting

    def get_total_for_month(self, month):
        row = self.conn.execute(
            "SELECT SUM(amount) AS total FROM expenses WHERE strftime('%Y-%m', date) = ?",
            (month,),
        ).fetchone()
        return row["total"] or 0.0

    
    
    
    
    # Budgets
    
    def set_budget(self, category_id, month, amount):
        self.conn.execute(
            """
            INSERT INTO budgets (category_id, month, amount) VALUES (?, ?, ?)
            ON CONFLICT(category_id, month) DO UPDATE SET amount = excluded.amount
            """,
            (category_id, month, amount),
        )
        self.conn.commit()

    def get_budgets(self, month):
        return self.conn.execute(
            """
            SELECT b.*, c.name AS category_name, c.color AS category_color
            FROM budgets b JOIN categories c ON b.category_id = c.id
            WHERE b.month = ?
            ORDER BY c.name
            """,
            (month,),
        ).fetchall()

    def delete_budget(self, budget_id):
        self.conn.execute("DELETE FROM budgets WHERE id = ?", (budget_id,))
        self.conn.commit()

    def get_budget_status(self, month):
        """Returns a list of dicts describing spend vs. budget per category."""
        budgets = self.get_budgets(month)
        spending = {row["name"]: row["total"] for row in self.get_spending_by_category(month)}
        result = []
        for b in budgets:
            spent = spending.get(b["category_name"], 0.0)
            pct = (spent / b["amount"] * 100) if b["amount"] > 0 else 0
            result.append(
                {
                    "budget_id": b["id"],
                    "category": b["category_name"],
                    "color": b["category_color"],
                    "budget": b["amount"],
                    "spent": spent,
                    "remaining": b["amount"] - spent,
                    "pct": pct,
                }
            )
        return result




  
    # Recurring payments
    
    def add_recurring(self, name, amount, category_id, frequency, next_due_date):
        cur = self.conn.execute(
            """
            INSERT INTO recurring_payments (name, amount, category_id, frequency, next_due_date)
            VALUES (?, ?, ?, ?, ?)
            """,
            (name, amount, category_id, frequency, next_due_date),
        )
        self.conn.commit()
        return cur.lastrowid

    def get_recurring(self, active_only=False):
        q = """
            SELECT r.*, c.name AS category_name, c.color AS category_color
            FROM recurring_payments r JOIN categories c ON r.category_id = c.id
        """
        if active_only:
            q += " WHERE r.active = 1"
        q += " ORDER BY r.next_due_date"
        return self.conn.execute(q).fetchall()

    def toggle_recurring(self, recurring_id, active):
        self.conn.execute(
            "UPDATE recurring_payments SET active = ? WHERE id = ?",
            (int(active), recurring_id),
        )
        self.conn.commit()

    def delete_recurring(self, recurring_id):
        self.conn.execute("DELETE FROM recurring_payments WHERE id = ?", (recurring_id,))
        self.conn.commit()

    def update_recurring_next_date(self, recurring_id, next_date):
        self.conn.execute(
            "UPDATE recurring_payments SET next_due_date = ? WHERE id = ?",
            (next_date, recurring_id),
        )
        self.conn.commit()

   
   
   
    # Savings goals
    
    def add_savings_goal(self, name, target_amount, deadline, created_date):
        cur = self.conn.execute(
            """
            INSERT INTO savings_goals (name, target_amount, current_amount, deadline, created_date)
            VALUES (?, ?, 0, ?, ?)
            """,
            (name, target_amount, deadline, created_date),
        )
        self.conn.commit()
        return cur.lastrowid

    def get_savings_goals(self):
        return self.conn.execute(
            "SELECT * FROM savings_goals ORDER BY (deadline IS NULL), deadline"
        ).fetchall()

    def contribute_to_goal(self, goal_id, amount):
        self.conn.execute(
            "UPDATE savings_goals SET current_amount = current_amount + ? WHERE id = ?",
            (amount, goal_id),
        )
        self.conn.commit()

    def delete_savings_goal(self, goal_id):
        self.conn.execute("DELETE FROM savings_goals WHERE id = ?", (goal_id,))
        self.conn.commit()

   
   
   
    def close(self):
        self.conn.close()
