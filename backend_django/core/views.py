from rest_framework import viewsets, permissions
from django.db.models import Q
from .models import (
    User, Admin, Address, Vehicle, Service, ServiceBooking, ServiceHistory,
    ProductCategory, Product, Cart, CartItem, Order, OrderItem, Payment,
    ContactMessage, Notification
)
from .serializers import (
    UserSerializer, AdminSerializer, AddressSerializer, VehicleSerializer,
    ServiceSerializer, ServiceBookingSerializer, ServiceHistorySerializer,
    ProductCategorySerializer, ProductSerializer, CartSerializer,
    CartItemSerializer, OrderSerializer, OrderItemSerializer,
    PaymentSerializer, ContactMessageSerializer, NotificationSerializer
)

class IsAdminUserRole(permissions.BasePermission):
    """
    Grants access only to authenticated users with role == 'ADMIN'.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            getattr(request.user, 'role', None) == 'ADMIN'
        )

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Public safe methods (GET, HEAD, OPTIONS); admin-only for mutating methods.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(
            request.user and
            request.user.is_authenticated and
            getattr(request.user, 'role', None) == 'ADMIN'
        )

class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return User.objects.none()
        if getattr(user, 'role', None) == 'ADMIN':
            return User.objects.all().order_by('-created_at')
        return User.objects.filter(id=user.id).order_by('-created_at')

class AdminViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsAdminUserRole]
    queryset = Admin.objects.all().select_related('user').order_by('-created_at')
    serializer_class = AdminSerializer

class AddressViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Address.objects.all()
    serializer_class = AddressSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Address.objects.none()
        if getattr(user, 'role', None) == 'ADMIN':
            return Address.objects.all().order_by('-created_at')
        return Address.objects.filter(user=user).order_by('-is_default', '-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class VehicleViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Vehicle.objects.none()
        if getattr(user, 'role', None) == 'ADMIN':
            return Vehicle.objects.all().order_by('-created_at')
        return Vehicle.objects.filter(user=user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ServiceViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer

    def get_queryset(self):
        user = self.request.user
        is_admin = bool(user and user.is_authenticated and getattr(user, 'role', None) == 'ADMIN')
        qs = Service.objects.all()
        if not is_admin:
            qs = qs.filter(status='active')
            
        category = self.request.query_params.get('category')
        if category:
            qs = qs.filter(category__iexact=category)
        return qs.order_by('name')

class ServiceBookingViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = ServiceBooking.objects.all()
    serializer_class = ServiceBookingSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return ServiceBooking.objects.none()
        qs = ServiceBooking.objects.all().select_related('user', 'vehicle', 'service')
        if getattr(user, 'role', None) == 'ADMIN':
            return qs.order_by('-created_at')
        return qs.filter(user=user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ServiceHistoryViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = ServiceHistory.objects.all()
    serializer_class = ServiceHistorySerializer

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return ServiceHistory.objects.none()
        qs = ServiceHistory.objects.all().select_related('user', 'vehicle', 'service', 'booking')
        if getattr(user, 'role', None) == 'ADMIN':
            return qs.order_by('-service_date')
        return qs.filter(user=user).order_by('-service_date')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ProductCategoryViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]
    queryset = ProductCategory.objects.all().order_by('name')
    serializer_class = ProductCategorySerializer

class ProductViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def get_queryset(self):
        user = self.request.user
        is_admin = bool(user and user.is_authenticated and getattr(user, 'role', None) == 'ADMIN')
        qs = Product.objects.all().select_related('category')
        
        if not is_admin:
            qs = qs.filter(status='active')

        category = self.request.query_params.get('category')
        if category:
            qs = qs.filter(Q(category__slug=category) | Q(category__name__iexact=category))

        search = self.request.query_params.get('search') or self.request.query_params.get('q')
        if search:
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(brand__icontains=search) |
                Q(sku__icontains=search) |
                Q(vehicle_compatibility__icontains=search)
            )

        return qs.order_by('-created_at')

class CartViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Cart.objects.all()
    serializer_class = CartSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Cart.objects.none()
        if getattr(user, 'role', None) == 'ADMIN':
            return Cart.objects.all().select_related('user').order_by('-created_at')
        return Cart.objects.filter(user=user).select_related('user').order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class CartItemViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return CartItem.objects.none()
        qs = CartItem.objects.all().select_related('cart', 'product')
        if getattr(user, 'role', None) == 'ADMIN':
            return qs.order_by('-created_at')
        return qs.filter(cart__user=user).order_by('-created_at')

class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Order.objects.none()
        qs = Order.objects.all().select_related('user', 'address').prefetch_related('orderitem_set')
        if getattr(user, 'role', None) == 'ADMIN':
            return qs.order_by('-created_at')
        return qs.filter(user=user).order_by('-created_at')

class OrderItemViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return OrderItem.objects.none()
        qs = OrderItem.objects.all().select_related('order', 'product')
        if getattr(user, 'role', None) == 'ADMIN':
            return qs.order_by('-created_at')
        return qs.filter(order__user=user).order_by('-created_at')

class PaymentViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Payment.objects.none()
        qs = Payment.objects.all().select_related('order', 'user')
        if getattr(user, 'role', None) == 'ADMIN':
            return qs.order_by('-created_at')
        return qs.filter(user=user).order_by('-created_at')

class ContactMessageViewSet(viewsets.ModelViewSet):
    queryset = ContactMessage.objects.all().order_by('-created_at')
    serializer_class = ContactMessageSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsAdminUserRole()]

class NotificationViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Notification.objects.none()
        qs = Notification.objects.all().select_related('user')
        if getattr(user, 'role', None) == 'ADMIN':
            return qs.order_by('-created_at')
        return qs.filter(user=user).order_by('-created_at')
