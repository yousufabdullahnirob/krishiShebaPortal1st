import os
import django
import sys

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
django.setup()

from api.models import ExpenseCalculation

def clear_expense_calculations():
    try:
        count = ExpenseCalculation.objects.count()
        print(f"Deleting {count} calculations...")
        ExpenseCalculation.objects.all().delete()
        print("All expense calculations deleted successfully.")
    except Exception as e:
        print(f"Error deleting calculations: {e}")

if __name__ == '__main__':
    clear_expense_calculations()
