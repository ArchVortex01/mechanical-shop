import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_django.settings')
django.setup()

from core.models import User, Admin, Product, ProductCategory, Service
from django.contrib.auth.hashers import make_password

print("Seeding database...")

# 1. Create Admin User
admin_user, created = User.objects.get_or_create(
    email='admin@example.com',
    defaults={
        'name': 'Admin User',
        'password': make_password('admin123'),
        'role': 'ADMIN',
        'phone': '9876543210',
        'is_active': True
    }
)
if created:
    Admin.objects.create(user=admin_user, department='Management')
    print("Created Admin: admin@example.com / admin123")

# 2. Create Test Customer
test_user, created = User.objects.get_or_create(
    email='test@example.com',
    defaults={
        'name': 'Test Customer',
        'password': make_password('test1234'),
        'role': 'USER',
        'phone': '9876543211',
        'is_active': True
    }
)
if created:
    print("Created Test User: test@example.com / test1234")

# 3. Create Product Categories
categories_data = [
    ('Car Parts', 'car-parts', 'Genuine and aftermarket parts for cars'),
    ('Bike Parts', 'bike-parts', 'High performance bike chains, brakes, and tyres'),
    ('Truck Parts', 'truck-parts', 'Heavy-duty truck engines, pumps, and differentials'),
    ('Tractor Parts', 'tractor-parts', 'Agricultural machinery and tractor assemblies'),
    ('Bus Parts', 'bus-parts', 'Commercial bus components, air brakes, and leaf springs'),
]

cat_map = {}
for name, slug, desc in categories_data:
    cat, _ = ProductCategory.objects.get_or_create(
        slug=slug,
        defaults={'name': name, 'description': desc}
    )
    cat_map[slug] = cat

# 4. Create Catalog Products (Matching buy-parts.html store items)
products_data = [
    # Car Parts
    ('Engine Oil Filter (Top Quality)', 'CAR-OIL-01', 'car-parts', 'Bosch', 'Universal Car', 450.00, 650.00, 50, '../image/Car_Engine_oil_Filter.webp'),
    ('Brake Pads (Set of 4)', 'CAR-BRK-02', 'car-parts', 'Brembo', 'Universal Car', 1299.00, 1899.00, 40, '../image/Car_Brake_Pads.webp'),
    ('Car Battery 60Ah SMF', 'CAR-BAT-03', 'car-parts', 'Amaron', 'Universal Car', 3499.00, 4299.00, 30, '../image/Car Battery 60Ah SMF.webp'),
    ('LED Headlight Bulbs Pair', 'CAR-LED-04', 'car-parts', 'Philips', 'Universal Car', 899.00, 1299.00, 60, '../image/Car_LED_Headlight_Bulbs_Pair1.webp'),
    ('Alternator Assembly', 'CAR-ALT-05', 'car-parts', 'Lucas-TVS', 'Universal Car', 5899.00, 7499.00, 20, '../image/car_alt.webp'),

    # Bike Parts
    ('Premium Bike Chain Kit', 'BIKE-CHN-01', 'bike-parts', 'Rolon', 'Motorcycle', 850.00, 1100.00, 45, '../image/Bike_Premium_Bike_Chain_Kit.webp'),
    ('High-Grip Bike Tyres (Pair)', 'BIKE-TYR-02', 'bike-parts', 'MRF', 'Motorcycle', 2600.00, 3200.00, 25, '../image/Bike_High-Grip_Bike_Tyres (Pair).webp'),
    ('Bike Brake Pads & Discs', 'BIKE-BRK-03', 'bike-parts', 'Endurance', 'Motorcycle', 750.00, 950.00, 50, '../image/Bike_Brake_Pads_&_Discs.webp'),
    ('Bike Clutch Plate Kit', 'BIKE-CLT-04', 'bike-parts', 'FCC', 'Motorcycle', 650.00, 850.00, 35, '../image/Bike_Clutch_Plate_Kit.webp'),
    ('Front Suspension Fork Assembly', 'BIKE-SUS-05', 'bike-parts', 'Gabriel', 'Motorcycle', 3200.00, 4100.00, 15, '../image/Bike_Front_Suspension_Fork_Assembly.webp'),

    # Truck Parts
    ('Turbocharger Assembly', 'TRK-TRB-01', 'truck-parts', 'Holset', 'Heavy Commercial', 14500.00, 18000.00, 10, '../image/Truck_Turbocharger_Assembly.webp'),
    ('Fuel Injection Pump', 'TRK-FIP-02', 'truck-parts', 'MICO-Bosch', 'Heavy Commercial', 9800.00, 12500.00, 12, '../image/Truck_Fuel_Injection_Pump.webp'),
    ('Engine Oil Filter', 'TRK-OIL-03', 'truck-parts', 'Fleetguard', 'Heavy Commercial', 850.00, 1150.00, 40, '../image/Truck_Engine_Oil_Filter.webp'),
    ('Clutch Plate Kit', 'TRK-CLT-04', 'truck-parts', 'Valeo', 'Heavy Commercial', 6200.00, 7800.00, 18, '../image/Truck_Clutch_Plate_Kit.webp'),
    ('Differential Assembly', 'TRK-DIF-05', 'truck-parts', 'Meritor', 'Heavy Commercial', 24000.00, 29000.00, 8, '../image/Truck_Differential_Assembly.webp'),

    # Tractor Parts
    ('Tractor Clutch Plate', 'TRC-CLT-01', 'tractor-parts', 'Mahindra Genuine', 'Tractor', 4200.00, 5200.00, 20, '../image/Tractor_Clutch_Plate.webp'),
    ('Tractor Piston Kit', 'TRC-PST-02', 'tractor-parts', 'Goetze', 'Tractor', 5800.00, 7100.00, 15, '../image/Tractor_Piston_Kit.webp'),
    ('Tractor Gear Box Parts', 'TRC-GBX-03', 'tractor-parts', 'Sonalika Genuine', 'Tractor', 8500.00, 10500.00, 10, '../image/Tractor_Gear_Box_Parts.webp'),
    ('Hydraulic Pump', 'TRC-HYD-04', 'tractor-parts', 'Rexroth', 'Tractor', 7200.00, 8900.00, 14, '../image/Tractor_Hydraulic_Pump.webp'),
    ('Engine Start Motor', 'TRC-STR-05', 'tractor-parts', 'Denso', 'Tractor', 3800.00, 4800.00, 22, '../image/Tractor_Engine_Start_Motor.webp'),

    # Bus Parts
    ('Bus Turbocharger Assembly', 'BUS-TRB-01', 'bus-parts', 'Garrett', 'Bus / Coach', 16000.00, 19500.00, 10, '../image/Bus_Turbocharger_Assembly.webp'),
    ('Fuel Injector', 'BUS-INJ-02', 'bus-parts', 'Bosch', 'Bus / Coach', 4500.00, 5600.00, 25, '../image/Bus_Fuel_Injector.webp'),
    ('Air Brake Chamber', 'BUS-BRK-03', 'bus-parts', 'Knorr-Bremse', 'Bus / Coach', 3200.00, 4100.00, 30, '../image/Bus_Air_Brake_Chamber.webp'),
    ('Leaf Spring Assembly', 'BUS-LFS-04', 'bus-parts', 'Jamna Auto', 'Bus / Coach', 5500.00, 6800.00, 16, '../image/Bus_Leaf_Spring_Assembly.webp'),
    ('Bus Differential Assembly', 'BUS-DIF-05', 'bus-parts', 'Dana Spicer', 'Bus / Coach', 26000.00, 31000.00, 6, '../image/Bus_Differential_Assembly.webp'),
]

