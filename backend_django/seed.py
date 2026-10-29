import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_django.settings')
django.setup()

from core.models import User, Admin, Product, ProductCategory, Service
from django.contrib.auth.hashers import make_password

print("Seeding database...")

# Create Admin User
admin_user, created = User.objects.get_or_create(
    email='admin@example.com',
    defaults={
        'name': 'Admin User',
        'password': make_password('admin123'),
        'role': 'ADMIN',
        'phone': '1234567890',
        'is_active': True
    }
)
if created:
    Admin.objects.create(user=admin_user)
    print("Created Admin: admin@example.com / admin123")

# Create Test User
test_user, created = User.objects.get_or_create(
    email='test@example.com',
    defaults={
        'name': 'Test Customer',
        'password': make_password('test1234'),
        'role': 'USER',
        'phone': '0987654321',
        'is_active': True
    }
)
if created:
    print("Created Test User: test@example.com / test1234")

# Create Categories
cat_parts, _ = ProductCategory.objects.get_or_create(
    name='Spare Parts',
    defaults={'description': 'Genuine spare parts', 'slug': 'spare-parts'}
)
cat_acc, _ = ProductCategory.objects.get_or_create(
    name='Accessories',
    defaults={'description': 'Car accessories', 'slug': 'accessories'}
)

# Create Products
Product.objects.get_or_create(
    sku='P-001',
    defaults={
        'name': 'Brake Pads (Front)',
        'category': cat_parts,
        'brand': 'Bosch',
        'price': 1500.00,
        'stock_quantity': 50,
        'status': 'active'
    }
)

Product.objects.get_or_create(
    sku='P-002',
    defaults={
        'name': 'Engine Oil 5W-30',
        'category': cat_parts,
        'brand': 'Castrol',
        'price': 1850.00,
        'stock_quantity': 100,
        'status': 'active'
    }
)

# Create Services
Service.objects.get_or_create(
    name='General Servicing',
    defaults={
        'description': 'Full body check, oil change, and washing.',
        'category': 'Maintenance',
        'price': 2500.00,
        'estimated_duration': 120,
        'status': 'active'
    }
)

Service.objects.get_or_create(
    name='AC Repair',
    defaults={
        'description': 'AC Gas check and refill, filter cleaning.',
        'category': 'Repair',
        'price': 1200.00,
        'estimated_duration': 60,
        'status': 'active'
    }
)

print("Database seeding completed!")
