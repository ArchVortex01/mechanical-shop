from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from .models import Service, Product, ProductCategory
from .auth_views import send_success, send_error

class HealthCheckView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        return send_success('API is running', {'status': 'ok', 'environment': 'development'})

class ServiceCategoriesView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        # Extract unique categories from Services
        categories = Service.objects.values_list('category', flat=True).distinct()
        return send_success('Service categories retrieved', list(categories))

class ProductBySkuView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request, sku):
        try:
            product = Product.objects.get(sku=sku)
            from .serializers import ProductSerializer
            return send_success('Product retrieved', ProductSerializer(product).data)
        except Product.DoesNotExist:
            return send_error('Product not found', status_code=404)

class CategoryBySlugView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request, slug):
        try:
            category = ProductCategory.objects.get(slug=slug)
            from .serializers import ProductCategorySerializer
            return send_success('Category retrieved', ProductCategorySerializer(category).data)
        except ProductCategory.DoesNotExist:
            return send_error('Category not found', status_code=404)
