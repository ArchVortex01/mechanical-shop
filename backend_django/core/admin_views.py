from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db.models import Sum, Count, Q
from .models import User, Order, ServiceBooking, Product, ContactMessage
from .auth_views import send_success, send_error

class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if request.user.role != 'ADMIN':
            return send_error('Access denied.', status_code=status.HTTP_403_FORBIDDEN)
            
        # User Stats
        users = User.objects.filter(role='USER')
        total_users = users.count()
        active_users = users.filter(is_active=True).count()
        
        # Order Stats
        orders = Order.objects.all()
        total_orders = orders.count()
        total_revenue = sum(float(o.total_amount) for o in orders if o.payment_status == 'paid')
        pending_orders = orders.filter(order_status='pending').count()
        delivered_orders = orders.filter(order_status='delivered').count()
        
        # Booking Stats
        bookings = ServiceBooking.objects.all()
        total_bookings = bookings.count()
        pending_bookings = bookings.filter(status='pending').count()
        completed_bookings = bookings.filter(status='completed').count()
        
        # Inventory Stats
        products = Product.objects.filter(status='active')
        total_products = products.count()
        low_stock_products = products.filter(stock_quantity__lte=5, stock_quantity__gt=0).count()
        out_of_stock_products = products.filter(stock_quantity=0).count()
        
        # Messages Stats
        messages = ContactMessage.objects.all()
        total_messages = messages.count()
        unread_messages = messages.filter(status='unread').count()
        
        # Recent
        recent_orders = orders.select_related('user').order_by('-created_at')[:5]
        recent_bookings = bookings.select_related('user', 'service').order_by('-created_at')[:5]
        
        recent_orders_list = [{
            'id': o.id, 'order_number': o.order_number, 'total_amount': float(o.total_amount),
            'order_status': o.order_status, 'payment_status': o.payment_status,
            'created_at': o.created_at, 'customer_name': o.user.name, 'customer_email': o.user.email
        } for o in recent_orders]
        
        recent_bookings_list = [{
            'id': b.id, 'booking_ref': b.booking_ref, 'booking_date': b.booking_date,
            'booking_time': b.booking_time, 'status': b.status, 'estimated_cost': float(b.estimated_cost),
            'service_name': b.service.name, 'customer_name': b.user.name, 'customer_phone': b.user.phone
        } for b in recent_bookings]
        
        return send_success('Admin dashboard statistics retrieved', {
            'overview': {
                'total_users': total_users,
                'active_users': active_users,
                'total_revenue': float("{:.2f}".format(total_revenue)),
                'total_orders': total_orders,
                'pending_orders': pending_orders,
                'delivered_orders': delivered_orders,
                'total_bookings': total_bookings,
                'pending_bookings': pending_bookings,
                'completed_bookings': completed_bookings,
                'total_products': total_products,
                'low_stock_products': low_stock_products,
                'unread_messages': unread_messages
            },
            'breakdowns': {
                'orders': {
                    'total_orders': total_orders,
                    'total_revenue': float("{:.2f}".format(total_revenue)),
                    'pending_orders': pending_orders,
                    'processing_orders': orders.filter(order_status='processing').count(),
                    'shipped_orders': orders.filter(order_status='shipped').count(),
                    'delivered_orders': delivered_orders,
                    'cancelled_orders': orders.filter(order_status='cancelled').count()
                },
                'bookings': {
                    'total_bookings': total_bookings,
                    'pending_bookings': pending_bookings,
                    'confirmed_bookings': bookings.filter(status='confirmed').count(),
                    'in_progress_bookings': bookings.filter(status='in_progress').count(),
                    'completed_bookings': completed_bookings,
                    'cancelled_bookings': bookings.filter(status='cancelled').count()
                },
                'inventory': {
                    'total_products': total_products,
                    'low_stock_products': low_stock_products,
                    'out_of_stock_products': out_of_stock_products
                }
            },
            'recent_orders': recent_orders_list,
            'recent_bookings': recent_bookings_list
        })
