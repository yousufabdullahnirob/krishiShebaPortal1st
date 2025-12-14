
import os
import django
import sys

# Setup Django environment
sys.path.append(os.getcwd()) 
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_project.settings')
django.setup()

from api.models import User

try:
    user = User.objects.get(username='django')
    if user.check_password('django'):
        print("SUCCESS: Password for user 'django' is 'django'")
    else:
        print("FAILURE: Password for user 'django' is NOT 'django'. Resetting...")
        user.set_password('django')
        user.save()
        print("RESET: Password for user 'django' has been reset to 'django'")
except User.DoesNotExist:
    print("ERROR: User 'django' not found.")
