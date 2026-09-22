#Finance Application - Nicole Tressler
# September 2025 - September 2026

"""
charts.py
Builds matplotlib Figures for embedding in the Tkinter GUI:
- Pie chart: spending by category for a given month
- Bar chart: budget vs. actual spend per category
- Line chart: total spending trend over recent months
"""

from matplotlib.figure import Figure



def spending_by_category_pie(spending_rows, month_label):
    fig = Figure(figsize=(5.5, 4.5), dpi=100)
    ax = fig.add_subplot(111)
    if not spending_rows:
        ax.text(0.5, 0.5, "No expenses recorded\nfor this month", ha="center", va="center")
        ax.axis("off")
        return fig

    labels = [row["name"] for row in spending_rows]
    values = [row["total"] for row in spending_rows]
    colors = [row["color"] for row in spending_rows]

    wedges, _texts, autotexts = ax.pie(
        values,
        labels=labels,
        colors=colors,
        autopct=lambda pct: f"${pct/100*sum(values):.0f}",
        startangle=90,
        textprops={"fontsize": 8},
    )
    ax.set_title(f"Spending by Category — {month_label}")
    fig.tight_layout()
    return fig







def budget_vs_actual_bar(budget_status, month_label):
    fig = Figure(figsize=(6, 4.5), dpi=100)
    ax = fig.add_subplot(111)
    if not budget_status:
        ax.text(0.5, 0.5, "No budgets set\nfor this month", ha="center", va="center")
        ax.axis("off")
        return fig

    categories = [b["category"] for b in budget_status]
    budgets = [b["budget"] for b in budget_status]
    spent = [b["spent"] for b in budget_status]

    x = range(len(categories))
    width = 0.35
    ax.bar([i - width / 2 for i in x], budgets, width, label="Budget", color="#B0BEC5")
    bar_colors = ["#E74C3C" if b["pct"] >= 100 else "#F39C12" if b["pct"] >= 80 else "#2ECC71" for b in budget_status]
    ax.bar([i + width / 2 for i in x], spent, width, label="Spent", color=bar_colors)



    ax.set_xticks(list(x))
    ax.set_xticklabels(categories, rotation=30, ha="right", fontsize=8)
    ax.set_ylabel("Amount ($)")
    ax.set_title(f"Budget vs. Actual — {month_label}")
    ax.legend()
    fig.tight_layout()
    return fig






def monthly_trend_line(monthly_totals):
    fig = Figure(figsize=(6, 4.5), dpi=100)
    ax = fig.add_subplot(111)
    if not monthly_totals:
        ax.text(0.5, 0.5, "No expense history yet", ha="center", va="center")
        ax.axis("off")
        return fig

    months = [row["month"] for row in monthly_totals]
    totals = [row["total"] or 0 for row in monthly_totals]


    ax.plot(months, totals, marker="o", color="#3498DB", linewidth=2)
    ax.fill_between(months, totals, alpha=0.15, color="#3498DB")
    ax.set_ylabel("Total Spending ($)")
    ax.set_title("Spending Trend")
    ax.tick_params(axis="x", rotation=30)
    for i, v in enumerate(totals):
        ax.annotate(f"${v:,.0f}", (i, v), textcoords="offset points", xytext=(0, 8), fontsize=8, ha="center")
    fig.tight_layout()
    return fig
