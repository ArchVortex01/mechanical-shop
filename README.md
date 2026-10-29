# 🚗 MahtoMech — Mechanical Shop & Vehicle Parts Management Platform

> **Robust, secure, and production-ready full-stack platform for automotive workshop bookings, genuine spare parts e-commerce, and centralized workshop administration.**

---

## 1. Project Overview & Current Status

**MahtoMech** is an end-to-end automotive service and e-commerce web platform designed for mechanical repair garages, multi-brand auto shops, and vehicle spare parts retailers. It connects vehicle owners with workshop mechanics, offers real-time booking for vehicle inspections and repairs, and provides a catalog of genuine replacement parts with secure checkout.

### Current Status
- **Backend Architecture:** Django 5/6 + Django REST Framework with modular micro-view structure.
- **Frontend Architecture:** High-performance, lightweight Vanilla HTML5, CSS3, and JavaScript (ES6+).
- **Database:** Full enterprise PostgreSQL support (via `psycopg2-binary`) with isolated test runner fallback.
- **Security & Integrity:** Production hardened (anti-tamper server pricing, atomic database row locking, HMAC SHA256 payment signature verification, role-based JWT authentication, rate limiting, and 100% passing automated test suite).
- **Deployment Status:** Fully prepared for containerized or virtual machine deployment behind Nginx/Gunicorn.

---

## 2. Architecture Overview

MahtoMech follows a decoupled client-server architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                       Web Browser                           │
│  (Vanilla HTML5 / CSS3 / ES6 JavaScript Client Application)  │
└───────────────┬─────────────────────────────▲───────────────┘
                │ HTTP Requests               │ JSON Responses
                │ Bearer JWT Authentication   │
                ▼                             │
┌─────────────────────────────────────────────┴───────────────┐
│                   Nginx / Reverse Proxy                     │
│           (TLS/SSL Termination & Static Assets)             │
└───────────────┬─────────────────────────────▲───────────────┘
                │ WSGI Proxy (Port 8000)      │
                ▼                             │
