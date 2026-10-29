from rest_framework import viewsets, permissions
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
            return User.objects.all()
        return User.objects.filter(id=user.id)

class AdminViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsAdminUserRole]
    queryset = Admin.objects.all()
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
            return Address.objects.all()
        return Address.objects.filter(user=user)

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
            return Vehicle.objects.all()
        return Vehicle.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ServiceViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer

class ServiceBookingViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = ServiceBooking.objects.all()
    serializer_class = ServiceBookingSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return ServiceBooking.objects.none()
        if getattr(user, 'role', None) == 'ADMIN':
            return ServiceBooking.objects.all()
        return ServiceBooking.objects.filter(user=user)

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
        if getattr(user, 'role', None) == 'ADMIN':
            return ServiceHistory.objects.all()
        return ServiceHistory.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ProductCategoryViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]
    queryset = ProductCategory.objects.all()
    serializer_class = ProductCategorySerializer

class ProductViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

class CartViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Cart.objects.all()
    serializer_class = CartSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Cart.objects.none()
        if getattr(user, 'role', None) == 'ADMIN':
            return Cart.objects.all()
        return Cart.objects.filter(user=user)

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
        if getattr(user, 'role', None) == 'ADMIN':
            return CartItem.objects.all()
        return CartItem.objects.filter(cart__user=user)

class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Order.objects.none()
        if getattr(user, 'role', None) == 'ADMIN':
            return Order.objects.all()
        return Order.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class OrderItemViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return OrderItem.objects.none()
        if getattr(user, 'role', None) == 'ADMIN':
            return OrderItem.objects.all()
        return OrderItem.objects.filter(order__user=user)

class PaymentViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Payment.objects.none()
        if getattr(user, 'role', None) == 'ADMIN':
            return Payment.objects.all()
        return Payment.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ContactMessageViewSet(viewsets.ModelViewSet):
    queryset = ContactMessage.objects.all()
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
        if getattr(user, 'role', None) == 'ADMIN':
            return Notification.objects.all()
        return Notification.objects.filter(user=user)
