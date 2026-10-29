import time
import random
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from django.db import transaction
from django.db.models import Q
from .models import ServiceBooking, Service, Vehicle, Notification, ServiceHistory, User
from .auth_views import send_success, send_error
from .email_utils import send_booking_confirmation_email

def generate_booking_ref():
    timestamp = str(int(time.time() * 1000))[-6:]
    rand_val = random.randint(1000, 9999)
    return f"MM-BKG-{timestamp}-{rand_val}"

class BookingListView(APIView):
    def get_permissions(self):
        if self.request.method == 'POST':
            return [AllowAny()]
        return [IsAuthenticated()]
    
    def get(self, request):
        bookings = ServiceBooking.objects.filter(user=request.user).order_by('-created_at')
        from .serializers import ServiceBookingSerializer
        return send_success('User bookings retrieved successfully', ServiceBookingSerializer(bookings, many=True).data)
        
    @transaction.atomic
    def post(self, request):
        data = request.data
        if request.user and request.user.is_authenticated:
            user = request.user
        else:
            cust_email = (data.get('cust_email') or data.get('email') or '').strip().lower()
            cust_phone = (data.get('cust_phone') or data.get('phone') or '').strip()
            cust_name = data.get('cust_name') or data.get('name') or 'Customer'
            
            if not cust_email:
                cust_email = f"guest_{int(time.time())}_{random.randint(1000, 9999)}@mahtomech.com"
            
            user = User.objects.filter(email=cust_email).first()
            if not user:
                user = User.objects.create_user(
                    email=cust_email,
                    name=cust_name,
                    phone=cust_phone,
                    password=None,
                    role='USER'
                )

        service_id = data.get('service_id')
        service_type = data.get('service_type') or data.get('service_name')
        service = None
        if service_id:
            service = Service.objects.filter(id=service_id, status='active').first()
        if not service and service_type:
            service = Service.objects.filter(name__iexact=service_type, status='active').first()
            if not service:
                service = Service.objects.filter(name__icontains=service_type, status='active').first()
        if not service:
            service = Service.objects.filter(status='active').first()
        if not service:
            service = Service.objects.create(name=service_type or 'General Servicing', price=1500.00, status='active')
            
        vehicle = None
        vehicle_id = data.get('vehicle_id')
        if vehicle_id:
            vehicle = Vehicle.objects.filter(id=vehicle_id, user=user).first()
        if not vehicle and (data.get('vehicle_model') or data.get('vehicle_reg')):
            vehicle_reg = (data.get('vehicle_reg') or '').strip().upper()
            if not vehicle_reg:
                vehicle_reg = f"TEMP-{int(time.time())}-{random.randint(100, 999)}"
            vehicle = Vehicle.objects.filter(registration_number=vehicle_reg).first()
            if not vehicle:
                vehicle = Vehicle.objects.create(
                    user=user,
                    vehicle_type=data.get('vehicle_type', 'Car'),
                    brand=data.get('vehicle_brand', data.get('vehicle_model', 'Vehicle')),
                    model=data.get('vehicle_model', 'Vehicle'),
                    registration_number=vehicle_reg
                )
                
        booking = ServiceBooking.objects.create(
            booking_ref=generate_booking_ref(),
            user=user,
            vehicle=vehicle,
            service=service,
            booking_date=data.get('booking_date'),
            booking_time=data.get('booking_time', '10:00 AM'),
            problem_description=data.get('problem_description'),
            pickup_option=data.get('pickup_option', 'self'),
            status='pending',
            estimated_cost=service.price
        )
        
        Notification.objects.create(
            user=user,
            title='Booking Submitted',
            message=f'Your booking for {service.name} has been received (Ref: {booking.booking_ref}). Our service manager will confirm shortly.',
            type='booking'
        )
        
        # Async-like email send (synchronous for now, but fails gracefully)
        send_booking_confirmation_email(user.email, booking)
        
        from .serializers import ServiceBookingSerializer
        return send_success('Service booking submitted successfully', ServiceBookingSerializer(booking).data, status_code=status.HTTP_201_CREATED)

