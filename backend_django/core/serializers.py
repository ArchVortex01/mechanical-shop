from rest_framework import serializers
from .models import (
    User, Admin, Address, Vehicle, Service, ServiceBooking, ServiceHistory,
    ProductCategory, Product, Cart, CartItem, Order, OrderItem, Payment,
    ContactMessage, Notification
)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'phone', 'role', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'role', 'is_active', 'created_at', 'updated_at']

class AdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Admin
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = '__all__'
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = '__all__'
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class ServiceBookingSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source='service.name', read_only=True)
    customer_name = serializers.CharField(source='user.name', read_only=True)
    customer_phone = serializers.CharField(source='user.phone', read_only=True)

    class Meta:
        model = ServiceBooking
        fields = '__all__'
        read_only_fields = ['id', 'booking_ref', 'user', 'estimated_cost', 'created_at', 'updated_at']

class ServiceHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceHistory
        fields = '__all__'
        read_only_fields = ['id', 'user', 'created_at']

class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError('Product price cannot be negative.')
        return value

    def validate_stock_quantity(self, value):
        if value < 0:
            raise serializers.ValidationError('Stock quantity cannot be negative.')
        return value

class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = '__all__'
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

class CartItemSerializer(serializers.ModelSerializer):
    product_details = ProductSerializer(source='product', read_only=True)

    class Meta:
        model = CartItem
        fields = '__all__'
        read_only_fields = ['id', 'cart', 'created_at', 'updated_at']

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError('Quantity must be at least 1.')
        if value > 50:
            raise serializers.ValidationError('Maximum purchase quantity is 50 units per item.')
        return value

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = '__all__'
        read_only_fields = ['id', 'order', 'unit_price', 'subtotal', 'created_at']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(source='orderitem_set', many=True, read_only=True)
    customer_name = serializers.CharField(source='user.name', read_only=True)
    customer_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = [
            'id', 'order_number', 'user', 'subtotal', 'shipping_charge',
            'tax_amount', 'discount_amount', 'total_amount',
            'payment_status', 'order_status', 'created_at', 'updated_at'
        ]

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ['id', 'user', 'amount', 'currency', 'status', 'created_at', 'updated_at']

class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = '__all__'
        read_only_fields = ['id', 'status', 'admin_response', 'created_at', 'updated_at']

    def validate_email(self, value):
        if '@' not in value or '.' not in value:
            raise serializers.ValidationError('Please enter a valid email address.')
        return value.lower().strip()

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ['id', 'user', 'created_at']
