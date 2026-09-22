# Expense & Savings Manager

A desktop application for tracking expenses and building savings habits,
built with Python's Tkinter (GUI), SQLite (storage), and Matplotlib (charts).


## Features

- **Expense categorization** — log expenses under built-in categories (Food, Housing,
  Transportation, Utilities, Entertainment, other.) with date and an option for a description.

- **Monthly budgets** — set a budget per category per month and see spend vs. budget with color-coded progress bars (green / yellow / red).

- **Financial charts** — pie chart of spending by category, bar chart of budget vs.
  actual, and a line chart of spending trend over recent months.

- **Recurring payments** — define bills/subscriptions (daily, weekly, monthly, or yearly) that are automatically posted as expenses whenever their due date arrives (checked each time the app starts, catching up on anything missed).

- **Savings goals** — set a target amount and optional deadline, then log contributions and watch a progress bar fill in.

- **Spending alerts** — get a warning at 80% of a category budget and an alert when a budget is exceeded, both on the Dashboard and when adding an expense.



## Setup

```bash
pip install -r requirements.txt
python main.py
```

Data is stored locally in `expenses.db` (SQLite), created automatically next to
the app on first run.

## Project structure

```
expense_manager/
├── main.py          # Entry point — run this
├── gui.py           # Tkinter interface (Dashboard, Expenses, Budgets,
│                     #   Recurring, Savings Goals, Charts tabs)
├── database.py       # SQLite schema and all data access
├── recurring.py       # Due-date math + auto-posting recurring payments
├── charts.py           # Matplotlib figure builders
└── requirements.txt
```

## Notes 

- Need to add additional categories.
  
- Dates are entered as `YYYY-MM-DD` and months as `YYYY-MM`.

- All amounts are treated as a single currency with "$".

- Add function to edit an entry for "Budget".