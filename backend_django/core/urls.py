from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet, AdminViewSet, AddressViewSet, VehicleViewSet,
    ServiceViewSet, ServiceBookingViewSet, ServiceHistoryViewSet,
    ProductCategoryViewSet, ProductViewSet, CartViewSet,
    CartItemViewSet, OrderViewSet, OrderItemViewSet,
    PaymentViewSet, ContactMessageViewSet, NotificationViewSet
)
from .auth_views import RegisterView, LoginView, AdminLoginView
from .cart_views import CartView, CartItemView, CartItemDetailView
from .order_views import CheckoutView, BuyNowView, CancelOrderView, AdminOrderListView, AdminOrderStatusView
from .payment_views import CreatePaymentOrderView, VerifyPaymentView, RecordFailureView, OrderPaymentDetailView
from .booking_views import BookingListView, BookingDetailView, BookingCancelView, AdminBookingListView, AdminBookingStatusView
from .admin_views import DashboardStatsView
from .user_views import UserProfileView, ChangePasswordView, UserDashboardView, AdminUserListView, AdminUserDetailView, AdminUserStatusView, AddressSetDefaultView
from .notification_views import ReadNotificationView, ReadAllNotificationView
from .misc_views import HealthCheckView, ServiceCategoriesView, ProductBySkuView, CategoryBySlugView

router = DefaultRouter(trailing_slash=False)
router.register(r'users', UserViewSet)
router.register(r'admins', AdminViewSet)
router.register(r'addresses', AddressViewSet)
router.register(r'vehicles', VehicleViewSet)
router.register(r'services', ServiceViewSet)
router.register(r'service-history', ServiceHistoryViewSet)
router.register(r'categories', ProductCategoryViewSet)
router.register(r'products', ProductViewSet)
router.register(r'carts', CartViewSet)
router.register(r'cart-items', CartItemViewSet)
router.register(r'orders', OrderViewSet)
router.register(r'order-items', OrderItemViewSet)
router.register(r'payments', PaymentViewSet)
router.register(r'contact', ContactMessageViewSet)
router.register(r'notifications', NotificationViewSet)

urlpatterns = [
    # Misc Endpoints
    path('api/health', HealthCheckView.as_view(), name='health-check'),
    path('api/services/categories', ServiceCategoriesView.as_view(), name='service-categories'),
    path('api/products/sku/<str:sku>', ProductBySkuView.as_view(), name='product-by-sku'),
    path('api/categories/<str:slug>', CategoryBySlugView.as_view(), name='category-by-slug'),
    path('api/auth/register', RegisterView.as_view(), name='register'),
    path('api/auth/login', LoginView.as_view(), name='login'),
    path('api/auth/admin/login', AdminLoginView.as_view(), name='admin-login'),
    
    # Custom Cart Endpoints
    path('api/cart', CartView.as_view(), name='cart'),
    path('api/cart/items', CartItemView.as_view(), name='cart-items-add'),
    path('api/cart/items/<int:product_id>', CartItemDetailView.as_view(), name='cart-items-detail'),
    
    # Custom Order Endpoints
    path('api/orders/checkout', CheckoutView.as_view(), name='checkout'),
    path('api/orders/buy-now', BuyNowView.as_view(), name='order-buy-now'),
    path('api/orders/<int:id>/cancel', CancelOrderView.as_view(), name='order-cancel'),
    path('api/orders/admin/all', AdminOrderListView.as_view(), name='admin-orders-list'),
    path('api/orders/<int:id>/status', AdminOrderStatusView.as_view(), name='admin-orders-status'),
    
    # Custom Payment Endpoints
    path('api/payments/create-order', CreatePaymentOrderView.as_view(), name='payment-create-order'),
    path('api/payments/verify', VerifyPaymentView.as_view(), name='payment-verify'),
    path('api/payments/failed', RecordFailureView.as_view(), name='payment-failed'),
    path('api/payments/order/<int:order_id>', OrderPaymentDetailView.as_view(), name='payment-order-detail'),
    
    # Custom Booking Endpoints
    path('api/bookings', BookingListView.as_view(), name='booking-list-create'),
    path('api/bookings/admin/all', AdminBookingListView.as_view(), name='booking-admin-all'),
    path('api/bookings/<str:id_or_ref>', BookingDetailView.as_view(), name='booking-detail'),
    path('api/bookings/<int:id>/cancel', BookingCancelView.as_view(), name='booking-cancel'),
    path('api/bookings/admin/<int:id>/status', AdminBookingStatusView.as_view(), name='booking-admin-status'),
    
    # Custom Admin Endpoints
    path('api/admin/dashboard', DashboardStatsView.as_view(), name='admin-dashboard'),
    path('api/admin/users', AdminUserListView.as_view(), name='admin-users-list'),
    path('api/admin/users/<int:id>', AdminUserDetailView.as_view(), name='admin-users-detail'),
    path('api/admin/users/<int:id>/status', AdminUserStatusView.as_view(), name='admin-users-status'),
    
    # Custom User Endpoints
    path('api/users/profile', UserProfileView.as_view(), name='user-profile'),
    path('api/users/change-password', ChangePasswordView.as_view(), name='user-change-password'),
    path('api/users/dashboard', UserDashboardView.as_view(), name='user-dashboard'),
    
    # Custom Address & Notifications
    path('api/addresses/<int:id>/default', AddressSetDefaultView.as_view(), name='address-default'),
    path('api/notifications/read-all', ReadAllNotificationView.as_view(), name='notification-read-all'),
    path('api/notifications/<int:id>/read', ReadNotificationView.as_view(), name='notification-read'),

    # Default router endpoints (generic CRUD) placed after custom paths so specific URLs match first
    path('api/', include(router.urls)),
]