┌─────────────────────────────────────────────┴───────────────┐
│                    Django REST Framework                    │
│   ┌─────────────────┬──────────────────┬─────────────────┐  │
│   │  Auth & Users   │  Cart & Orders   │ Service Booking │  │
│   ├─────────────────┼──────────────────┼─────────────────┤  │
│   │ Security Guard  │  HMAC Payments   │ Admin Dashboard │  │
│   └─────────────────┴──────────────────┴─────────────────┘  │
└──────────────────────────────┬──────────────────────────────┘
                               │ SQL Queries / Row Locking
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 PostgreSQL Relational Database              │
│       (Users, Products, Bookings, Orders, Payments)         │
└─────────────────────────────────────────────────────────────┘
```

- **Frontend:** Lightweight static assets served with zero compilation overhead. Dynamic API routing adapts via `window.MAHTOMECH_API_BASE_URL` or standard origin defaults.
- **Backend:** Modular Django REST Framework views with atomic transactions, strict serializer validations, and centralized error/success envelopes.
- **Database:** PostgreSQL ensures ACID compliance, concurrency safety with `select_for_update()`, and strict relational constraints.

---

## 3. Complete Feature Inventory

### 🧑‍💼 Customer & Vehicle Owner Portal
- **Service Booking System:** Book vehicle repair, diagnostic, engine tuning, and maintenance appointments with instant confirmation.
- **Parts Catalog & Search:** Filter spare parts by category, search by part name, SKU, brand, and vehicle compatibility.
- **Tamper-Proof Shopping Cart & Checkout:** Add products, apply promo codes (`SAVE10`, `MAHTO10`), enter delivery address, and place orders.
- **Order Tracking & Management:** View order history, item breakdowns, delivery status, and cancel pending orders.
- **Customer Profile:** Manage contact details, saved delivery addresses, and vehicle garage records.

### 🛠️ Administrative & Management Portal (`/admin-login.html`)
- **Executive Dashboard:** Live metrics for total revenue, active orders, pending repair bookings, and registered customer count.
- **Service Bookings Management:** View incoming repair bookings, update booking status (`confirmed`, `in_progress`, `completed`, `cancelled`), and record mechanic notes.
- **Order Processing:** Update order fulfillment stages (`pending`, `confirmed`, `processing`, `shipped`, `delivered`, `cancelled`).
- **Inventory & Catalog Control:** Add/edit products, track stock thresholds, and manage service categories.
- **Customer Directory:** View customer accounts, order counts, and manage access privileges.

---

## 4. Technology Stack

| Layer | Technologies |
|---|---|
| **Backend Language** | Python 3.10+ (Tested on Python 3.12, 3.13, 3.14) |
| **Backend Framework** | Django, Django REST Framework (DRF) |
| **Database** | PostgreSQL 14+ (production/development) / SQLite (isolated test runner) |
| **Database Driver** | `psycopg2-binary` |
| **Authentication** | JSON Web Tokens (`PyJWT`) with HMAC-SHA256 |
| **Payment Gateway** | Razorpay SDK & Server-side HMAC SHA256 Signature Verification |
| **CORS / Security** | `django-cors-headers`, Django Security Middleware |
| **Frontend** | HTML5, CSS3, Vanilla ES6 JavaScript |
| **Deployment** | Gunicorn / Uvicorn, Nginx, Systemd, Docker compatible |

---

## 5. Repository Structure

```
mechanical shop/
├── README.md                      # Comprehensive project documentation
├── .gitignore                     # Git exclusion rules (secrets, venv, sqlite, cache)
├── backend_django/                # Django REST API Backend
│   ├── manage.py                  # Django management CLI
│   ├── requirements.txt           # Pinned production Python dependencies
│   ├── .env.example               # Safe environment variable template
│   ├── backend_django/            # Django Core Project Configuration
│   │   ├── __init__.py
│   │   ├── settings.py            # Hardened settings (env-driven, CORS, HTTPS, DB)
│   │   ├── urls.py                # Main URL router
│   │   ├── wsgi.py                # WSGI entry point for Gunicorn
│   │   └── asgi.py                # ASGI entry point
│   ├── core/                      # Application Business Logic
│   │   ├── models.py              # Models (User, Order, Product, Booking, Payment)
│   │   ├── serializers.py         # DRF Serializers with strict validation
│   │   ├── authentication.py      # JWT Authentication & Bearer Header handler
│   │   ├── auth_views.py          # Register, Login, Admin Login
│   │   ├── order_views.py         # Checkout, Buy Now, Cancel, Stock Locking
│   │   ├── payment_views.py       # Razorpay Order, HMAC Verification, Idempotency
│   │   ├── booking_views.py       # Service appointment scheduling
│   │   ├── admin_views.py         # Dashboard analytics & staff management
│   │   ├── user_views.py          # Customer profile & addresses
│   │   ├── notification_views.py  # User notifications (`is_read` handling)
│   │   ├── misc_views.py          # Health check, SKU lookups, Categories
│   │   ├── views.py               # Scoped ModelViewSets (RBAC & ownership)
│   │   ├── urls.py                # Modular URL routing
│   │   └── tests.py               # Comprehensive regression & security test suite
│   ├── seed.py                    # Database seeding script for catalog & services
│   └── migrations/                # Database schema migrations
└── frontend/                      # Static Web Application
    ├── html/                      # Customer & Admin Web Pages
    │   ├── index.html             # Homepage & service overview
    │   ├── parts.html             # Spare parts catalog
    │   ├── booking.html           # Service appointment booking
    │   ├── cart.html              # Customer cart
    │   ├── checkout.html          # Secure order checkout
    │   ├── profile.html           # Customer dashboard & order history
    │   ├── admin-login.html       # Administrator portal login
    │   ├── admin.html             # Workshop administration dashboard
    │   └── contact.html           # Customer contact form
    ├── CSS/                       # Responsive stylesheets
    │   ├── home.css, parts.css, booking.css, admin.css, etc.
    ├── JAVASRIPT/                 # Frontend client logic
    │   ├── api.js                 # Centralized API client (dynamic baseUrl, auth headers)
    │   ├── login.js               # Customer auth flow
    │   ├── booking.js             # Workshop booking client
    │   ├── checkout.js            # Secure checkout client
    │   ├── cart.js, parts.js, etc.
    │   └── admin/
    │       ├── api.js             # Admin API client with session management
    │       └── admin.js           # Admin dashboard data rendering
    └── images/                    # UI branding and product visuals
