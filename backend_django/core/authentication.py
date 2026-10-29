import jwt
from django.conf import settings
from rest_framework import authentication
from rest_framework import exceptions
from .models import User, Admin

class JWTAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
            
        try:
            token = auth_header.split(' ')[1]
        except IndexError:
            return None
            
        try:
            secret = getattr(settings, 'JWT_SECRET', 'dev_jwt_secret_key_mahtomech_workshop_9876543210')
            decoded = jwt.decode(token, secret, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('Authentication token has expired. Please login again.')
        except jwt.DecodeError:
            raise exceptions.AuthenticationFailed('Invalid authentication token.')
            
        is_admin_table = decoded.get('isAdminTable', False)
        user_id = decoded.get('id')
        
        if is_admin_table:
            try:
                admin = Admin.objects.get(id=user_id)
                if not admin.user.is_active:
                    raise exceptions.AuthenticationFailed('Admin account is deactivated.')
                # Attach the user object connected to this admin
                return (admin.user, token)
            except Admin.DoesNotExist:
                raise exceptions.AuthenticationFailed('Admin account not found.')
                
        try:
            user = User.objects.get(id=user_id)
            if not user.is_active:
                raise exceptions.AuthenticationFailed('Account has been deactivated.')
            return (user, token)
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed('User associated with this token no longer exists.')