for name, sku, cat_slug, brand, compat, price, orig_price, stock, img in products_data:
    cat = cat_map[cat_slug]
    Product.objects.get_or_create(
        sku=sku,
        defaults={
            'name': name,
            'category': cat,
            'brand': brand,
            'vehicle_compatibility': compat,
            'price': price,
            'original_price': orig_price,
            'stock_quantity': stock,
            'image_url': img,
            'status': 'active'
        }
    )

# 5. Create Workshop Services
services_data = [
    ('Engine Repair', 'Complete engine overhaul, timing belt, and valve clearance tuning', 'Engine Service', 4500.00, '4-6 hours'),
    ('Oil Change', 'Engine oil drainage, filter replacement, and grade check', 'Engine Service', 1200.00, '1-2 hours'),
    ('Engine Diagnostics', 'Computerized ECU scanner fault diagnostics and sensor calibration', 'Engine Service', 800.00, '1-2 hours'),
    ('Cooling System', 'Radiator flush, coolant refill, and thermostat valve inspection', 'Engine Service', 1500.00, '2-3 hours'),
    ('Full Service', 'Bumper-to-bumper 50-point inspection and complete service', 'Vehicle Service', 3500.00, '5-7 hours'),
    ('Brake Service', 'Brake pad replacement, disc skimming, and bleeding', 'Vehicle Service', 1800.00, '2-3 hours'),
    ('AC Service', 'Compressor health check, AC condenser cleaning, and refrigerant recharge', 'Vehicle Service', 2200.00, '2-4 hours'),
    ('General Servicing', 'Multi-point inspection, fluid top-up, and lubrication', 'Maintenance', 2500.00, '3-4 hours'),
]

for name, desc, category, price, duration in services_data:
    Service.objects.get_or_create(
        name=name,
        defaults={
            'description': desc,
            'category': category,
            'price': price,
            'estimated_duration': duration,
            'status': 'active'
        }
    )

print("Database seeding completed successfully! All catalog parts & services are loaded.")
