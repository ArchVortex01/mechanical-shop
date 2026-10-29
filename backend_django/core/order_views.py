import uuid
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Cart, CartItem, Product, ProductCategory, Order, OrderItem, Address, Notification, User
from .auth_views import send_success, send_error
from django.db import transaction

def generate_order_number():
    return 'ORD-' + str(uuid.uuid4().hex)[:10].upper()

class CheckoutView(APIView):
    def get_permissions(self):
        if self.request.method == 'POST':
            return [AllowAny()]
        return [IsAuthenticated()]

    @transaction.atomic
    def post(self, request):
        data = request.data
        if request.user and request.user.is_authenticated:
            user = request.user
        else:
            email = (data.get('email') or '').lower().strip()
            phone = (data.get('phone') or '').strip()
            full_name = data.get('fullName') or data.get('full_name') or 'Customer'
            if not email:
                return send_error('Email is required for checkout.', status_code=status.HTTP_400_BAD_REQUEST)
            user = User.objects.filter(email=email).first()
            if not user:
                user = User.objects.create_user(email=email, name=full_name, phone=phone, password=None, role='USER')

        address_id = data.get('address_id')
        address = None
        if address_id:
            try:
                address = Address.objects.get(id=address_id, user=user)
            except Address.DoesNotExist:
                pass
        if not address and (data.get('address') or data.get('streetAddress')):
            address = Address.objects.create(
                user=user,
                full_name=data.get('fullName') or data.get('full_name', user.name),
                phone=data.get('phone', user.phone),
                address_line=data.get('address') or data.get('streetAddress', ''),
                city=data.get('city', ''),
                state=data.get('state', ''),
                pincode=data.get('pinCode') or data.get('pincode', ''),
                landmark=data.get('landmark', '')
            )
        
        cart, _ = Cart.objects.get_or_create(user=user)
        items = CartItem.objects.filter(cart=cart).select_related('product')
        
        # If cart in database is empty, check if client passed items (e.g. from localStorage)
        if not items.exists() and data.get('items'):
            for it in data.get('items'):
                pid = it.get('product_id') or it.get('id')
                qty = int(it.get('quantity') or it.get('qty', 1))
                product = None
                if pid:
                    product = Product.objects.filter(id=pid).first()
                if not product and it.get('title'):
                    product = Product.objects.filter(name__icontains=it.get('title')).first()
                if not product:
                    cat = ProductCategory.objects.first()
                    if not cat:
                        cat = ProductCategory.objects.create(name='General Parts', slug='general-parts')
                    raw_price = str(it.get('price', 999)).replace('₹', '').replace(',', '').strip()
                    try:
                        price_val = float(raw_price)
                    except ValueError:
                        price_val = 999.00
                    product = Product.objects.create(
                        name=it.get('title', 'Vehicle Part'),
                        sku='SKU-' + str(uuid.uuid4().hex)[:8].upper(),
                        category=cat,
                        brand='Standard',
                        vehicle_compatibility='Universal',
                        price=price_val,
                        stock_quantity=50,
                        status='active'
                    )
                CartItem.objects.create(cart=cart, product=product, quantity=qty)
            items = CartItem.objects.filter(cart=cart).select_related('product')
        
        if not items.exists():
            return send_error('Your cart is empty.', status_code=status.HTTP_400_BAD_REQUEST)
            
        subtotal = 0
        for item in items:
            product = item.product
            if product.status != 'active':
                return send_error(f'Product {product.name} is currently unavailable.', status_code=status.HTTP_400_BAD_REQUEST)
            if product.stock_quantity < item.quantity:
                return send_error(f'Insufficient stock for {product.name}.', status_code=status.HTTP_400_BAD_REQUEST)
                
            subtotal += float(product.price) * item.quantity
            
        shipping_charge = 0.00 if subtotal >= 999 else 99.00
        tax_amount = float("{:.2f}".format(subtotal * 0.18))
        total_amount = float("{:.2f}".format(subtotal + shipping_charge + tax_amount))
                
        order = Order.objects.create(
            order_number=generate_order_number(),
            user=user,
            address=address,
            subtotal=subtotal,
            shipping_charge=shipping_charge,
            tax_amount=tax_amount,
            total_amount=total_amount,
            payment_status='pending',
            order_status='pending'
        )
        
        for item in items:
            product = item.product
            item_subtotal = float(product.price) * item.quantity
            
            OrderItem.objects.create(
                order=order,
                product=product,
                product_name=product.name,
                product_sku=product.sku,
                unit_price=product.price,
                quantity=item.quantity,
                subtotal=item_subtotal
            )
            
            # Deduct stock
            product.stock_quantity -= item.quantity
            product.save()
            
        # Clear cart
        items.delete()
        
        # Notification
        Notification.objects.create(
            user=user,
            title='Order Placed Successfully',
            message=f'Your order {order.order_number} has been placed successfully.',
            type='order'
        )
        
        return send_success('Order placed successfully', {
            'order_id': order.id,
            'order_number': order.order_number,
            'total_amount': order.total_amount
        }, status_code=status.HTTP_201_CREATED)

