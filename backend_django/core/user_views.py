from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.contrib.auth.hashers import check_password, make_password
from .models import User, Vehicle, Order, ServiceBooking, Address
from .auth_views import send_success, send_error

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        data = {
            'id': user.id,
            'full_name': user.name,
            'email': user.email,
            'phone': user.phone,
            'avatar_url': getattr(user, 'avatar_url', None),
            'role': user.role
        }
        return send_success('Profile retrieved', data)

    def put(self, request):
        user = request.user
        user.name = request.data.get('full_name', user.name)
        user.phone = request.data.get('phone', user.phone)
        user.save()
        
        data = {
            'id': user.id,
            'full_name': user.name,
            'email': user.email,
            'phone': user.phone,
            'avatar_url': getattr(user, 'avatar_url', None),
            'role': user.role
        }
        return send_success('Profile updated successfully', data)

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        user = request.user
        old_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        
        if not check_password(old_password, user.password):
            return send_error('Incorrect current password', status_code=status.HTTP_400_BAD_REQUEST)

        if not new_password or len(new_password) < 8:
            return send_error('New password must be at least 8 characters long.', status_code=status.HTTP_400_BAD_REQUEST)
            
        user.password = make_password(new_password)
        user.save()
        return send_success('Password updated successfully')

class UserDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        vehicles = Vehicle.objects.filter(user=user).count()
        orders = Order.objects.filter(user=user)
        bookings = ServiceBooking.objects.filter(user=user)
        
        active_bookings = bookings.exclude(status__in=['completed', 'cancelled']).count()
        completed_bookings = bookings.filter(status='completed').count()
        
        data = {
            'vehicles_count': vehicles,
            'total_orders': orders.count(),
            'active_bookings': active_bookings,
            'completed_bookings': completed_bookings,
            'recent_activity': []
        }
        return send_success('Dashboard retrieved', data)

class AdminUserListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'ADMIN':
            return send_error('Access denied', status_code=status.HTTP_403_FORBIDDEN)
            
        users = User.objects.filter(role='USER')
        data = []
        for u in users:
            data.append({
                'id': u.id,
                'full_name': u.name,
                'email': u.email,
                'phone': u.phone,
                'is_active': u.is_active,
                'created_at': u.created_at,
                'orders_count': Order.objects.filter(user=u).count(),
                'bookings_count': ServiceBooking.objects.filter(user=u).count(),
                'vehicles_count': Vehicle.objects.filter(user=u).count(),
            })
        
        return send_success('Users retrieved', {'users': data, 'pagination': {'total': len(data), 'page': 1, 'pages': 1, 'limit': 100}})

class AdminUserDetailView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, id):
        if request.user.role != 'ADMIN':
            return send_error('Access denied', status_code=status.HTTP_403_FORBIDDEN)
            
        try:
            u = User.objects.get(id=id)
            return send_success('User retrieved', {
                'id': u.id,
                'full_name': u.name,
                'email': u.email,
                'phone': u.phone,
                'role': u.role,
                'is_active': u.is_active,
                'created_at': u.created_at,
                'vehicles': list(Vehicle.objects.filter(user=u).values()),
                'orders': list(Order.objects.filter(user=u).values('id', 'order_number', 'total_amount', 'order_status', 'created_at')),
                'bookings': list(ServiceBooking.objects.filter(user=u).values('id', 'booking_ref', 'status', 'booking_date'))
            })
        except User.DoesNotExist:
            return send_error('User not found', status_code=status.HTTP_404_NOT_FOUND)

class AdminUserStatusView(APIView):
    permission_classes = [IsAuthenticated]
    
    def put(self, request, id):
        if request.user.role != 'ADMIN':
            return send_error('Access denied', status_code=status.HTTP_403_FORBIDDEN)
            
        try:
            u = User.objects.get(id=id)
            is_active = request.data.get('is_active', u.is_active)
            if isinstance(is_active, str):
                is_active = is_active.lower() == 'true'
            u.is_active = is_active
            u.save()
            return send_success('User status updated')
        except User.DoesNotExist:
            return send_error('User not found', status_code=status.HTTP_404_NOT_FOUND)

class AddressSetDefaultView(APIView):
    permission_classes = [IsAuthenticated]
    
    def put(self, request, id):
        try:
            addr = Address.objects.get(id=id, user=request.user)
            Address.objects.filter(user=request.user).update(is_default=False)
            addr.is_default = True
            addr.save()
            return send_success('Address set as default')
        except Address.DoesNotExist:
            return send_error('Address not found', status_code=status.HTTP_404_NOT_FOUND)
