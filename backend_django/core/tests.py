import hmac
import hashlib
from decimal import Decimal
from django.test import TestCase, override_settings
from django.urls import resolve
from rest_framework.test import APIClient
from rest_framework import status
from .models import (
    User, Admin, Service, Product, ProductCategory, Order, OrderItem,
    Notification, ContactMessage, ServiceBooking, Payment, Address
)
from .user_views import UserProfileView
from .order_views import CheckoutView
from .notification_views import ReadAllNotificationView, ReadNotificationView
from .misc_views import ServiceCategoriesView
from .payment_views import is_mock_mode
from .auth_views import generate_token


class CodeIssuesRegressionTests(TestCase):
    """
    Regression tests for core issues identified in the initial project audit:
    - Custom URLs resolved before generic router.
    - Notification read operations using model's is_read field.
    - Anonymous access blocked on sensitive viewsets; data isolation between users.
    - Real backend flows for login, booking, and checkout.
    """

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
            price=Decimal('350.00'),
            stock_quantity=20,
            status='active'
        )
        self.service = Service.objects.create(
            name='Engine Diagnostics',
            category='Diagnostics',
            price=Decimal('800.00'),
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
        """Anonymous users must receive 401/403 for user, order, payment data."""
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
        Order.objects.create(
            order_number='ORD-111111',
            user=self.user1,
            subtotal=Decimal('350.00'),
            total_amount=Decimal('350.00')
        )
        Order.objects.create(
            order_number='ORD-222222',
            user=self.user2,
            subtotal=Decimal('700.00'),
            total_amount=Decimal('700.00')
        )

        self.client.force_authenticate(user=self.user1)
        res_orders = self.client.get('/api/orders')
        self.assertEqual(res_orders.status_code, status.HTTP_200_OK)
        order_list = res_orders.data.get('results', res_orders.data) if isinstance(res_orders.data, dict) else res_orders.data
        order_numbers = [o['order_number'] for o in order_list]
        self.assertIn('ORD-111111', order_numbers)
        self.assertNotIn('ORD-222222', order_numbers)

        res_users = self.client.get('/api/users')
        self.assertEqual(res_users.status_code, status.HTTP_200_OK)
        user_list = res_users.data.get('results', res_users.data) if isinstance(res_users.data, dict) else res_users.data
        user_ids = [u['id'] for u in user_list]
        self.assertIn(self.user1.id, user_ids)
        self.assertNotIn(self.user2.id, user_ids)

    # -------------------------------------------------------------------------
    # Issue 4 Test: Real backend flows for login, booking, checkout
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


class CheckoutSecurityAndPricingTests(TestCase):
    """
    Tests ensuring server-side pricing integrity, stock enforcement,
    concurrency controls, and promo code verification.
    """

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='customer@example.com',
            name='Test Customer',
            phone='9876543210',
            password='securePassword123!',
            role='USER'
        )
        self.category = ProductCategory.objects.create(name='Brakes', slug='brakes')
        self.product = Product.objects.create(
            name='Ceramic Brake Pads',
            sku='BRK-CER-001',
            category=self.category,
            brand='Bosch',
            price=Decimal('1200.00'),
            stock_quantity=10,
            status='active'
        )
        self.client.force_authenticate(user=self.user)

    def test_client_price_manipulation_is_ignored(self):
        """
        CRITICAL VULNERABILITY TEST:
        Client sends manipulated price (e.g. ₹1.00). The backend MUST look up
        the trusted price from the database (₹1200.00) and ignore client price.
        """
        payload = {
            'fullName': 'Test Customer',
            'email': 'customer@example.com',
            'phone': '9876543210',
            'address': '123 Market Road',
            'city': 'Ranchi',
            'state': 'Jharkhand',
            'pinCode': '834001',
            'items': [
                {
                    'product_id': self.product.id,
                    'quantity': 2,
                    'price': 1.00,  # Attacker attempt to buy for ₹1
                    'title': 'Ceramic Brake Pads'
                }
            ]
        }
        res = self.client.post('/api/orders/checkout', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        order = Order.objects.get(id=res.data['data']['order_id'])
        # Subtotal must be 2 * 1200.00 = 2400.00
        self.assertEqual(order.subtotal, Decimal('2400.00'))
        # Order >= 999 gets free shipping
        self.assertEqual(order.shipping_charge, Decimal('0.00'))
        # GST 18% of 2400 = 432.00
        self.assertEqual(order.tax_amount, Decimal('432.00'))
        # Total = 2400 + 432 = 2832.00 (NOT ₹2.00!)
        self.assertEqual(order.total_amount, Decimal('2832.00'))

    def test_fabricated_product_checkout_rejected(self):
        """
        CRITICAL VULNERABILITY TEST:
        Client cannot inject arbitrary, non-existent products into the database.
        """
        payload = {
            'fullName': 'Attacker',
            'email': 'attacker@example.com',
            'phone': '9876543210',
            'address': 'Unknown',
            'city': 'Unknown',
            'state': 'Jharkhand',
            'pinCode': '834001',
            'items': [
                {
                    'product_id': 999999,  # Does not exist
                    'quantity': 1,
                    'title': 'Fabricated Gold Spark Plug',
                    'price': 100.00
                }
            ]
        }
        res = self.client.post('/api/orders/checkout', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        # Ensure no product was created in the database
        self.assertFalse(Product.objects.filter(name='Fabricated Gold Spark Plug').exists())

    def test_insufficient_stock_rejection(self):
        """
        Checkout must reject orders requesting more stock than available.
        """
        payload = {
            'fullName': 'Test Customer',
            'email': 'customer@example.com',
            'phone': '9876543210',
            'address': '123 Market Road',
            'city': 'Ranchi',
            'state': 'Jharkhand',
            'pinCode': '834001',
            'items': [
                {
                    'product_id': self.product.id,
                    'quantity': 15,  # Only 10 in stock
                    'title': 'Ceramic Brake Pads'
                }
            ]
        }
        res = self.client.post('/api/orders/checkout', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Insufficient stock', res.data.get('message', ''))
        # Product stock should remain unchanged
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 10)

    def test_checkout_reduces_stock_atomically(self):
        """
        Successful checkout must atomically decrement product stock.
        """
        payload = {
            'fullName': 'Test Customer',
            'email': 'customer@example.com',
            'phone': '9876543210',
            'address': '123 Market Road',
            'city': 'Ranchi',
            'state': 'Jharkhand',
            'pinCode': '834001',
            'items': [
                {
                    'product_id': self.product.id,
                    'quantity': 3,
                    'title': 'Ceramic Brake Pads'
                }
            ]
        }
        res = self.client.post('/api/orders/checkout', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 7)  # 10 - 3 = 7

    def test_server_side_promo_code_calculation(self):
        """
        Promo codes must be calculated purely on the server.
        """
        # Subtotal for 2 items @ 1200 = 2400.
        # Promo code SAVE10 for subtotal >= 2000 gives flat 500 off.
        payload = {
            'fullName': 'Test Customer',
            'email': 'customer@example.com',
            'phone': '9876543210',
            'address': '123 Market Road',
            'city': 'Ranchi',
            'state': 'Jharkhand',
            'pinCode': '834001',
            'promo_code': 'SAVE10',
            'items': [
                {
                    'product_id': self.product.id,
                    'quantity': 2,
                    'title': 'Ceramic Brake Pads'
                }
            ]
        }
        res = self.client.post('/api/orders/checkout', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        order = Order.objects.get(id=res.data['data']['order_id'])
        self.assertEqual(order.promo_code, 'SAVE10')
        self.assertEqual(order.discount_amount, Decimal('500.00'))
        net = Decimal('2400.00') - Decimal('500.00')  # 1900.00
        tax = (net * Decimal('0.18')).quantize(Decimal('0.01'))  # 342.00
        self.assertEqual(order.total_amount, net + tax)

    def test_invalid_promo_code_rejected(self):
        """
        Invalid or fabricated promo code must be rejected with 400 Bad Request.
        """
        payload = {
            'fullName': 'Test Customer',
            'email': 'customer@example.com',
            'phone': '9876543210',
            'address': '123 Market Road',
            'city': 'Ranchi',
            'state': 'Jharkhand',
            'pinCode': '834001',
            'promo_code': 'FAKE_DISCOUNT_99',
            'items': [
                {
                    'product_id': self.product.id,
                    'quantity': 1,
                    'title': 'Ceramic Brake Pads'
                }
            ]
        }
        res = self.client.post('/api/orders/checkout', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid promo code', res.data.get('message', ''))

    def test_order_cancellation_restores_inventory(self):
        """
        Cancelling an order restores the items back into product stock.
        """
        order = Order.objects.create(
            order_number='ORD-CAN-001',
            user=self.user,
            subtotal=Decimal('2400.00'),
            total_amount=Decimal('2832.00'),
            order_status='pending'
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            product_name=self.product.name,
            quantity=3,
            unit_price=self.product.price,
            subtotal=Decimal('3600.00')
        )
        # Decrement stock simulating purchase
        self.product.stock_quantity = 7
        self.product.save()

        res = self.client.post(f'/api/orders/{order.id}/cancel')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        order.refresh_from_db()
        self.assertEqual(order.order_status, 'cancelled')
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 10)  # Restored 7 + 3 = 10


class PaymentSecurityTests(TestCase):
    """
    Tests payment authorization, digital signature validation,
    idempotency, and production mock-mode disabling.
    """

    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(
            email='payuser1@example.com',
            name='Payment User 1',
            phone='1234567890',
            password='password123',
            role='USER'
        )
        self.user2 = User.objects.create_user(
            email='payuser2@example.com',
            name='Payment User 2',
            phone='9876543210',
            password='password123',
            role='USER'
        )
        self.order1 = Order.objects.create(
            order_number='ORD-PAY-111',
            user=self.user1,
            subtotal=Decimal('1000.00'),
            total_amount=Decimal('1180.00'),
            order_status='pending',
            payment_status='pending'
        )
        self.client.force_authenticate(user=self.user1)

    @override_settings(DEBUG=True, PAYMENT_MOCK_MODE=True)
    def test_initiate_payment_order(self):
        """Initiating payment creates Payment record in 'created' state."""
        res = self.client.post('/api/payments/create-order', {'order_id': self.order1.id}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['success'])
        self.assertIn('razorpay_order_id', res.data['data'])
        self.assertTrue(Payment.objects.filter(order=self.order1).exists())

    @override_settings(DEBUG=False, PAYMENT_MOCK_MODE=False, RAZORPAY_KEY_SECRET='prod_secret_key_999')
    def test_payment_verification_valid_signature(self):
        """
        With real payment verification (non-mock), valid HMAC SHA256 signature
        must successfully confirm the order and mark payment as paid.
        """
        payment = Payment.objects.create(
            order=self.order1,
            user=self.user1,
            razorpay_order_id='order_real_12345',
            amount=self.order1.total_amount,
            currency='INR',
            status='created'
        )
        rzp_payment_id = 'pay_real_67890'
        msg = f"{payment.razorpay_order_id}|{rzp_payment_id}"
        valid_signature = hmac.new(
            b'prod_secret_key_999',
            msg.encode(),
            hashlib.sha256
        ).hexdigest()

        res = self.client.post('/api/payments/verify', {
            'razorpay_order_id': payment.razorpay_order_id,
            'razorpay_payment_id': rzp_payment_id,
            'razorpay_signature': valid_signature
        }, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['success'])

        payment.refresh_from_db()
        self.assertEqual(payment.status, 'paid')
        self.assertEqual(payment.razorpay_payment_id, rzp_payment_id)

        self.order1.refresh_from_db()
        self.assertEqual(self.order1.payment_status, 'paid')
        self.assertEqual(self.order1.order_status, 'confirmed')

    @override_settings(DEBUG=False, PAYMENT_MOCK_MODE=False, RAZORPAY_KEY_SECRET='prod_secret_key_999')
    def test_payment_verification_tampered_signature_rejected(self):
        """
        Payment verification with forged signature MUST be rejected with 400 Bad Request.
        """
        payment = Payment.objects.create(
            order=self.order1,
            user=self.user1,
            razorpay_order_id='order_real_12345',
            amount=self.order1.total_amount,
            currency='INR',
            status='created'
        )
        res = self.client.post('/api/payments/verify', {
            'razorpay_order_id': payment.razorpay_order_id,
            'razorpay_payment_id': 'pay_fake_999',
            'razorpay_signature': 'tampered_invalid_signature_hex'
        }, format='json')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid digital signature', res.data.get('message', ''))

        payment.refresh_from_db()
        self.assertEqual(payment.status, 'created')  # Not paid!

    def test_payment_verification_idempotent(self):
        """
        Re-verifying an already paid payment must be idempotent and return success safely.
        """
        payment = Payment.objects.create(
            order=self.order1,
            user=self.user1,
            razorpay_order_id='order_already_paid_123',
            razorpay_payment_id='pay_already_paid_456',
            amount=self.order1.total_amount,
            currency='INR',
            status='paid'
        )
        self.order1.payment_status = 'paid'
        self.order1.save()

        res = self.client.post('/api/payments/verify', {
            'razorpay_order_id': payment.razorpay_order_id,
            'razorpay_payment_id': payment.razorpay_payment_id,
            'razorpay_signature': 'any_sig'
        }, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['success'])
        self.assertIn('already verified', res.data.get('message', ''))

    @override_settings(DEBUG=False)
    def test_mock_mode_strictly_disabled_in_production(self):
        """Mock payment mode must return False when DEBUG is False."""
        self.assertFalse(is_mock_mode())

    def test_cross_user_payment_access_forbidden(self):
        """User 2 cannot verify or access User 1's payment."""
        payment = Payment.objects.create(
            order=self.order1,
            user=self.user1,
            razorpay_order_id='order_secret_111',
            amount=self.order1.total_amount,
            currency='INR',
            status='created'
        )
        self.client.force_authenticate(user=self.user2)
        res = self.client.post('/api/payments/verify', {
            'razorpay_order_id': payment.razorpay_order_id,
            'razorpay_payment_id': 'pay_123',
            'razorpay_signature': 'sig'
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AuthenticationAndAuthorizationTests(TestCase):
    """
    Tests JWT validation, account suspension, role-based access control,
    and direct object reference protections.
    """

    def setUp(self):
        self.client = APIClient()
        self.customer = User.objects.create_user(
            email='regular@example.com',
            name='Regular User',
            phone='1234567890',
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

    def test_invalid_jwt_token_rejected(self):
        """Corrupted or invalid JWT bearer token returns 401 Unauthorized."""
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid.garbage.token')
        res = self.client.get('/api/users/profile')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_deactivated_user_cannot_access_api(self):
        """Deactivated account (is_active=False) cannot access protected endpoints."""
        token = generate_token(self.customer)
        self.customer.is_active = False
        self.customer.save()

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        res = self.client.get('/api/users/profile')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admin_endpoints_forbidden_for_regular_user(self):
        """Regular user cannot access admin-only endpoints."""
        self.client.force_authenticate(user=self.customer)
        res1 = self.client.get('/api/admin/dashboard')
        self.assertEqual(res1.status_code, status.HTTP_403_FORBIDDEN)

        res2 = self.client.get('/api/admins')
        self.assertEqual(res2.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_user_can_access_admin_endpoints(self):
        """Admin user can successfully access admin-only endpoints."""
        self.client.force_authenticate(user=self.admin)
        res = self.client.get('/api/admin/dashboard')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['success'])

    def test_address_isolation_between_users(self):
        """User cannot access or delete another user's address."""
        addr1 = Address.objects.create(
            user=self.customer,
            full_name='Customer Address',
            phone='1234567890',
            address_line='123 Street',
            city='Ranchi',
            state='Jharkhand',
            pincode='834001'
        )
        other_user = User.objects.create_user(
            email='other@example.com',
            name='Other User',
            phone='5555555555',
            password='password123',
            role='USER'
        )
        self.client.force_authenticate(user=other_user)
        res = self.client.get(f'/api/addresses/{addr1.id}')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
