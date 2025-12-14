import os
import django
import sys

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
django.setup()

from api.models import Problem

def check_problems():
    problems = Problem.objects.all()
    print(f"Total problems: {problems.count()}")
    for p in problems:
        print(f"ID: {p.id}, Title: {p.title}, Status: {p.status}, Tracking ID: {p.tracking_id}")

if __name__ == '__main__':
    check_problems()
