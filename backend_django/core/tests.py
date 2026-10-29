from django.test import TestCase
from django.urls import resolve
from rest_framework.test import APIClient
from rest_framework import status
from .models import User, Admin, Service, Product, ProductCategory, Order, Notification, ContactMessage, ServiceBooking
from .user_views import UserProfileView
from .order_views import CheckoutView
from .notification_views import ReadAllNotificationView, ReadNotificationView
from .misc_views import ServiceCategoriesView

class CodeIssuesRegressionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            name='User One',
            phone='1111111111',
            password='password123',
            role='USER'
        )
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            name='User Two',
            phone='2222222222',
            password='password123',
            role='USER'
        )
        self.admin = User.objects.create_user(
            email='admin@example.com',
            name='Admin User',
            phone='9999999999',
            password='password123',
            role='ADMIN'
        )
        Admin.objects.create(user=self.admin)

        self.category = ProductCategory.objects.create(name='Engine Parts', slug='engine-parts')
        self.product = Product.objects.create(
            name='Spark Plug',
            sku='SP-101',
            category=self.category,
            brand='NGK',
            price=350.00,
            stock_quantity=20,
            status='active'
        )
        self.service = Service.objects.create(
            name='Engine Diagnostics',
            category='Diagnostics',
            price=800.00,
            status='active'
        )

    # -------------------------------------------------------------------------
    # Issue 2 Test: Custom URLs resolved before generic router
    # -------------------------------------------------------------------------
    def test_url_resolutions_reach_intended_views(self):
        """Ensure /api/users/profile, /api/orders/checkout, etc., reach custom views, not ViewSets with pk."""
        self.assertEqual(resolve('/api/users/profile').func.view_class, UserProfileView)
        self.assertEqual(resolve('/api/orders/checkout').func.view_class, CheckoutView)
        self.assertEqual(resolve('/api/notifications/read-all').func.view_class, ReadAllNotificationView)
        self.assertEqual(resolve('/api/notifications/1/read').func.view_class, ReadNotificationView)
        self.assertEqual(resolve('/api/services/categories').func.view_class, ServiceCategoriesView)

    # -------------------------------------------------------------------------
    # Issue 3 Test: Notification read & read-all use is_read without crashing
    # -------------------------------------------------------------------------
    def test_notification_mark_read_and_read_all(self):
        """Ensure notification mark-read uses model's is_read field and does not crash."""
        n1 = Notification.objects.create(
            user=self.user1,
            title='Order Update',
            message='Order shipped',
            type='order',
            is_read=False
        )
        n2 = Notification.objects.create(
            user=self.user1,
            title='Service Reminder',
            message='Due tomorrow',
            type='booking',
            is_read=False
        )

        self.client.force_authenticate(user=self.user1)

        # Mark single notification as read
        res1 = self.client.put(f'/api/notifications/{n1.id}/read')
        self.assertEqual(res1.status_code, status.HTTP_200_OK)
        n1.refresh_from_db()
        self.assertTrue(n1.is_read)

        # Mark all notifications as read
        res2 = self.client.put('/api/notifications/read-all')
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        n2.refresh_from_db()
        self.assertTrue(n2.is_read)

    # -------------------------------------------------------------------------
    # Issue 5 Test: Anonymous access blocked on sensitive viewsets; user isolation
    # -------------------------------------------------------------------------
    def test_anonymous_access_to_sensitive_data_blocked(self):
        """Anonymous users must receive 401 Unauthorized for user, order, payment data."""
        endpoints = [
            '/api/users',
            '/api/admins',
            '/api/orders',
            '/api/payments',
            '/api/addresses',
            '/api/vehicles',
            '/api/notifications',
            '/api/contact',  # GET is admin-only
        ]
        for ep in endpoints:
            res = self.client.get(ep)
            self.assertIn(res.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
                          f"Endpoint {ep} allowed unauthorized access (status {res.status_code})")

    def test_public_endpoints_accessible(self):
        """Services and products must be publicly readable; contact form publicly submittable."""
        res_svc = self.client.get('/api/services')
        self.assertEqual(res_svc.status_code, status.HTTP_200_OK)

        res_prod = self.client.get('/api/products')
        self.assertEqual(res_prod.status_code, status.HTTP_200_OK)

        res_contact = self.client.post('/api/contact', {
            'name': 'Visitor',
            'email': 'visitor@example.com',
            'phone': '1234567890',
            'subject': 'Inquiry',
            'category': 'General Inquiry',
            'message': 'Hello there'
        }, format='json')
        self.assertEqual(res_contact.status_code, status.HTTP_201_CREATED)

    def test_user_data_isolation(self):
        """Normal user can only see their own orders and user profile, not other users' data."""
        order1 = Order.objects.create(
            order_number='ORD-111111',
            user=self.user1,
            subtotal=350,
            total_amount=350
        )
        order2 = Order.objects.create(
            order_number='ORD-222222',
            user=self.user2,
            subtotal=700,
            total_amount=700
        )

        self.client.force_authenticate(user=self.user1)
        res_orders = self.client.get('/api/orders')
        self.assertEqual(res_orders.status_code, status.HTTP_200_OK)
        order_numbers = [o['order_number'] for o in res_orders.data]
        self.assertIn('ORD-111111', order_numbers)
        self.assertNotIn('ORD-222222', order_numbers)

        res_users = self.client.get('/api/users')
        self.assertEqual(res_users.status_code, status.HTTP_200_OK)
        user_ids = [u['id'] for u in res_users.data]
        self.assertIn(self.user1.id, user_ids)
        self.assertNotIn(self.user2.id, user_ids)

    # -------------------------------------------------------------------------
    # Issue 4 Test: Real backend flows for login, booking, checkout, contact
    # -------------------------------------------------------------------------
    def test_login_flow(self):
        """Login endpoint returns user info and JWT token for valid credentials."""
        res = self.client.post('/api/auth/login', {
            'email': 'user1@example.com',
            'password': 'password123'
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['success'])
        self.assertIn('token', res.data['data'])
        self.assertEqual(res.data['data']['user']['email'], 'user1@example.com')

    def test_booking_flow(self):
        """Booking endpoint creates a valid service booking."""
        res = self.client.post('/api/bookings', {
            'cust_name': 'Ramesh Kumar',
            'cust_phone': '9876543210',
            'cust_email': 'ramesh@example.com',
            'vehicle_model': 'Hyundai i20',
            'vehicle_reg': 'JH 01 AB 9999',
            'service_type': 'Engine Diagnostics',
            'booking_date': '2026-11-01',
            'booking_time': '10:00 AM'
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(res.data['success'])
        self.assertTrue(ServiceBooking.objects.filter(booking_ref=res.data['data']['booking_ref']).exists())

    def test_checkout_flow(self):
        """Checkout endpoint creates a valid order."""
        res = self.client.post('/api/orders/checkout', {
            'fullName': 'Ramesh Kumar',
            'email': 'ramesh@example.com',
            'phone': '9876543210',
            'address': 'Main Road, Ramgarh',
            'city': 'Ramgarh',
            'state': 'Jharkhand',
            'pinCode': '829122',
            'items': [
                {'product_id': self.product.id, 'quantity': 2, 'title': 'Spark Plug', 'price': 350}
            ]
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(res.data['success'])
        order_number = res.data['data']['order_number']
        self.assertTrue(Order.objects.filter(order_number=order_number).exists())