```

---

## 6. Prerequisites

Ensure your system has the following installed before setting up MahtoMech:

- **Python:** Version 3.10, 3.11, 3.12, 3.13, or 3.14
- **PostgreSQL:** Version 14, 15, or 16
- **Git:** Version 2.25+
- **Modern Web Browser:** Google Chrome, Mozilla Firefox, Apple Safari, or Microsoft Edge

---

## 7. Step-by-Step Setup Guide

### 7.1 Clone the Repository
```bash
git clone <repository_url> "mechanical shop"
cd "mechanical shop"
```

### 7.2 Create and Activate a Python Virtual Environment

**On Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**On Windows (Command Prompt):**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

### 7.3 Install Python Dependencies
```bash
pip install --upgrade pip
pip install -r backend_django/requirements.txt
```

---

## 8. Environment Variables Guide

Copy the example environment template to create your local `.env`:

```bash
cp backend_django/.env.example backend_django/.env
```

### Generating Secure Secrets
Generate cryptographically strong keys using Python:

```bash
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(50))"
python -c "import secrets; print('JWT_SECRET=' + secrets.token_urlsafe(50))"
```

### Environment Variable Reference

| Variable | Description | Example / Recommended Value |
|---|---|---|
| `DEBUG` | Enable debug mode (`True` for local dev, `False` in prod) | `True` (dev) / `False` (prod) |
| `SECRET_KEY` | Django cryptographic signing key (50+ random chars) | *Generated via secrets module* |
| `ALLOWED_HOSTS` | Comma-separated list of permitted hostnames | `localhost,127.0.0.1,api.mahtomech.in` |
| `CORS_ALLOWED_ORIGINS` | Permitted frontend origins for CORS | `http://localhost:8000,http://127.0.0.1:8000` |
| `CSRF_TRUSTED_ORIGINS` | Trusted origins for CSRF protection | `http://localhost:8000,http://127.0.0.1:8000` |
| `ENABLE_HTTPS` | Enforces SSL redirect, HSTS, and secure cookies | `False` (dev) / `True` (prod) |
| `DB_ENGINE` | Database dialect (`postgresql` or `sqlite`) | `postgresql` |
| `DB_NAME` | Database name | `mahtomech_db` |
| `DB_USER` | PostgreSQL username | `postgres` |
| `DB_PASSWORD` | PostgreSQL user password | `your_secure_password` |
| `DB_HOST` | Database host | `localhost` |
| `DB_PORT` | Database port | `5432` |
| `DATABASE_URL` | Optional complete PostgreSQL connection string | `postgresql://user:pass@host:5432/dbname` |
| `JWT_SECRET` | Secret key for signing customer & admin tokens | *Generated via secrets module* |
| `PAYMENT_MOCK_MODE` | Allows simulated checkout during local testing | `True` (dev) / `False` (prod) |
| `RAZORPAY_KEY_ID` | Razorpay Merchant Key ID | `rzp_test_xxxxxx` |
| `RAZORPAY_KEY_SECRET` | Razorpay Merchant Secret Key | `xxxxxx` |

---

## 9. Database Setup & Migrations

### 9.1 Create the PostgreSQL Database
Access your PostgreSQL prompt:

```bash
psql -U postgres
```

Execute the database creation commands:
```sql
CREATE DATABASE mahtomech_db;
CREATE USER mahtomech_user WITH PASSWORD 'StrongPassword123!';
GRANT ALL PRIVILEGES ON DATABASE mahtomech_db TO mahtomech_user;
ALTER DATABASE mahtomech_db OWNER TO mahtomech_user;
\q
```

### 9.2 Run Migrations
Run the initial Django migrations to establish table schemas:

```bash
cd backend_django
python manage.py migrate
```

---

## 10. Database Seeding

The project includes an idempotent database seeder that populates:
- Default Administrator account (`admin@example.com` / `admin123`)
- Standard Workshop Services (Engine Overhaul, Brake Service, AC Maintenance, Computer Diagnostics, etc.)
- 25 Genuine Spare Parts across 7 vehicle categories matching frontend catalog

Run the seeder from within `backend_django/`:
```bash
python seed.py
```

