#Finance Application - Nicole Tressler
# September 2025 - September 2026

"""
gui.py
Tkinter desktop interface for the Expense & Savings Manager.
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import date, datetime
import calendar

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from database import Database
import charts
import recurring

DATE_FMT = "%Y-%m-%d"
MONTH_FMT = "%Y-%m"

ALERT_WARNING_PCT = 80  # % of budget that triggers a "getting close" alert


def today_str():
    return date.today().strftime(DATE_FMT)


def current_month():
    return date.today().strftime(MONTH_FMT)


def month_label(month_str):
    d = datetime.strptime(month_str, MONTH_FMT)
    return d.strftime("%B %Y")


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Expense & Savings Manager")
        self.geometry("1050x700")
        self.minsize(900, 600)

        self.db = Database()
        self._style()

        # Auto-post any recurring payments that have come due since last run
        posted = recurring.process_due_recurring_payments(self.db)

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=8, pady=8)

        self.dashboard_tab = DashboardTab(notebook, self)
        self.expenses_tab = ExpensesTab(notebook, self)
        self.budgets_tab = BudgetsTab(notebook, self)
        self.recurring_tab = RecurringTab(notebook, self)
        self.savings_tab = SavingsTab(notebook, self)
        self.charts_tab = ChartsTab(notebook, self)

        notebook.add(self.dashboard_tab, text="  Dashboard  ")
        notebook.add(self.expenses_tab, text="  Expenses  ")
        notebook.add(self.budgets_tab, text="  Budgets  ")
        notebook.add(self.recurring_tab, text="  Recurring  ")
        notebook.add(self.savings_tab, text="  Savings Goals  ")
        notebook.add(self.charts_tab, text="  Charts  ")

        self.protocol("WM_DELETE_WINDOW", self._on_close)

        if posted:
            messagebox.showinfo(
                "Recurring Payments Posted",
                "The following recurring payments were automatically added:\n\n"
                + "\n".join(posted),
            )

        self.refresh_all()

    def _style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Green.Horizontal.TProgressbar", troughcolor="#ECEFF1", background="#2ECC71")
        style.configure("Yellow.Horizontal.TProgressbar", troughcolor="#ECEFF1", background="#F39C12")
        style.configure("Red.Horizontal.TProgressbar", troughcolor="#ECEFF1", background="#E74C3C")
        style.configure("Card.TFrame", background="#FFFFFF", relief="raised")

    def refresh_all(self):
        """Called whenever data changes so every tab reflects the latest state."""
        self.dashboard_tab.refresh()
        self.expenses_tab.refresh()
        self.budgets_tab.refresh()
        self.recurring_tab.refresh()
        self.savings_tab.refresh()
        self.charts_tab.refresh()

    def category_choices(self):
        cats = self.db.get_categories()
        return [(c["id"], c["name"]) for c in cats]

    def _on_close(self):
        self.db.close()
        self.destroy()





# Dashboard
class DashboardTab(ttk.Frame):
    def __init__(self, parent, app: App):
        super().__init__(parent)
        self.app = app

        top = ttk.Frame(self)
        top.pack(fill="x", padx=10, pady=10)

        self.total_var = tk.StringVar()
        self.budget_var = tk.StringVar()
        self.savings_var = tk.StringVar()

        self._stat_card(top, "This Month's Spending", self.total_var).pack(side="left", expand=True, fill="both", padx=5)
        self._stat_card(top, "Total Budget Remaining", self.budget_var).pack(side="left", expand=True, fill="both", padx=5)
        self._stat_card(top, "Total Saved", self.savings_var).pack(side="left", expand=True, fill="both", padx=5)

        # Alerts
        alert_frame = ttk.LabelFrame(self, text="Spending Alerts")
        alert_frame.pack(fill="x", padx=10, pady=(0, 10))
        self.alerts_list = tk.Listbox(alert_frame, height=6)
        self.alerts_list.pack(fill="x", padx=5, pady=5)

        # Quick add expense
        quick = ttk.LabelFrame(self, text="Quick Add Expense")
        quick.pack(fill="x", padx=10, pady=(0, 10))

        ttk.Label(quick, text="Amount ($):").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.amount_entry = ttk.Entry(quick, width=12)
        self.amount_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(quick, text="Category:").grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.category_combo = ttk.Combobox(quick, state="readonly", width=20)
        self.category_combo.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(quick, text="Description:").grid(row=0, column=4, padx=5, pady=5, sticky="e")
        self.desc_entry = ttk.Entry(quick, width=25)
        self.desc_entry.grid(row=0, column=5, padx=5, pady=5)

        ttk.Button(quick, text="Add Expense", command=self.add_expense).grid(row=0, column=6, padx=10, pady=5)




        # Recent expenses
        recent_frame = ttk.LabelFrame(self, text="Recent Expenses")
        recent_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        columns = ("date", "category", "description", "amount")
        self.recent_tree = ttk.Treeview(recent_frame, columns=columns, show="headings", height=10)
        for col, text, width in [
            ("date", "Date", 100),
            ("category", "Category", 150),
            ("description", "Description", 300),
            ("amount", "Amount", 100),
        ]:
            self.recent_tree.heading(col, text=text)
            self.recent_tree.column(col, width=width, anchor="center" if col != "description" else "w")
        self.recent_tree.pack(fill="both", expand=True, padx=5, pady=5)

    def _stat_card(self, parent, title, var):
        frame = ttk.Frame(parent, relief="groove", borderwidth=1)
        ttk.Label(frame, text=title, font=("Segoe UI", 10)).pack(pady=(10, 2))
        ttk.Label(frame, textvariable=var, font=("Segoe UI", 18, "bold")).pack(pady=(0, 10))
        return frame

    def add_expense(self):
        try:
            amount = float(self.amount_entry.get())
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Amount", "Please enter a positive number for the amount.")
            return

        cat_idx = self.category_combo.current()
        if cat_idx < 0:
            messagebox.showerror("Missing Category", "Please choose a category.")
            return
        category_id = self._category_ids[cat_idx]
        description = self.desc_entry.get().strip()

        self.app.db.add_expense(amount, category_id, description, today_str())
        self.amount_entry.delete(0, tk.END)
        self.desc_entry.delete(0, tk.END)
        self.app.refresh_all()
        self._check_alert_for(category_id)

    def _check_alert_for(self, category_id):
        month = current_month()
        status = self.app.db.get_budget_status(month)
        cat_name = dict(self.app.category_choices())[category_id]
        for s in status:
            if s["category"] == cat_name and s["pct"] >= 100:
                messagebox.showwarning(
                    "Budget Exceeded",
                    f"You've exceeded your {cat_name} budget for {month_label(month)}!\n"
                    f"Spent ${s['spent']:.2f} of ${s['budget']:.2f}.",
                )
            elif s["category"] == cat_name and s["pct"] >= ALERT_WARNING_PCT:
                messagebox.showinfo(
                    "Approaching Budget Limit",
                    f"You've used {s['pct']:.0f}% of your {cat_name} budget for {month_label(month)}.",
                )

    def refresh(self):
        cats = self.app.category_choices()
        self._category_ids = [c[0] for c in cats]
        self.category_combo["values"] = [c[1] for c in cats]

        month = current_month()
        total_spent = self.app.db.get_total_for_month(month)
        self.total_var.set(f"${total_spent:,.2f}")

        status = self.app.db.get_budget_status(month)
        total_remaining = sum(s["remaining"] for s in status)
        self.budget_var.set(f"${total_remaining:,.2f}" if status else "No budgets set")

        goals = self.app.db.get_savings_goals()
        total_saved = sum(g["current_amount"] for g in goals)
        self.savings_var.set(f"${total_saved:,.2f}")




        # Alerts
        self.alerts_list.delete(0, tk.END)
        any_alert = False
        for s in status:
            if s["pct"] >= 100:
                self.alerts_list.insert(
                    tk.END, f"\u26D4 {s['category']}: OVER budget — ${s['spent']:.2f} / ${s['budget']:.2f}"
                )
                any_alert = True
            elif s["pct"] >= ALERT_WARNING_PCT:
                self.alerts_list.insert(
                    tk.END, f"\u26A0 {s['category']}: {s['pct']:.0f}% of budget used"
                )
                any_alert = True
        if not any_alert:
            self.alerts_list.insert(tk.END, "No alerts — spending is within budget. \u2705")

        # Recent expenses (last 15)
        for row in self.recent_tree.get_children():
            self.recent_tree.delete(row)
        for e in self.app.db.get_expenses()[:15]:
            self.recent_tree.insert(
                "", tk.END,
                values=(e["date"], e["category_name"], e["description"] or "", f"${e['amount']:.2f}"),
            )




# All Expenses

class ExpensesTab(ttk.Frame):
    def __init__(self, parent, app: App):
        super().__init__(parent)
        self.app = app

        form = ttk.LabelFrame(self, text="Add Expense")
        form.pack(fill="x", padx=10, pady=10)

        ttk.Label(form, text="Amount ($):").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.amount_entry = ttk.Entry(form, width=12)
        self.amount_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(form, text="Category:").grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.category_combo = ttk.Combobox(form, state="readonly", width=20)
        self.category_combo.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(form, text="Date (YYYY-MM-DD):").grid(row=0, column=4, padx=5, pady=5, sticky="e")
        self.date_entry = ttk.Entry(form, width=12)
        self.date_entry.insert(0, today_str())
        self.date_entry.grid(row=0, column=5, padx=5, pady=5)

        ttk.Label(form, text="Description:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.desc_entry = ttk.Entry(form, width=40)
        self.desc_entry.grid(row=1, column=1, columnspan=3, padx=5, pady=5, sticky="w")

        ttk.Button(form, text="Add Expense", command=self.add_expense).grid(row=1, column=5, padx=5, pady=5)

        filter_frame = ttk.Frame(self)
        filter_frame.pack(fill="x", padx=10)
        ttk.Label(filter_frame, text="Filter by month:").pack(side="left", padx=(0, 5))
        self.month_filter = ttk.Combobox(filter_frame, state="readonly", width=12)
        self.month_filter.pack(side="left")
        self.month_filter.bind("<<ComboboxSelected>>", lambda e: self.refresh(keep_month=True))
        ttk.Button(filter_frame, text="Show All", command=lambda: self._set_filter(None)).pack(side="left", padx=5)
        ttk.Button(filter_frame, text="Delete Selected", command=self.delete_selected).pack(side="right")

        list_frame = ttk.Frame(self)
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        columns = ("id", "date", "category", "description", "amount", "source")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        headers = [("id", "ID", 40), ("date", "Date", 90), ("category", "Category", 130),
                   ("description", "Description", 280), ("amount", "Amount", 90), ("source", "Source", 90)]
        for col, text, width in headers:
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width, anchor="center" if col != "description" else "w")
        self.tree.column("id", width=40)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

    def _set_filter(self, month):
        if month is None:
            self.month_filter.set("")
        self.refresh(keep_month=(month is not None))

    def add_expense(self):
        try:
            amount = float(self.amount_entry.get())
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Amount", "Please enter a positive number for the amount.")
            return
        cat_idx = self.category_combo.current()
        if cat_idx < 0:
            messagebox.showerror("Missing Category", "Please choose a category.")
            return
        try:
            datetime.strptime(self.date_entry.get(), DATE_FMT)
        except ValueError:
            messagebox.showerror("Invalid Date", "Please use YYYY-MM-DD format.")
            return

        category_id = self._category_ids[cat_idx]
        self.app.db.add_expense(amount, category_id, self.desc_entry.get().strip(), self.date_entry.get())
        self.amount_entry.delete(0, tk.END)
        self.desc_entry.delete(0, tk.END)
        self.date_entry.delete(0, tk.END)
        self.date_entry.insert(0, today_str())
        self.app.refresh_all()

    def delete_selected(self):
        selection = self.tree.selection()
        if not selection:
            return
        if not messagebox.askyesno("Confirm Delete", "Delete the selected expense(s)?"):
            return
        for item in selection:
            expense_id = self.tree.item(item, "values")[0]
            self.app.db.delete_expense(expense_id)
        self.app.refresh_all()

    def refresh(self, keep_month=False):
        cats = self.app.category_choices()
        self._category_ids = [c[0] for c in cats]
        self.category_combo["values"] = [c[1] for c in cats]

        months = sorted({e["date"][:7] for e in self.app.db.get_expenses()}, reverse=True)
        self.month_filter["values"] = months
        selected_month = self.month_filter.get() if keep_month else None

        for row in self.tree.get_children():
            self.tree.delete(row)
        for e in self.app.db.get_expenses(selected_month or None):
            self.tree.insert(
                "", tk.END,
                values=(e["id"], e["date"], e["category_name"], e["description"] or "",
                        f"${e['amount']:.2f}", e["source"]),
            )





# My Budgets

class BudgetsTab(ttk.Frame):
    def __init__(self, parent, app: App):
        super().__init__(parent)
        self.app = app

        form = ttk.LabelFrame(self, text="Set Monthly Budget")
        form.pack(fill="x", padx=10, pady=10)

        ttk.Label(form, text="Month (YYYY-MM):").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.month_entry = ttk.Entry(form, width=10)
        self.month_entry.insert(0, current_month())
        self.month_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(form, text="Category:").grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.category_combo = ttk.Combobox(form, state="readonly", width=20)
        self.category_combo.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(form, text="Budget Amount ($):").grid(row=0, column=4, padx=5, pady=5, sticky="e")
        self.amount_entry = ttk.Entry(form, width=12)
        self.amount_entry.grid(row=0, column=5, padx=5, pady=5)

        ttk.Button(form, text="Set Budget", command=self.set_budget).grid(row=0, column=6, padx=10, pady=5)
        ttk.Button(form, text="View This Month", command=lambda: self._view_month(current_month())).grid(
            row=0, column=7, padx=5, pady=5
        )

        self.status_container = ttk.Frame(self)
        self.status_container.pack(fill="both", expand=True, padx=10, pady=10)

    def set_budget(self):
        month = self.month_entry.get().strip()
        try:
            datetime.strptime(month, MONTH_FMT)
        except ValueError:
            messagebox.showerror("Invalid Month", "Please use YYYY-MM format.")
            return
        cat_idx = self.category_combo.current()
        if cat_idx < 0:
            messagebox.showerror("Missing Category", "Please choose a category.")
            return
        try:
            amount = float(self.amount_entry.get())
            if amount < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Amount", "Please enter a non-negative number.")
            return

        category_id = self._category_ids[cat_idx]
        self.app.db.set_budget(category_id, month, amount)
        self.amount_entry.delete(0, tk.END)
        self.app.refresh_all()

    def _view_month(self, month):
        self.month_entry.delete(0, tk.END)
        self.month_entry.insert(0, month)
        self.refresh()

    def refresh(self):
        cats = self.app.category_choices()
        self._category_ids = [c[0] for c in cats]
        self.category_combo["values"] = [c[1] for c in cats]

        for widget in self.status_container.winfo_children():
            widget.destroy()

        month = self.month_entry.get().strip() or current_month()
        try:
            datetime.strptime(month, MONTH_FMT)
        except ValueError:
            return
        status = self.app.db.get_budget_status(month)

        header = ttk.Label(self.status_container, text=f"Budget Status — {month_label(month)}", font=("Segoe UI", 12, "bold"))
        header.pack(anchor="w", pady=(0, 10))

        if not status:
            ttk.Label(self.status_container, text="No budgets set for this month yet.").pack(anchor="w")
            return

        for s in status:
            row = ttk.Frame(self.status_container)
            row.pack(fill="x", pady=6)

            ttk.Label(row, text=s["category"], width=16).pack(side="left")

            style_name = "Red.Horizontal.TProgressbar" if s["pct"] >= 100 else (
                "Yellow.Horizontal.TProgressbar" if s["pct"] >= ALERT_WARNING_PCT else "Green.Horizontal.TProgressbar"
            )
            pb = ttk.Progressbar(row, style=style_name, maximum=100, value=min(s["pct"], 100), length=350)
            pb.pack(side="left", padx=10)

            label = f"${s['spent']:.2f} / ${s['budget']:.2f}  ({s['pct']:.0f}%)"
            ttk.Label(row, text=label, width=28).pack(side="left")

            if s["remaining"] < 0:
                ttk.Label(row, text=f"Over by ${-s['remaining']:.2f}", foreground="#E74C3C").pack(side="left")
            else:
                ttk.Label(row, text=f"${s['remaining']:.2f} left", foreground="#2ECC71").pack(side="left")





# Recurring payments

class RecurringTab(ttk.Frame):
    FREQUENCIES = ["daily", "weekly", "monthly", "yearly"]

    def __init__(self, parent, app: App):
        super().__init__(parent)
        self.app = app

        form = ttk.LabelFrame(self, text="Add Recurring Payment")
        form.pack(fill="x", padx=10, pady=10)

        ttk.Label(form, text="Name:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.name_entry = ttk.Entry(form, width=20)
        self.name_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(form, text="Amount ($):").grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.amount_entry = ttk.Entry(form, width=10)
        self.amount_entry.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(form, text="Category:").grid(row=0, column=4, padx=5, pady=5, sticky="e")
        self.category_combo = ttk.Combobox(form, state="readonly", width=18)
        self.category_combo.grid(row=0, column=5, padx=5, pady=5)

        ttk.Label(form, text="Frequency:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.freq_combo = ttk.Combobox(form, state="readonly", values=self.FREQUENCIES, width=18)
        self.freq_combo.current(2)  # monthly
        self.freq_combo.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(form, text="Next Due Date (YYYY-MM-DD):").grid(row=1, column=2, padx=5, pady=5, sticky="e")
        self.due_entry = ttk.Entry(form, width=12)
        self.due_entry.insert(0, today_str())
        self.due_entry.grid(row=1, column=3, padx=5, pady=5)

        ttk.Button(form, text="Add Recurring Payment", command=self.add_recurring).grid(row=1, column=5, padx=5, pady=5)

        info = ttk.Label(
            self,
            text="Recurring payments are automatically posted as expenses when their due date arrives "
                 "(checked each time the app starts).",
            foreground="#607D8B",
        )
        info.pack(anchor="w", padx=10)

        list_frame = ttk.Frame(self)
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        columns = ("id", "name", "amount", "category", "frequency", "next_due", "active")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        headers = [("id", "ID", 40), ("name", "Name", 160), ("amount", "Amount", 80),
                   ("category", "Category", 130), ("frequency", "Frequency", 90),
                   ("next_due", "Next Due", 100), ("active", "Active", 60)]
        for col, text, width in headers:
            self.tree.heading(col, text=text)
            self.tree.column(col, width=width, anchor="center")
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))
        ttk.Button(btn_frame, text="Toggle Active/Paused", command=self.toggle_selected).pack(side="left")
        ttk.Button(btn_frame, text="Delete Selected", command=self.delete_selected).pack(side="left", padx=5)

    def add_recurring(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showerror("Missing Name", "Please enter a name for this payment.")
            return
        try:
            amount = float(self.amount_entry.get())
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Amount", "Please enter a positive number for the amount.")
            return
        cat_idx = self.category_combo.current()
        if cat_idx < 0:
            messagebox.showerror("Missing Category", "Please choose a category.")
            return
        try:
            datetime.strptime(self.due_entry.get(), DATE_FMT)
        except ValueError:
            messagebox.showerror("Invalid Date", "Please use YYYY-MM-DD format.")
            return

        category_id = self._category_ids[cat_idx]
        frequency = self.freq_combo.get()
        self.app.db.add_recurring(name, amount, category_id, frequency, self.due_entry.get())
        self.name_entry.delete(0, tk.END)
        self.amount_entry.delete(0, tk.END)
        self.app.refresh_all()

    def toggle_selected(self):
        selection = self.tree.selection()
        if not selection:
            return
        for item in selection:
            values = self.tree.item(item, "values")
            recurring_id, active = values[0], values[6]
            self.app.db.toggle_recurring(recurring_id, active != "Yes")
        self.app.refresh_all()

    def delete_selected(self):
        selection = self.tree.selection()
        if not selection:
            return
        if not messagebox.askyesno("Confirm Delete", "Delete the selected recurring payment(s)?"):
            return
        for item in selection:
            recurring_id = self.tree.item(item, "values")[0]
            self.app.db.delete_recurring(recurring_id)
        self.app.refresh_all()

    def refresh(self):
        cats = self.app.category_choices()
        self._category_ids = [c[0] for c in cats]
        self.category_combo["values"] = [c[1] for c in cats]

        for row in self.tree.get_children():
            self.tree.delete(row)
        for r in self.app.db.get_recurring():
            self.tree.insert(
                "", tk.END,
                values=(r["id"], r["name"], f"${r['amount']:.2f}", r["category_name"],
                        r["frequency"], r["next_due_date"], "Yes" if r["active"] else "No"),
            )





# Savings goals

class SavingsTab(ttk.Frame):
    def __init__(self, parent, app: App):
        super().__init__(parent)
        self.app = app

        form = ttk.LabelFrame(self, text="Add Savings Goal")
        form.pack(fill="x", padx=10, pady=10)

        ttk.Label(form, text="Goal Name:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.name_entry = ttk.Entry(form, width=25)
        self.name_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(form, text="Target Amount ($):").grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.target_entry = ttk.Entry(form, width=12)
        self.target_entry.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(form, text="Deadline (YYYY-MM-DD, optional):").grid(row=0, column=4, padx=5, pady=5, sticky="e")
        self.deadline_entry = ttk.Entry(form, width=12)
        self.deadline_entry.grid(row=0, column=5, padx=5, pady=5)

        ttk.Button(form, text="Add Goal", command=self.add_goal).grid(row=0, column=6, padx=10, pady=5)

        self.goals_container = ttk.Frame(self)
        self.goals_container.pack(fill="both", expand=True, padx=10, pady=10)

    def add_goal(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showerror("Missing Name", "Please enter a goal name.")
            return
        try:
            target = float(self.target_entry.get())
            if target <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Target", "Please enter a positive target amount.")
            return
        deadline = self.deadline_entry.get().strip() or None
        if deadline:
            try:
                datetime.strptime(deadline, DATE_FMT)
            except ValueError:
                messagebox.showerror("Invalid Deadline", "Please use YYYY-MM-DD format, or leave blank.")
                return

        self.app.db.add_savings_goal(name, target, deadline, today_str())
        self.name_entry.delete(0, tk.END)
        self.target_entry.delete(0, tk.END)
        self.deadline_entry.delete(0, tk.END)
        self.app.refresh_all()

    def contribute(self, goal_id, goal_name):
        amount = simpledialog.askfloat(
            "Contribute to Goal", f"How much would you like to add to '{goal_name}'?", minvalue=0.01
        )
        if amount:
            self.app.db.contribute_to_goal(goal_id, amount)
            self.app.refresh_all()

    def delete_goal(self, goal_id, goal_name):
        if messagebox.askyesno("Delete Goal", f"Delete the savings goal '{goal_name}'?"):
            self.app.db.delete_savings_goal(goal_id)
            self.app.refresh_all()

    def refresh(self):
        for widget in self.goals_container.winfo_children():
            widget.destroy()

        goals = self.app.db.get_savings_goals()
        if not goals:
            ttk.Label(self.goals_container, text="No savings goals yet — add one above!").pack(anchor="w")
            return

        for g in goals:
            pct = min(g["current_amount"] / g["target_amount"] * 100, 100) if g["target_amount"] else 0
            row = ttk.Frame(self.goals_container, relief="groove", borderwidth=1)
            row.pack(fill="x", pady=6, ipady=6)

            title = f"{g['name']}"
            if g["deadline"]:
                title += f"   (by {g['deadline']})"
            ttk.Label(row, text=title, font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=10, pady=(5, 0))

            bar_row = ttk.Frame(row)
            bar_row.pack(fill="x", padx=10, pady=5)
            style_name = "Green.Horizontal.TProgressbar" if pct >= 100 else "Yellow.Horizontal.TProgressbar" if pct >= 50 else "Red.Horizontal.TProgressbar"
            pb = ttk.Progressbar(bar_row, style=style_name, maximum=100, value=pct, length=400)
            pb.pack(side="left")
            ttk.Label(
                bar_row,
                text=f"${g['current_amount']:.2f} / ${g['target_amount']:.2f}  ({pct:.0f}%)",
            ).pack(side="left", padx=10)

            btn_row = ttk.Frame(row)
            btn_row.pack(anchor="e", padx=10)
            ttk.Button(btn_row, text="Contribute", command=lambda gid=g["id"], name=g["name"]: self.contribute(gid, name)).pack(side="left", padx=3)
            ttk.Button(btn_row, text="Delete", command=lambda gid=g["id"], name=g["name"]: self.delete_goal(gid, name)).pack(side="left", padx=3)




# Charts

class ChartsTab(ttk.Frame):
    def __init__(self, parent, app: App):
        super().__init__(parent)
        self.app = app

        controls = ttk.Frame(self)
        controls.pack(fill="x", padx=10, pady=10)

        ttk.Label(controls, text="Chart type:").pack(side="left", padx=(0, 5))
        self.chart_combo = ttk.Combobox(
            controls, state="readonly",
            values=["Spending by Category (Pie)", "Budget vs. Actual (Bar)", "Spending Trend (Line)"],
        )
        self.chart_combo.current(0)
        self.chart_combo.pack(side="left", padx=5)
        self.chart_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh())

        ttk.Label(controls, text="Month:").pack(side="left", padx=(20, 5))
        self.month_combo = ttk.Combobox(controls, state="readonly", width=10)
        self.month_combo.pack(side="left")
        self.month_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh())

        ttk.Button(controls, text="Refresh", command=self.refresh).pack(side="left", padx=15)

        self.canvas_frame = ttk.Frame(self)
        self.canvas_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self._canvas_widget = None

    def refresh(self):
        months = sorted({e["date"][:7] for e in self.app.db.get_expenses()}, reverse=True)
        if not months:
            months = [current_month()]
        current_selection = self.month_combo.get()
        self.month_combo["values"] = months
        if current_selection in months:
            self.month_combo.set(current_selection)
        else:
            self.month_combo.set(months[0])

        month = self.month_combo.get()
        choice = self.chart_combo.get()

        if choice.startswith("Spending by Category"):
            fig = charts.spending_by_category_pie(self.app.db.get_spending_by_category(month), month_label(month))
        elif choice.startswith("Budget vs"):
            fig = charts.budget_vs_actual_bar(self.app.db.get_budget_status(month), month_label(month))
        else:
            fig = charts.monthly_trend_line(self.app.db.get_monthly_totals(12))

        if self._canvas_widget is not None:
            self._canvas_widget.get_tk_widget().destroy()

        canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self._canvas_widget = canvas
