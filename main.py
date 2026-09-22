"""
Expense & Savings Manager
--------------------------
A desktop app for tracking expenses, setting budgets, managing recurring
payments, working toward savings goals, and visualizing spending — built
with Tkinter (GUI), SQLite (storage), and Matplotlib (charts).

Run with:
    python main.py
"""

from gui import App

if __name__ == "__main__":
    app = App()
    app.mainloop()
