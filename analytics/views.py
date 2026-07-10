from datetime import datetime, timedelta
from django.db.models import Sum
from django.db.models.functions import ExtractMonth, ExtractYear
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from transactions.models import Transaction, Category
from budgets.models import Budget
from savings.models import SavingsGoal

class AnalyticsOverviewView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        
        # 1. Date Range: Last 6 Months (including current)
        today = datetime.today()
        start_date = (today - timedelta(days=180)).replace(day=1)
        
        # 2. Monthly Income vs Expense Trends & Cash Flow
        transactions = Transaction.objects.filter(user=user, date__gte=start_date)
        
        # Aggregate by month and year
        monthly_data = {}
        for tx in transactions:
            month_key = tx.date.strftime("%Y-%m")
            month_name = tx.date.strftime("%b %Y")
            if month_key not in monthly_data:
                monthly_data[month_key] = {
                    'month_key': month_key,
                    'name': month_name,
                    'income': 0.0,
                    'expense': 0.0
                }
            if tx.type == 'income':
                monthly_data[month_key]['income'] += float(tx.amount)
            else:
                monthly_data[month_key]['expense'] += float(tx.amount)
                
        # Sort monthly trends chronologically
        sorted_trends = sorted(list(monthly_data.values()), key=lambda x: x['month_key'])
        
        # Calculate cash flow for each month
        for item in sorted_trends:
            item['cash_flow'] = item['income'] - item['expense']

        # 3. Category Breakdown (Current Month)
        current_month = today.month
        current_year = today.year
        
        current_month_txs = Transaction.objects.filter(
            user=user,
            date__month=current_month,
            date__year=current_year
        )
        
        # Expenses breakdown
        expenses = current_month_txs.filter(type='expense')
        expense_sum = float(expenses.aggregate(Sum('amount'))['amount__sum'] or 0.0)
        
        expense_cats = {}
        for tx in expenses:
            cat_name = tx.category.name if tx.category else "Uncategorized"
            cat_color = tx.category.color if tx.category else "#64748B"
            cat_icon = tx.category.icon if tx.category else "HelpCircle"
            if cat_name not in expense_cats:
                expense_cats[cat_name] = {
                    'name': cat_name,
                    'value': 0.0,
                    'color': cat_color,
                    'icon': cat_icon
                }
            expense_cats[cat_name]['value'] += float(tx.amount)
            
        expense_breakdown = list(expense_cats.values())
        for cat in expense_breakdown:
            cat['percentage'] = round((cat['value'] / expense_sum) * 100, 1) if expense_sum > 0 else 0.0

        # Incomes breakdown
        incomes = current_month_txs.filter(type='income')
        income_sum = float(incomes.aggregate(Sum('amount'))['amount__sum'] or 0.0)
        
        income_cats = {}
        for tx in incomes:
            cat_name = tx.category.name if tx.category else "Uncategorized"
            cat_color = tx.category.color if tx.category else "#64748B"
            cat_icon = tx.category.icon if tx.category else "HelpCircle"
            if cat_name not in income_cats:
                income_cats[cat_name] = {
                    'name': cat_name,
                    'value': 0.0,
                    'color': cat_color,
                    'icon': cat_icon
                }
            income_cats[cat_name]['value'] += float(tx.amount)
            
        income_breakdown = list(income_cats.values())
        for cat in income_breakdown:
            cat['percentage'] = round((cat['value'] / income_sum) * 100, 1) if income_sum > 0 else 0.0

        # 4. Savings Goals Progress
        savings_goals = SavingsGoal.objects.filter(user=user)
        goals_data = []
        for goal in savings_goals:
            goals_data.append({
                'id': goal.id,
                'name': goal.name,
                'target': float(goal.target_amount),
                'current': float(goal.current_amount),
                'percentage': round((float(goal.current_amount) / float(goal.target_amount)) * 100, 1) if goal.target_amount > 0 else 0.0,
                'is_completed': goal.is_completed
            })

        # 5. Rule-Based "AI" Insights
        insights = []
        
        # Rule 1: Expense > Income warning
        if expense_sum > income_sum and income_sum > 0:
            insights.append({
                'type': 'warning',
                'title': 'High Spending Alert',
                'message': f"You spent {round(expense_sum - income_sum, 2)} more than you earned this month. Consider trimming non-essential expenditures."
            })
        elif income_sum > 0:
            savings_rate = round(((income_sum - expense_sum) / income_sum) * 100, 1)
            if savings_rate >= 20.0:
                insights.append({
                    'type': 'success',
                    'title': 'Healthy Savings Rate',
                    'message': f"Great job! You saved {savings_rate}% of your income this month. You're on track to meet your targets."
                })
            else:
                insights.append({
                    'type': 'info',
                    'title': 'Increase Savings Opportunities',
                    'message': f"Your savings rate is {savings_rate}% this month. Aim to save at least 20% by cutting small daily expenses."
                })
                
        # Rule 2: Budget overruns or warnings
        budgets = Budget.objects.filter(user=user, month=current_month, year=current_year)
        for budget in budgets:
            cat_spend = float(expenses.filter(category=budget.category).aggregate(Sum('amount'))['amount__sum'] or 0.0)
            limit = float(budget.amount_limit)
            if cat_spend > limit:
                insights.append({
                    'type': 'danger',
                    'title': 'Budget Exceeded',
                    'message': f"You have exceeded your '{budget.category.name}' budget limit of {limit} by {round(cat_spend - limit, 2)}!"
                })
            elif cat_spend >= limit * 0.8:
                insights.append({
                    'type': 'warning',
                    'title': 'Nearing Budget Limit',
                    'message': f"You've used {round((cat_spend/limit)*100, 1)}% of your '{budget.category.name}' budget. You have {round(limit - cat_spend, 2)} remaining."
                })

        # Rule 3: Top spending categories
        sorted_expense_cats = sorted(expense_breakdown, key=lambda x: x['value'], reverse=True)
        if sorted_expense_cats:
            top_cat = sorted_expense_cats[0]
            if top_cat['percentage'] > 30.0:
                insights.append({
                    'type': 'info',
                    'title': f"Heavy '{top_cat['name']}' Spending",
                    'message': f"'{top_cat['name']}' accounts for {top_cat['percentage']}% of your monthly expenses. Look for ways to downsize in this category."
                })

        # Default insights if empty
        if not insights:
            insights.append({
                'type': 'info',
                'title': 'Welcome to Finora Insights',
                'message': 'Log more transactions and set up monthly budgets to generate customized financial recommendations here.'
            })

        return Response({
            'monthly_trends': sorted_trends,
            'expense_breakdown': expense_breakdown,
            'income_breakdown': income_breakdown,
            'savings_goals': goals_data,
            'insights': insights,
            'total_income': income_sum,
            'total_expense': expense_sum,
            'net_savings': income_sum - expense_sum
        })
