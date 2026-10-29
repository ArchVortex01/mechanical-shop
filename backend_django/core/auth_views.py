import jwt
import datetime
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate
from django.db import transaction
from .models import User, Admin, Cart, Notification

def send_success(message, data=None, status_code=status.HTTP_200_OK):
    return Response({
        'success': True,
        'message': message,
        'data': data
    }, status=status_code)

def send_error(message, error_detail=None, status_code=status.HTTP_400_BAD_REQUEST):
    return Response({
        'success': False,
        'message': message,
        'error': error_detail if error_detail else message
    }, status=status_code)

def generate_token(user, is_admin_table=False):
    payload = {
        'id': user.id,
        'email': user.email,
        'role': 'ADMIN' if is_admin_table else user.role,
        'full_name': user.name,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }
    secret = getattr(settings, 'JWT_SECRET', 'dev_jwt_secret_key_mahtomech_workshop_9876543210')
    return jwt.encode(payload, secret, algorithm='HS256')

class RegisterView(APIView):
    permission_classes = [AllowAny]
    @transaction.atomic
    def post(self, request):
        data = request.data
        email = data.get('email', '').lower().strip()
        phone = data.get('phone', '').strip()
        password = data.get('password')
        full_name = data.get('full_name') or data.get('name') or ''
        
        if User.objects.filter(email=email).exists():
            return send_error('An account with this email address already exists.', status_code=status.HTTP_409_CONFLICT)
        if phone and User.objects.filter(phone=phone).exists():
            return send_error('An account with this phone number already exists.', status_code=status.HTTP_409_CONFLICT)
            
        user = User.objects.create_user(
            email=email,
            name=full_name,
            phone=phone,
            password=password,
            role='USER'
        )
        
        # Create empty cart
        Cart.objects.create(user=user)
        
        # Create notification
        Notification.objects.create(
            user=user,
            title='Welcome to MahtoMech!',
            message='Thank you for registering. Explore our vehicle services and parts catalog.',
            type='system'
        )
        
        token = generate_token(user)
        
        user_response = {
            'id': user.id,
            'full_name': user.name,
            'email': user.email,
            'phone': user.phone,
            'role': user.role
        }
        
        return send_success('User registered successfully', {
            'user': user_response,
            'token': token
        }, status_code=status.HTTP_201_CREATED)

class LoginView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        identifier = request.data.get('email', '').strip()
        password = request.data.get('password')
        
        email = identifier.lower()
        if '@' not in identifier and identifier:
            phone_user = User.objects.filter(phone=identifier).first()
            if phone_user:
                email = phone_user.email
        
        user = authenticate(username=email, password=password)
        if not user:
            return send_error('Invalid email or password.', status_code=status.HTTP_401_UNAUTHORIZED)
            
        if not user.is_active:
            return send_error('Your account has been deactivated. Please contact support.', status_code=status.HTTP_403_FORBIDDEN)
            
        token = generate_token(user)
        
        user_response = {
            'id': user.id,
            'full_name': user.name,
            'email': user.email,
            'phone': user.phone,
            'role': user.role,
        }
        
        return send_success('Login successful', {
            'user': user_response,
            'token': token
        })

class AdminLoginView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        email = request.data.get('email', '').lower().strip()
        password = request.data.get('password')
        
        # Admin can be a User with role='ADMIN'
        user = authenticate(username=email, password=password)
        
        if not user or user.role != 'ADMIN':
            return send_error('Invalid admin credentials.', status_code=status.HTTP_401_UNAUTHORIZED)
            
        if not user.is_active:
            return send_error('Admin account is deactivated.', status_code=status.HTTP_403_FORBIDDEN)
            
        token = generate_token(user, is_admin_table=True)
        
        admin_response = {
            'id': user.id,
            'full_name': user.name,
            'email': user.email,
            'role': 'ADMIN'
        }
        
        return send_success('Admin login successful', {
            'admin': admin_response,
            'token': token
        })
