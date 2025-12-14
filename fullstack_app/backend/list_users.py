
import os
import django
import sys

# Setup Django environment
# Current dir is .../backend
sys.path.append(os.getcwd()) 
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
django.setup()

from api.models import User

users = User.objects.all()
print(f"Found {users.count()} users:")
for user in users:
    print(f"- Username: '{user.username}', Role: '{user.role}', Phone: '{user.phone}', Email: '{user.email}'")
