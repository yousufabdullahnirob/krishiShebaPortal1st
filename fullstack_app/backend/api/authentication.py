
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .models import User
import logging

logger = logging.getLogger(__name__)

class SimpleTokenAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        logger.info(f"SimpleTokenAuthentication: Header: {auth_header}")
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return None

        token = auth_header.split(' ')[1]
        logger.info(f"SimpleTokenAuthentication: Token: {token}")
        
        # Handle admin token
        if token == 'admin_token':
            user, _ = User.objects.get_or_create(username='admin', defaults={'role': 'admin'})
            return (user, None)

        # Handle farmer/buyer/expert tokens
        if token.startswith('farmer_token_') or token.startswith('buyer_token_') or token.startswith('expert_token_'):
            try:
                user_id = int(token.split('_')[-1])
                logger.info(f"SimpleTokenAuthentication: User ID: {user_id}")
                user = User.objects.get(id=user_id)
                logger.info(f"SimpleTokenAuthentication: User found: {user}")
                return (user, token)
            except (ValueError, User.DoesNotExist) as e:
                logger.error(f"SimpleTokenAuthentication: Error: {e}")
                raise AuthenticationFailed('Invalid token')

        logger.warning("SimpleTokenAuthentication: Token pattern mismatch")
        return None