class BookingDetailView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, id_or_ref):
        user = request.user
        is_admin = user.role == 'ADMIN'
        
        try:
            if str(id_or_ref).isdigit():
                booking = ServiceBooking.objects.get(Q(id=id_or_ref) | Q(booking_ref=id_or_ref))
            else:
                booking = ServiceBooking.objects.get(booking_ref=id_or_ref)
        except ServiceBooking.DoesNotExist:
            return send_error('Booking not found or access denied.', status_code=status.HTTP_404_NOT_FOUND)
            
        if not is_admin and booking.user_id != user.id:
            return send_error('Booking not found or access denied.', status_code=status.HTTP_404_NOT_FOUND)
            
        from .serializers import ServiceBookingSerializer
        return send_success('Booking retrieved successfully', ServiceBookingSerializer(booking).data)

class BookingCancelView(APIView):
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def put(self, request, id):
        try:
            booking = ServiceBooking.objects.get(id=id, user=request.user)
        except ServiceBooking.DoesNotExist:
            return send_error('Booking not found or does not belong to you.', status_code=status.HTTP_404_NOT_FOUND)
            
        if booking.status == 'completed':
            return send_error('Cannot cancel a completed service booking.', status_code=status.HTTP_400_BAD_REQUEST)
        if booking.status == 'cancelled':
            return send_error('This booking has already been cancelled.', status_code=status.HTTP_400_BAD_REQUEST)
        if booking.status == 'in_progress':
            return send_error('Cannot cancel a service that is currently in progress. Please contact the workshop.', status_code=status.HTTP_400_BAD_REQUEST)
            
        booking.status = 'cancelled'
        booking.save()
        
        Notification.objects.create(
            user=request.user,
            title='Booking Cancelled',
            message=f'Booking {booking.booking_ref} has been cancelled.',
            type='booking'
        )
        
        return send_success('Booking cancelled successfully', {'id': booking.id, 'status': 'cancelled'})

class AdminBookingListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if request.user.role != 'ADMIN':
            return send_error('Access denied.', status_code=status.HTTP_403_FORBIDDEN)
            
        bookings = ServiceBooking.objects.all().order_by('-booking_date', '-booking_time')
        
        # We could add filtering logic for status, date, search here
        
        from .serializers import ServiceBookingSerializer
        return send_success('Bookings retrieved successfully', {
            'bookings': ServiceBookingSerializer(bookings, many=True).data
        })

class AdminBookingStatusView(APIView):
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def put(self, request, id):
        if request.user.role != 'ADMIN':
            return send_error('Access denied.', status_code=status.HTTP_403_FORBIDDEN)
            
        try:
            booking = ServiceBooking.objects.get(id=id)
        except ServiceBooking.DoesNotExist:
            return send_error('Booking not found.', status_code=status.HTTP_404_NOT_FOUND)
            
        new_status = request.data.get('status', booking.status)
        estimated_cost = request.data.get('estimated_cost', booking.estimated_cost)
        admin_notes = request.data.get('admin_notes', booking.admin_notes)
        
        booking.status = new_status
        booking.estimated_cost = estimated_cost
        booking.admin_notes = admin_notes
        booking.save()
        
        if new_status == 'completed':
            ServiceHistory.objects.get_or_create(
                booking=booking,
                defaults={
                    'user': booking.user,
                    'vehicle': booking.vehicle,
                    'service': booking.service,
                    'service_date': booking.booking_date,
                    'notes': admin_notes or 'Service successfully completed',
                    'final_cost': estimated_cost
                }
            )
            
        Notification.objects.create(
            user=booking.user,
            title=f'Booking Status Updated: {new_status.upper()}',
            message=f'Your booking ({booking.booking_ref}) status has been updated to "{new_status}".',
            type='booking'
        )
        
        from .serializers import ServiceBookingSerializer
        return send_success('Booking status updated successfully', ServiceBookingSerializer(booking).data)
