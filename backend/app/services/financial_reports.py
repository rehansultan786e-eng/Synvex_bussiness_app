from app.database.connection import get_db
from datetime import datetime

async def get_revenue_overview():
    """
    Real-time revenue overview:
    - Total contracts value
    - Total received (milestones marked Received)
    - Total pending (milestones not yet received)
    - Total overdue
    """
    db = get_db()
    contracts = await db.contracts.find({"is_deleted": False}).to_list(1000)

    total_contract_value = 0.0
    total_received = 0.0
    total_pending = 0.0
    total_overdue = 0.0

    for c in contracts:
        total_contract_value += c.get("total_value", 0)
        for m in c.get("milestones", []):
            amount = m.get("amount", 0)
            if m["status"] == "Received":
                total_received += amount
            elif m["status"] == "Overdue":
                total_overdue += amount
            else:
                total_pending += amount

    return {
        "total_contract_value": round(total_contract_value, 2),
        "total_received": round(total_received, 2),
        "total_pending": round(total_pending, 2),
        "total_overdue": round(total_overdue, 2),
        "collection_rate": round(
            (total_received / total_contract_value * 100) if total_contract_value > 0 else 0, 2
        )
    }


async def get_profit_and_loss(month: int = None, year: int = None):
    """
    P&L Report (SRS 4.5):
    Revenue (milestone receipts) minus Expenses and Salaries.
    Filterable by month and/or year.
    """
    db = get_db()

    # Revenue: milestones marked Received in the given period
    contracts = await db.contracts.find({"is_deleted": False}).to_list(1000)
    total_revenue = 0.0
    for c in contracts:
        for m in c.get("milestones", []):
            if m["status"] == "Received" and m.get("paid_date"):
                paid_date = m["paid_date"]
                paid_year = int(paid_date[:4])
                paid_month = int(paid_date[5:7])
                if year and paid_year != year:
                    continue
                if month and paid_month != month:
                    continue
                total_revenue += m.get("amount", 0)

    # Expenses: approved expenses in the given period
    expense_query = {"is_deleted": False, "status": "Approved"}
    expenses = await db.expenses.find(expense_query).to_list(10000)
    total_expenses = 0.0
    for e in expenses:
        exp_date = e.get("expense_date", "")
        if year and int(exp_date[:4]) != year:
            continue
        if month and int(exp_date[5:7]) != month:
            continue
        total_expenses += e.get("amount", 0)

    # Salaries: paid payroll batches in the given period
    salary_query = {"status": "Paid"}
    if year:
        salary_query["year"] = year
    if month:
        salary_query["month"] = month
    batches = await db.payroll_batches.find(salary_query).to_list(100)
    total_salaries = sum(b.get("total_net", 0) for b in batches)
    total_commissions = sum(b.get("total_commission", 0) for b in batches)

    total_costs = total_expenses + total_salaries
    net_profit = total_revenue - total_costs

    return {
        "period": {
            "month": month,
            "year": year
        },
        "revenue": round(total_revenue, 2),
        "expenses": round(total_expenses, 2),
        "salaries": round(total_salaries, 2),
        "commissions_paid": round(total_commissions, 2),
        "total_costs": round(total_costs, 2),
        "net_profit": round(net_profit, 2),
        "profit_margin_percent": round(
            (net_profit / total_revenue * 100) if total_revenue > 0 else 0, 2
        )
    }


