
import os
import django
import sys

# Add the project directory to the sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
django.setup()

from api.models import User

users = User.objects.all()
print(f"Total users: {users.count()}")
for user in users:
    print(f"Username: {user.username}, Role: {user.role}, Phone: {user.phone}, Email: {user.email}")