*Output:*
```
🌱 Seeding MahtoMech database...
  ✓ Default admin verified (admin@example.com)
  ✓ Seeded category: Engine Parts
  ✓ Seeded category: Brakes & Suspension
  ...
  ✓ 25 products verified/seeded.
  ✓ 10 workshop services verified/seeded.
✨ Database seeding completed successfully!
```

---

## 11. Running the Development Server

Start the Django development server on port `8000`:

```bash
python manage.py runserver 0.0.0.0:8000
```

The REST API is now available at:
- **Base API:** `http://127.0.0.1:8000/api/`
- **Health Check:** `http://127.0.0.1:8000/api/health`

---

## 12. Frontend Usage & Serving Options

The frontend consists of static files located in `frontend/`. You have multiple flexible options to view and run the UI:

### Option A: VS Code Live Server (Recommended for Development)
1. Open the workspace in VS Code.
2. Right-click on `frontend/html/index.html` and select **"Open with Live Server"**.
3. Live server will host on `http://127.0.0.1:5500`.
4. In `frontend/html/index.html` (or globally via script), the frontend automatically resolves API requests to `http://localhost:8000/api`.

### Option B: Built-in Python HTTP Server
```bash
cd frontend
python3 -m http.server 3000
```
Open `http://localhost:3000/html/index.html` in your web browser.