class BuyNowView(APIView):
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def post(self, request):
        user = request.user
        data = request.data
        
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))
        address_id = data.get('address_id')
        
        try:
            product = Product.objects.get(id=product_id, status='active')
            if product.stock_quantity < quantity:
                return send_error('Not enough stock', status_code=status.HTTP_400_BAD_REQUEST)
        except Product.DoesNotExist:
            return send_error('Product not found', status_code=status.HTTP_404_NOT_FOUND)
            
        address = None
        if address_id:
            try:
                address = Address.objects.get(id=address_id, user=user)
            except Address.DoesNotExist:
                return send_error('Address not found', status_code=status.HTTP_404_NOT_FOUND)
        
        total_amount = float(product.price) * quantity
        
        order = Order.objects.create(
            user=user,
            order_number=generate_order_number(),
            total_amount=total_amount,
            address=address,
            order_status='pending',
            payment_status='pending',
            subtotal=total_amount,
            shipping_charge=0,
            tax_amount=0
        )
        
        OrderItem.objects.create(
            order=order,
            product=product,
            product_name=product.name,
            product_sku=product.sku,
            quantity=quantity,
            unit_price=product.price,
            subtotal=total_amount
        )
        
        product.stock_quantity -= quantity
        product.save()
        
        return send_success('Order created successfully', {'order_id': order.id, 'order_number': order.order_number})

class CancelOrderView(APIView):
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def put(self, request, id):
        try:
            order = Order.objects.get(id=id, user=request.user)
        except Order.DoesNotExist:
            return send_error('Order not found', status_code=status.HTTP_404_NOT_FOUND)
            
        if order.order_status in ['shipped', 'delivered', 'cancelled']:
            return send_error('Order cannot be cancelled', status_code=status.HTTP_400_BAD_REQUEST)
            
        order.order_status = 'cancelled'
        order.save()
        
        items = OrderItem.objects.filter(order=order)
        for item in items:
            item.product.stock_quantity += item.quantity
            item.product.save()
            
        return send_success('Order cancelled successfully')

class AdminOrderListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if request.user.role != 'ADMIN':
            return send_error('Access denied', status_code=status.HTTP_403_FORBIDDEN)
            
        orders = Order.objects.all().order_by('-created_at')
        from .serializers import OrderSerializer
        return send_success('Orders retrieved', {'orders': OrderSerializer(orders, many=True).data})

class AdminOrderStatusView(APIView):
    permission_classes = [IsAuthenticated]
    
    def put(self, request, id):
        if request.user.role != 'ADMIN':
            return send_error('Access denied', status_code=status.HTTP_403_FORBIDDEN)
            
        try:
            order = Order.objects.get(id=id)
        except Order.DoesNotExist:
            return send_error('Order not found', status_code=status.HTTP_404_NOT_FOUND)
            
        new_status = request.data.get('order_status', order.order_status)
        order.order_status = new_status
        order.save()
        
        return send_success('Order status updated')
