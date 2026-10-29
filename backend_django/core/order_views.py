import uuid
import time
from decimal import Decimal
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db import transaction
from django.utils import timezone
from .models import Cart, CartItem, Product, ProductCategory, Order, OrderItem, Address, Notification, User
from .auth_views import send_success, send_error
from .serializers import OrderSerializer

def generate_order_number():
    return 'ORD-' + str(uuid.uuid4().hex)[:10].upper()

class CheckoutView(APIView):
    def get_permissions(self):
        if self.request.method == 'POST':
            return [AllowAny()]
        return [IsAuthenticated()]

    @transaction.atomic
    def post(self, request):
        data = request.data or {}

        # 1. Identify or create customer securely
        if request.user and request.user.is_authenticated:
            user = request.user
        else:
            email = (data.get('email') or '').lower().strip()
            phone = (data.get('phone') or '').strip()
            full_name = (data.get('fullName') or data.get('full_name') or 'Customer').strip()

            if not email or '@' not in email or '.' not in email:
                return send_error('A valid email address is required for checkout.', status_code=status.HTTP_400_BAD_REQUEST)
            if not phone or len(phone) < 10:
                return send_error('A valid phone number (at least 10 digits) is required.', status_code=status.HTTP_400_BAD_REQUEST)

            user = User.objects.filter(email=email).first()
            if not user:
                user = User.objects.create_user(
                    email=email,
                    name=full_name,
                    phone=phone,
                    password=None,
                    role='USER'
                )

        # 2. Shipping Address resolution / creation
        address_id = data.get('address_id')
        address = None
        if address_id:
            try:
                address = Address.objects.get(id=address_id, user=user)
            except Address.DoesNotExist:
                return send_error('Selected shipping address not found or does not belong to your account.', status_code=status.HTTP_400_BAD_REQUEST)

        if not address and (data.get('address') or data.get('streetAddress')):
            street = (data.get('address') or data.get('streetAddress') or '').strip()
            city = (data.get('city') or '').strip()
            state = (data.get('state') or '').strip()
            pincode = (data.get('pinCode') or data.get('pincode') or '').strip()

            if not street or not city or not state or not pincode:
                return send_error('Street address, city, state, and pin code are required.', status_code=status.HTTP_400_BAD_REQUEST)

            address = Address.objects.create(
                user=user,
                full_name=(data.get('fullName') or data.get('full_name') or user.name).strip(),
                phone=(data.get('phone') or user.phone).strip(),
                address_line=street,
                city=city,
                state=state,
                pincode=pincode,
                landmark=(data.get('landmark') or '').strip()
            )

        # 3. Synchronize Cart Items from database or client payload
        cart, _ = Cart.objects.get_or_create(user=user)
        existing_items = CartItem.objects.filter(cart=cart)

        # If database cart is empty, ingest validated client items
        if not existing_items.exists() and data.get('items'):
            client_items = data.get('items')
            if not isinstance(client_items, list):
                return send_error('Invalid items format.', status_code=status.HTTP_400_BAD_REQUEST)

            for it in client_items:
                pid = it.get('product_id') or it.get('id')
                sku = it.get('sku')
                title = (it.get('title') or it.get('name') or '').strip()

                product = None
                if pid:
                    product = Product.objects.filter(id=pid, status='active').first()
                if not product and sku:
                    product = Product.objects.filter(sku=sku, status='active').first()
                if not product and title:
                    product = Product.objects.filter(name__iexact=title, status='active').first()

                if not product:
                    return send_error(
                        f"Product '{title or pid or sku}' does not exist in catalog or is inactive. You cannot checkout unverified items.",
                        status_code=status.HTTP_400_BAD_REQUEST
                    )

                try:
                    qty = int(it.get('quantity') or it.get('qty', 1))
                except (ValueError, TypeError):
                    return send_error('Invalid item quantity.', status_code=status.HTTP_400_BAD_REQUEST)

                if qty < 1 or qty > 50:
                    return send_error(f"Quantity for {product.name} must be between 1 and 50 units.", status_code=status.HTTP_400_BAD_REQUEST)

                CartItem.objects.get_or_create(cart=cart, product=product, defaults={'quantity': qty})

        # Fetch active cart items with row locking on products to prevent overselling
        cart_items = list(CartItem.objects.filter(cart=cart).select_related('product'))
        if not cart_items:
            return send_error('Your cart is empty. Please add items before checking out.', status_code=status.HTTP_400_BAD_REQUEST)

        # 4. Strict Server-side stock verification and price calculation (ignoring client prices)
        subtotal = Decimal('0.00')
        locked_items = []

        for item in cart_items:
            # Row-lock product to avoid race conditions
            product = Product.objects.select_for_update().get(id=item.product_id)

            if product.status != 'active':
                return send_error(f'Product "{product.name}" is currently unavailable.', status_code=status.HTTP_400_BAD_REQUEST)

            if item.quantity < 1 or item.quantity > 50:
                return send_error(f'Invalid quantity for "{product.name}". Must be between 1 and 50.', status_code=status.HTTP_400_BAD_REQUEST)

            if product.stock_quantity < item.quantity:
                return send_error(
                    f'Insufficient stock for "{product.name}". Requested {item.quantity}, but only {product.stock_quantity} available.',
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            item_subtotal = Decimal(str(product.price)) * item.quantity
            subtotal += item_subtotal
            locked_items.append((product, item.quantity, item_subtotal))

        # 5. Server-Side Discount & Promotion Calculation
        promo_code = (data.get('promo_code') or data.get('promoCode') or '').strip().upper()
        discount_amount = Decimal('0.00')

        if promo_code:
            if promo_code in ('SAVE10', 'MAHTO10'):
                if subtotal >= Decimal('2000.00'):
                    discount_amount = Decimal('500.00')
                else:
                    discount_amount = (subtotal * Decimal('0.10')).quantize(Decimal('0.01'))
            else:
                return send_error(f"Invalid promo code '{promo_code}'.", status_code=status.HTTP_400_BAD_REQUEST)

        discount_amount = min(discount_amount, subtotal)
        net_subtotal = subtotal - discount_amount

        # Shipping: Free for orders >= 999 else 99
        shipping_charge = Decimal('0.00') if net_subtotal >= Decimal('999.00') else Decimal('99.00')
        # 18% GST tax
        tax_amount = (net_subtotal * Decimal('0.18')).quantize(Decimal('0.01'))
        total_amount = net_subtotal + shipping_charge + tax_amount

        # 6. Idempotency & Duplicate Order Guard (5-second window for identical order)
        recent_cutoff = timezone.now() - timezone.timedelta(seconds=5)
        recent_order = Order.objects.filter(
            user=user,
            total_amount=total_amount,
            order_status='pending',
            created_at__gte=recent_cutoff
        ).first()

        if recent_order:
            return send_success('Order already received', {
                'order_id': recent_order.id,
                'order_number': recent_order.order_number,
                'total_amount': float(recent_order.total_amount)
            }, status_code=status.HTTP_200_OK)

        # 7. Create Order & OrderItems
        order = Order.objects.create(
            order_number=generate_order_number(),
            user=user,
            address=address,
            subtotal=subtotal,
            shipping_charge=shipping_charge,
            tax_amount=tax_amount,
            discount_amount=discount_amount,
            total_amount=total_amount,
            promo_code=promo_code or None,
            payment_status='pending',
            order_status='pending'
        )

        for product, quantity, line_subtotal in locked_items:
            OrderItem.objects.create(
                order=order,
                product=product,
                product_name=product.name,
                product_sku=product.sku,
                unit_price=product.price,
                quantity=quantity,
                subtotal=line_subtotal
            )

            # Deduct inventory atomically
            product.stock_quantity -= quantity
            product.save(update_fields=['stock_quantity', 'updated_at'])

        # Clear cart upon successful order creation
        CartItem.objects.filter(cart=cart).delete()

        # Customer Notification
        Notification.objects.create(
            user=user,
            title='Order Placed Successfully',
            message=f'Your order {order.order_number} has been placed for ₹{order.total_amount}.',
            type='order'
        )

        return send_success('Order placed successfully', {
            'order_id': order.id,
            'order_number': order.order_number,
            'subtotal': float(order.subtotal),
            'discount_amount': float(order.discount_amount),
            'shipping_charge': float(order.shipping_charge),
            'tax_amount': float(order.tax_amount),
            'total_amount': float(order.total_amount)
        }, status_code=status.HTTP_201_CREATED)

class BuyNowView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        user = request.user
        data = request.data or {}

        product_id = data.get('product_id')
        if not product_id:
            return send_error('Product ID is required.', status_code=status.HTTP_400_BAD_REQUEST)

        try:
            quantity = int(data.get('quantity', 1))
        except (ValueError, TypeError):
            return send_error('Invalid quantity.', status_code=status.HTTP_400_BAD_REQUEST)

        if quantity < 1 or quantity > 50:
            return send_error('Quantity must be between 1 and 50.', status_code=status.HTTP_400_BAD_REQUEST)

        try:
            product = Product.objects.select_for_update().get(id=product_id, status='active')
        except Product.DoesNotExist:
            return send_error('Product not found or is currently unavailable.', status_code=status.HTTP_404_NOT_FOUND)

        if product.stock_quantity < quantity:
            return send_error(f'Insufficient stock for "{product.name}". Only {product.stock_quantity} available.', status_code=status.HTTP_400_BAD_REQUEST)

        address_id = data.get('address_id')
        address = None
        if address_id:
            try:
                address = Address.objects.get(id=address_id, user=user)
            except Address.DoesNotExist:
                return send_error('Address not found or does not belong to your account.', status_code=status.HTTP_400_BAD_REQUEST)

        # Server-side price calculation
        unit_price = Decimal(str(product.price))
        subtotal = unit_price * quantity
        shipping_charge = Decimal('0.00') if subtotal >= Decimal('999.00') else Decimal('99.00')
        tax_amount = (subtotal * Decimal('0.18')).quantize(Decimal('0.01'))
        total_amount = subtotal + shipping_charge + tax_amount

        order = Order.objects.create(
            user=user,
            order_number=generate_order_number(),
            address=address,
            subtotal=subtotal,
            shipping_charge=shipping_charge,
            tax_amount=tax_amount,
            total_amount=total_amount,
            order_status='pending',
            payment_status='pending'
        )

        OrderItem.objects.create(
            order=order,
            product=product,
            product_name=product.name,
            product_sku=product.sku,
            quantity=quantity,
            unit_price=product.price,
            subtotal=subtotal
        )

        # Deduct stock
        product.stock_quantity -= quantity
        product.save(update_fields=['stock_quantity', 'updated_at'])

        Notification.objects.create(
            user=user,
            title='Buy Now Order Placed',
            message=f'Order {order.order_number} created for ₹{order.total_amount}.',
            type='order'
        )

        return send_success('Order created successfully', {
            'order_id': order.id,
            'order_number': order.order_number,
            'total_amount': float(order.total_amount)
        }, status_code=status.HTTP_201_CREATED)

class CancelOrderView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, id):
        return self.put(request, id)

    @transaction.atomic
    def put(self, request, id):
        try:
            order = Order.objects.select_for_update().get(id=id, user=request.user)
        except Order.DoesNotExist:
            return send_error('Order not found or access denied.', status_code=status.HTTP_404_NOT_FOUND)

        if order.order_status in ['shipped', 'delivered', 'cancelled']:
            return send_error(f'Order cannot be cancelled because it is already {order.order_status}.', status_code=status.HTTP_400_BAD_REQUEST)

        order.order_status = 'cancelled'
        order.save(update_fields=['order_status', 'updated_at'])

        # Restock inventory safely
        items = OrderItem.objects.filter(order=order).select_related('product')
        for item in items:
            if item.product_id:
                try:
                    p = Product.objects.select_for_update().get(id=item.product_id)
                    p.stock_quantity += item.quantity
                    p.save(update_fields=['stock_quantity', 'updated_at'])
                except Product.DoesNotExist:
                    pass

        Notification.objects.create(
            user=request.user,
            title='Order Cancelled',
            message=f'Your order {order.order_number} has been cancelled.',
            type='order'
        )

        return send_success('Order cancelled successfully', {'order_id': order.id, 'order_status': 'cancelled'})

class AdminOrderListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if getattr(request.user, 'role', None) != 'ADMIN':
            return send_error('Access denied.', status_code=status.HTTP_403_FORBIDDEN)

        orders = Order.objects.all().select_related('user', 'address').prefetch_related('orderitem_set').order_by('-created_at')
        return send_success('Orders retrieved', {'orders': OrderSerializer(orders, many=True).data})

class AdminOrderStatusView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def put(self, request, id):
        if getattr(request.user, 'role', None) != 'ADMIN':
            return send_error('Access denied.', status_code=status.HTTP_403_FORBIDDEN)

        try:
            order = Order.objects.select_for_update().get(id=id)
        except Order.DoesNotExist:
            return send_error('Order not found.', status_code=status.HTTP_404_NOT_FOUND)

        new_status = request.data.get('order_status', order.order_status)
        valid_statuses = [choice[0] for choice in Order.ORDER_STATUS_CHOICES]
        if new_status not in valid_statuses:
            return send_error(f'Invalid status. Allowed statuses: {", ".join(valid_statuses)}', status_code=status.HTTP_400_BAD_REQUEST)

        order.order_status = new_status
        order.save(update_fields=['order_status', 'updated_at'])

        Notification.objects.create(
            user=order.user,
            title=f'Order Status: {new_status.upper()}',
            message=f'Your order {order.order_number} is now marked as {new_status}.',
            type='order'
        )

        return send_success('Order status updated', {'order_id': order.id, 'order_status': order.order_status})
