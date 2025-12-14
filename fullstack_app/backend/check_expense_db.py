import os
import django
import sys

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
django.setup()

from api.models import ExpenseCalculation

def check_expense_calculations():
    calculations = ExpenseCalculation.objects.all()
    print(f"Total calculations: {calculations.count()}")
    for c in calculations:
        try:
            print(f"ID: {c.id}")
            print(f"  Seed Cost: {c.seed_cost}")
            print(f"  Fertilizer Cost: {c.fertilizer_cost}")
            print(f"  Labour Cost: {c.labour_cost}")
            print(f"  Other Cost: {c.other_cost}")
            print(f"  Area: {c.area}")
            print(f"  Expected Yield: {c.expected_yield_per_area}")
            print(f"  Market Price: {c.market_price_per_kg}")
            print(f"  Total Cost: {c.total_cost}")
            print(f"  Expected Revenue: {c.expected_revenue}")
            print(f"  Expected Profit Margin: {c.expected_profit_margin}")
        except Exception as e:
            print(f"  Error accessing fields for ID {c.id}: {e}")

if __name__ == '__main__':
    check_expense_calculations()
