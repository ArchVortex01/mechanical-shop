import razorpay
import hmac
import hashlib
import time
import random
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db import transaction
from .models import Order, Payment, Notification
from .auth_views import send_success, send_error

def is_mock_mode():
    key = getattr(settings, 'RAZORPAY_KEY_ID', 'rzp_test_placeholder')
    return not key or key == 'rzp_test_placeholder' or key == 'rzp_test_mock_key'

def get_razorpay_client():
    if not is_mock_mode():
        return razorpay.Client(auth=(
            getattr(settings, 'RAZORPAY_KEY_ID', ''),
            getattr(settings, 'RAZORPAY_KEY_SECRET', '')
        ))
    return None

class CreatePaymentOrderView(APIView):
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def post(self, request):
        user = request.user
        order_id = request.data.get('order_id')
        
        if not order_id:
            return send_error('Order ID is required.', status_code=status.HTTP_400_BAD_REQUEST)
            
        try:
            order = Order.objects.get(id=order_id, user=user)
        except Order.DoesNotExist:
            return send_error('Order not found or access denied.', status_code=status.HTTP_400_BAD_REQUEST)
            
        if order.payment_status == 'paid':
            return send_error('This order has already been paid for.', status_code=status.HTTP_400_BAD_REQUEST)
            
        amount_in_paise = int(float(order.total_amount) * 100)
        
        if not is_mock_mode():
            client = get_razorpay_client()
            rzp_order = client.order.create({
                'amount': amount_in_paise,
                'currency': 'INR',
                'receipt': str(order.order_number)[:40],
                'notes': {
                    'orderId': str(order.id),
                    'userId': str(user.id),
                    'orderNumber': order.order_number
                }
            })
            razorpay_order_id = rzp_order['id']
        else:
            razorpay_order_id = f"order_sim_{int(time.time()*1000)}_{random.randint(1000,9999)}"
            
        payment, created = Payment.objects.get_or_create(
            order=order,
            status='created',
            defaults={
                'user': user,
                'razorpay_order_id': razorpay_order_id,
                'amount': order.total_amount,
                'currency': 'INR'
            }
        )
        
        if not created:
            payment.razorpay_order_id = razorpay_order_id
            payment.amount = order.total_amount
            payment.save()
            
        return send_success('Payment order initiated', {
            'razorpay_order_id': razorpay_order_id,
            'amount': amount_in_paise,
            'currency': 'INR',
            'key_id': getattr(settings, 'RAZORPAY_KEY_ID', 'rzp_test_placeholder'),
            'order_id': order.id,
            'order_number': order.order_number,
            'mock_mode': is_mock_mode()
        })

class VerifyPaymentView(APIView):
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def post(self, request):
        user = request.user
        data = request.data
        razorpay_order_id = data.get('razorpay_order_id')
        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_signature = data.get('razorpay_signature')
        payment_method = data.get('payment_method', 'online')
        
        if not razorpay_order_id or not razorpay_payment_id:
            return send_error('razorpay_order_id and razorpay_payment_id are required.', status_code=status.HTTP_400_BAD_REQUEST)
            
        if not is_mock_mode():
            secret = getattr(settings, 'RAZORPAY_KEY_SECRET', '')
            msg = f"{razorpay_order_id}|{razorpay_payment_id}"
            expected_signature = hmac.new(
                secret.encode(),
                msg.encode(),
                hashlib.sha256
            ).hexdigest()
            
            if expected_signature != razorpay_signature:
                return send_error('Payment verification failed: Invalid digital signature.', status_code=status.HTTP_400_BAD_REQUEST)
                
        try:
            payment = Payment.objects.select_for_update().get(razorpay_order_id=razorpay_order_id)
        except Payment.DoesNotExist:
            return send_error('Payment record not found for this transaction.', status_code=status.HTTP_400_BAD_REQUEST)
            
        payment.razorpay_payment_id = razorpay_payment_id
        payment.razorpay_signature = razorpay_signature or 'simulated_signature'
        payment.payment_method = payment_method
        payment.status = 'paid'
        payment.save()
        
        order = payment.order
        order.payment_status = 'paid'
        if order.order_status == 'pending':
            order.order_status = 'confirmed'
        order.save()
        
        Notification.objects.create(
            user=payment.user,
            title='Payment Received',
            message=f'Payment of ₹{payment.amount} has been successfully verified (Txn: {razorpay_payment_id}).',
            type='order'
        )
        
        return send_success('Payment verified successfully', {
            'success': True,
            'order_id': order.id,
            'razorpay_payment_id': razorpay_payment_id,
            'status': 'paid'
        })

class RecordFailureView(APIView):
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def post(self, request):
        order_id = request.data.get('order_id')
        error_description = request.data.get('error_description', 'Payment cancelled by user')
        
        if not order_id:
            return send_error('Order ID is required.', status_code=status.HTTP_400_BAD_REQUEST)
            
        Payment.objects.filter(order_id=order_id, status='created').update(
            status='failed',
            error_description=error_description
        )
        Order.objects.filter(id=order_id).update(payment_status='failed')
        
        return send_success('Payment failure recorded')

class OrderPaymentDetailView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, order_id):
        user = request.user
        is_admin = user.role == 'ADMIN'
        
        payments = Payment.objects.filter(order_id=order_id)
        if not is_admin:
            payments = payments.filter(user=user)
            
        payment = payments.order_by('-id').first()
        if not payment:
            return send_error('No payment record found for this order.', status_code=status.HTTP_404_NOT_FOUND)
            
        from .serializers import PaymentSerializer
        return send_success('Payment record retrieved', PaymentSerializer(payment).data)