async def get_cash_flow(month: int = None, year: int = None):
    """
    Cash Flow Statement (SRS 4.5):
    Inflows (milestone payments received) vs Outflows (salaries + expenses paid).
    """
    db = get_db()

    # Inflows: milestone payments received
    contracts = await db.contracts.find({"is_deleted": False}).to_list(1000)
    inflows = []
    total_inflow = 0.0

    for c in contracts:
        for m in c.get("milestones", []):
            if m["status"] == "Received" and m.get("paid_date"):
                paid_date = m["paid_date"]
                if year and int(paid_date[:4]) != year:
                    continue
                if month and int(paid_date[5:7]) != month:
                    continue
                amount = m.get("amount", 0)
                total_inflow += amount
                inflows.append({
                    "date": paid_date,
                    "description": f"{c['client_name']} — {m['description']}",
                    "amount": amount,
                    "currency": c.get("currency", "USD"),
                    "type": "inflow"
                })

    # Outflows: approved expenses
    expense_query = {"is_deleted": False, "status": "Approved"}
    expenses = await db.expenses.find(expense_query).to_list(10000)
    outflows = []
    total_outflow = 0.0

    for e in expenses:
        exp_date = e.get("expense_date", "")
        if year and int(exp_date[:4]) != year:
            continue
        if month and int(exp_date[5:7]) != month:
            continue
        amount = e.get("amount", 0)
        total_outflow += amount
        outflows.append({
            "date": exp_date,
            "description": f"{e['category']} — {e.get('description', '')}",
            "amount": amount,
            "type": "outflow"
        })

    # Outflows: paid salaries
    salary_query = {"status": "Paid"}
    if year:
        salary_query["year"] = year
    if month:
        salary_query["month"] = month
    batches = await db.payroll_batches.find(salary_query).to_list(100)
    for b in batches:
        amount = b.get("total_net", 0)
        total_outflow += amount
        outflows.append({
            "date": f"{b['year']}-{b['month']:02d}-01",
            "description": f"Payroll — {b['month']:02d}/{b['year']}",
            "amount": amount,
            "type": "outflow"
        })

    net_cash_flow = total_inflow - total_outflow

    return {
        "period": {"month": month, "year": year},
        "total_inflow": round(total_inflow, 2),
        "total_outflow": round(total_outflow, 2),
        "net_cash_flow": round(net_cash_flow, 2),
        "inflows": sorted(inflows, key=lambda x: x["date"]),
        "outflows": sorted(outflows, key=lambda x: x["date"])
    }


async def get_outstanding_receivables():
    """
    Real-time outstanding receivables:
    All overdue + upcoming milestones with client contact info.
    """
    db = get_db()
    from datetime import date
    contracts = await db.contracts.find({"is_deleted": False}).to_list(1000)
    today = date.today()
    receivables = []

    for c in contracts:
        for m in c.get("milestones", []):
            if m["status"] in ["Overdue", "Upcoming", "Due"]:
                receivables.append({
                    "contract_id": c["contract_id"],
                    "client_name": c["client_name"],
                    "project_name": c["project_name"],
                    "milestone_id": m["milestone_id"],
                    "description": m["description"],
                    "due_date": m["due_date"],
                    "amount": m["amount"],
                    "currency": c.get("currency", "USD"),
                    "status": m["status"],
                    "days_overdue": (
                        (today - date.fromisoformat(m["due_date"])).days
                        if m["status"] == "Overdue" else 0
                    )
                })

    receivables.sort(key=lambda x: x["due_date"])
    return receivables


async def get_executive_dashboard_summary():
    """
    CEO Executive Dashboard — unified KPIs across all modules (SRS 12.2).
    """
    db = get_db()

    # Revenue
    revenue = await get_revenue_overview()

    # Headcount
    total_employees = await db.employees.count_documents(
        {"is_deleted": False, "status": "active"}
    )

    # Open leads
    open_leads = await db.leads.count_documents(
        {"is_deleted": False, "status": {"$nin": ["Won", "Lost"]}}
    )
    won_leads = await db.leads.count_documents(
        {"is_deleted": False, "status": "Won"}
    )

    # Pending commissions
    commissions = await db.commissions.find({}).to_list(10000)
    pending_commission_total = 0.0
    for c in commissions:
        for mp in c.get("milestone_payouts", []):
            if mp["status"] == "Pending":
                pending_commission_total += mp["commission_share"]

    # Pending expenses
    pending_expenses = await db.expenses.count_documents(
        {"is_deleted": False, "status": "Pending"}
    )

    # Pending payroll
    pending_payroll = await db.payroll_batches.count_documents(
        {"status": {"$in": ["Pending Review", "Pending Approval"]}}
    )

    # Assets
    total_assets = await db.assets.count_documents({}) if await db.list_collection_names().__class__ else 0
    try:
        total_assets = await db.assets.count_documents({})
    except Exception:
        total_assets = 0

    return {
        "revenue": revenue,
        "headcount": total_employees,
        "leads": {
            "open": open_leads,
            "won": won_leads
        },
        "pending_commission_liability": round(pending_commission_total, 2),
        "pending_expenses_count": pending_expenses,
        "pending_payroll_batches": pending_payroll,
        "total_assets": total_assets
    }