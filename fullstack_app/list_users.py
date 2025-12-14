
import os
import django
import sys

# Setup Django environment
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from api.models import User

users = User.objects.all()
print(f"Found {users.count()} users:")
for user in users:
    print(f"- Username: '{user.username}', Role: '{user.role}', Phone: '{user.phone}', Email: '{user.email}'")