### Option C: Production Nginx Static File Serving
Configure Nginx to serve the `frontend/` directory directly (see [Production Deployment](#17-production-deployment-checklist)).

---

## 13. API Documentation & Endpoints

All responses follow a consistent standard envelope:
```json
{
  "success": true,
  "message": "Human-readable status",
  "data": { ... }
}
```

### Key Endpoints

| Method | Endpoint | Auth Required | Description |
|---|---|---|---|
| `GET` | `/api/health` | No | System health and database status |
| `POST` | `/api/auth/register` | No | Customer registration |
| `POST` | `/api/auth/login` | No | Customer login (returns JWT) |
| `POST` | `/api/auth/admin/login` | No | Administrator login (returns admin JWT) |
| `GET` | `/api/products` | No | List products with search, pagination, and category filters |
| `GET` | `/api/products/<id>` | No | Retrieve product details |
| `GET` | `/api/services` | No | List available workshop repair services |
| `POST` | `/api/bookings` | No / Yes | Submit new vehicle repair appointment |
| `GET` | `/api/cart` | Yes | Retrieve current customer cart |
| `POST` | `/api/cart/items` | Yes | Add product to cart |
| `POST` | `/api/orders/checkout` | No / Yes | **Tamper-proof checkout** (server-calculated prices & stock locking) |
| `POST` | `/api/orders/<id>/cancel`| Yes | Cancel order and automatically restore inventory |
| `POST` | `/api/payments/create-order` | Yes | Create Razorpay payment transaction |
| `POST` | `/api/payments/verify` | Yes | **Server-side HMAC-SHA256 signature verification** |
| `GET` | `/api/users/profile` | Yes | Customer profile and vehicle details |
| `GET` | `/api/admin/dashboard` | Admin | Real-time analytics, order stats, revenue |
| `GET` | `/api/orders/admin/all`| Admin | Workshop order management |
| `PUT` | `/api/orders/<id>/status`| Admin | Update order shipping/fulfillment status |
| `GET` | `/api/bookings/admin/all`| Admin | Workshop appointment management |
| `PUT` | `/api/bookings/admin/<id>/status` | Admin | Update service booking status |

---

## 14. Authentication & Authorization Flow

```
1. Customer / Admin logs in with credentials.
   POST /api/auth/login  or  POST /api/auth/admin/login
           │
           ▼
2. Server validates password against Django PBKDF2/Argon2 hashes.
   Generates JWT token signed with server-side JWT_SECRET.
           │
           ▼
3. Client stores token in localStorage ('token' / 'adminToken').
   Centralized api.js automatically attaches header:
   Authorization: Bearer <token>
           │
           ▼
4. Django JWTAuthentication interceptor:
   - Validates HMAC signature and expiration timestamp.
   - Enforces user active status (deactivated accounts instantly blocked).
   - Resolves role ('ADMIN' vs 'USER').
           │
           ▼
5. DRF Permission Classes:
   - IsAuthenticated: Requires valid token.
   - IsAdminUserRole: Strictly requires role == 'ADMIN'.
   - Object-level isolation: Customers can ONLY query their own records.
```

---

## 15. Automated Test Suite

MahtoMech includes an automated test suite verifying security invariants, regression fixes, pricing integrity, and concurrency controls:

### Running Tests
From the project root:
```bash
./venv/bin/python backend_django/manage.py test core
```

### Verified Test Areas
- **Regression Fixes (`CodeIssuesRegressionTests`):**
  - Custom URLs resolved ahead of generic router patterns.
  - Notification mark-read routines using valid `is_read` model field.
  - Anonymous access strictly blocked across sensitive endpoints.
  - Isolation of user records (User A cannot view User B's orders or profiles).
  - Real end-to-end flows for customer login, service booking, and checkout.
- **Pricing & Checkout Integrity (`CheckoutSecurityAndPricingTests`):**
  - **Price manipulation rejection:** Client attempts to submit fabricated prices (`price: 1.00`) are ignored; server computes totals strictly from verified database records.
  - **Fabricated product rejection:** Client attempts to purchase non-existent IDs return `400 Bad Request` without creating dummy products.
  - **Overselling prevention:** Insufficient inventory requests are rejected.
  - **Atomic stock reduction:** Purchases decrement stock atomically using row locking (`select_for_update()`).
  - **Server-side discounts:** Promo codes (`SAVE10`, `MAHTO10`) calculated on server.
  - **Order cancellation:** Cancelling an order automatically restores inventory to database.
- **Payment Security (`PaymentSecurityTests`):**
  - Payment order initiation with gateway/mock state tracking.
  - Digital signature verification using HMAC-SHA256 (`hmac.compare_digest`).
  - Rejection of tampered signatures.
  - Payment verification idempotency.
  - Cross-user payment authorization checks.
  - Production enforcement: `is_mock_mode()` returns `False` when `DEBUG=False`.
- **Authentication & RBAC (`AuthenticationAndAuthorizationTests`):**
  - Rejection of invalid, malformed, or expired JWT tokens.
  - Immediate exclusion of deactivated accounts (`is_active=False`).
  - Role-based protection: regular users are denied access to admin dashboards.
  - Direct object reference protection: users cannot query or alter other users' addresses.

---

## 16. Security Best Practices Implemented

1. **Zero-Trust Client Pricing:** Client-submitted prices, discounts, and totals are discarded. Prices are read exclusively from database records inside atomic database transactions.
2. **Race-Condition & Stock Depletion Defense:** Inventory reduction uses row-level locking (`select_for_update()`) to prevent race conditions during high-volume flash sales.
3. **Server-Side Digital Signature Verification:** Razorpay webhook/client payment evidence is verified via HMAC SHA256 signatures with constant-time equality comparisons (`hmac.compare_digest`).
4. **Idempotency Protection:** Consecutive duplicate checkout requests within a 5-second window return existing order records to prevent double billing.
5. **Role-Based Object Isolation:** ModelViewSet querysets are strictly scoped to `request.user` for non-admin accounts.
6. **No Leaked Secrets:** Hardcoded production secrets removed from repository. `.env` is excluded via `.gitignore`.
7. **Rate Limiting (Throttling):** DRF throttling configured (`100/minute` for anonymous visitors, `1000/minute` for authenticated users).
8. **HTTP Security Headers:** Clickjacking protection (`X-Frame-Options: DENY`), MIME sniffing protection (`X-Content-Type-Options: nosniff`), and configurable HSTS.

---

## 17. Production Deployment Checklist

Before deploying MahtoMech to production:

- [ ] Set `DEBUG=False` in `.env`.
- [ ] Generate unique, cryptographically random `SECRET_KEY` and `JWT_SECRET`.
- [ ] Configure explicit `ALLOWED_HOSTS` (e.g. `ALLOWED_HOSTS=mahtomech.in,www.mahtomech.in`).
- [ ] Set `ENABLE_HTTPS=True` to activate SSL redirection, secure cookies, and HSTS.
- [ ] Restrict `CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS` to trusted frontend domains.
- [ ] Set `PAYMENT_MOCK_MODE=False` and supply valid live `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET`.
- [ ] Run Django deployment verification:
  ```bash
  python manage.py check --deploy
  ```
- [ ] Collect static files:
  ```bash
  python manage.py collectstatic --noinput
  ```
- [ ] Run under a production WSGI/ASGI server (e.g. Gunicorn):
  ```bash
  gunicorn backend_django.wsgi:application --bind 127.0.0.1:8000 --workers 4 --threads 2
  ```
- [ ] Place behind an Nginx reverse proxy with TLS/SSL certificates (Let's Encrypt / Certbot).

---

## 18. Sample Nginx & Systemd Configuration

### Nginx Configuration (`/etc/nginx/sites-available/mahtomech`)
```nginx
server {
    listen 80;
    server_name mahtomech.in www.mahtomech.in;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name mahtomech.in www.mahtomech.in;

    ssl_certificate /etc/letsencrypt/live/mahtomech.in/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/mahtomech.in/privkey.pem;

    # Static Frontend
    location / {
        root /var/www/mahtomech/frontend/html;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # Static CSS, JS, and Images
    location /CSS/ {
        alias /var/www/mahtomech/frontend/CSS/;
    }
    location /JAVASRIPT/ {
        alias /var/www/mahtomech/frontend/JAVASRIPT/;
    }
    location /images/ {
        alias /var/www/mahtomech/frontend/images/;
    }

    # Django Static & Media
    location /static/ {
        alias /var/www/mahtomech/backend_django/staticfiles/;
    }
    location /media/ {
        alias /var/www/mahtomech/backend_django/media/;
    }

    # Django API Reverse Proxy
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Systemd Service (`/etc/systemd/system/mahtomech.service`)
```ini
[Unit]
Description=MahtoMech Gunicorn Application Server
After=network.target postgresql.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/mahtomech/backend_django
ExecStart=/var/www/mahtomech/venv/bin/gunicorn \
          --workers 4 \
          --threads 2 \
          --bind 127.0.0.1:8000 \
          backend_django.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## 19. Troubleshooting Guide

### 1. `psycopg2.OperationalError: could not connect to server`
- **Cause:** PostgreSQL server is not running or credentials in `.env` are incorrect.
- **Solution:** Verify service status via `sudo systemctl status postgresql`. Test connection directly with `psql -h localhost -U <user> -d <dbname>`.

### 2. Frontend shows `Failed to fetch` or Network Errors
- **Cause:** Django backend is not running or running on an unexpected port.
- **Solution:** Ensure Django is running on port 8000 (`python manage.py runserver 0.0.0.0:8000`). If hosting frontend on another port, verify `CORS_ALLOWED_ORIGINS` in `.env`.

### 3. `Method Not Allowed (405)` on Custom Endpoints
- **Cause:** Incorrect HTTP verb used (e.g. `GET` instead of `POST` or `PUT`).
- **Solution:** Check the [API Documentation](#13-api-documentation--endpoints) table above. Note that order cancellation accepts both `POST` and `PUT`.

### 4. Admin Login Redirect Loop or Unauthorized
- **Cause:** User account does not have `role = 'ADMIN'` or database was not seeded.
- **Solution:** Run `python seed.py` to ensure the default administrator (`admin@example.com` / `admin123`) is properly initialized with role `'ADMIN'`.

---

## 20. Project Limitations & Future Roadmap

### Current Scope & Limitations
- **Email Delivery:** Booking confirmations currently simulate email dispatch via mock logger. Connect an SMTP host (e.g. AWS SES, SendGrid, Mailgun) in `.env` for production email transmission.
- **SMS Notifications:** SMS alerts for repair milestones can be integrated via Twilio or Fast2SMS.

### Roadmap & Planned Enhancements
- [ ] Real-time mechanic work order status via Django Channels / WebSockets.
- [ ] Customer Google / OAuth2 social authentication.
- [ ] Automated invoice generation (PDF downloads for paid orders).
- [ ] Multi-garage inventory synchronization for workshop chains.
- [ ] Progressive Web App (PWA) offline support for garage mechanics on tablets.

---

## License & Ownership
Copyright © 2026 **MahtoMech Mechanical Shop**. All rights reserved.  
Developed and maintained for automotive service excellence.
