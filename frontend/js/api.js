/**
 * MahtoMech - Central Frontend API Client
 * Secure, resilient bridge between the frontend UI and REST API backend.
 */

(function(window) {
    'use strict';

    /**
     * Resolve Base API URL:
     * 1. window.MAHTOMECH_API_BASE_URL (Injected via deployment or page script)
     * 2. LocalStorage override ('mm_api_base_url' for testing/staging)
     * 3. Same-origin '/api' if hosted alongside Django
     * 4. Default development fallback 'http://localhost:8000/api'
     */
    function resolveBaseUrl() {
        if (window.MAHTOMECH_API_BASE_URL && typeof window.MAHTOMECH_API_BASE_URL === 'string') {
            return window.MAHTOMECH_API_BASE_URL.replace(/\/+$/, '');
        }
        try {
            const custom = localStorage.getItem('mm_api_base_url');
            if (custom) return custom.replace(/\/+$/, '');
        } catch (e) {}

        if (window.location && window.location.protocol.startsWith('http')) {
            // If served directly by Django on port 8000 or production domain
            if (window.location.port === '8000' || window.location.port === '') {
                return '/api';
            }
        }
        return 'http://localhost:8000/api';
    }

    const API_BASE_URL = resolveBaseUrl();
    const TOKEN_KEY = 'mm_auth_token';
    const USER_KEY = 'mm_auth_user';
    const DEFAULT_TIMEOUT_MS = 15000;

    /**
     * Core HTTP Request Dispatcher with timeout & error handling
     */
    async function request(endpoint, options = {}) {
        const url = `${API_BASE_URL}${endpoint.startsWith('/') ? endpoint : '/' + endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            ...(options.headers || {})
        };

        const token = getToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const controller = typeof AbortController !== 'undefined' ? new AbortController() : null;
        const timeoutMs = options.timeout || DEFAULT_TIMEOUT_MS;
        let timeoutId = null;

        if (controller) {
            timeoutId = setTimeout(() => {
                controller.abort();
            }, timeoutMs);
        }

        const config = {
            ...options,
            headers,
            signal: controller ? controller.signal : undefined
        };

        if (options.body && typeof options.body === 'object' && !(options.body instanceof FormData)) {
            config.body = JSON.stringify(options.body);
        }

        try {
            const response = await fetch(url, config);
            if (timeoutId) clearTimeout(timeoutId);

            const data = await response.json().catch(() => ({}));

            if (!response.ok) {
                // If token expired or unauthorized
                if (response.status === 401 && token) {
                    setToken(null);
                    setUser(null);
                    try {
                        window.dispatchEvent(new CustomEvent('mm_auth_expired', { detail: { endpoint } }));
                    } catch (e) {}
                }

                const errorMessage = data.message || data.error || (typeof data === 'string' ? data : `HTTP ${response.status}: ${response.statusText}`);
                const error = new Error(errorMessage);
                error.status = response.status;
                error.data = data;
                throw error;
            }

            return data;
        } catch (err) {
            if (timeoutId) clearTimeout(timeoutId);
            if (err.name === 'AbortError') {
                const timeoutErr = new Error(`Request timed out after ${timeoutMs / 1000} seconds. Please check your network.`);
                timeoutErr.status = 408;
                throw timeoutErr;
            }
            console.error(`[MahtoMech API] ${options.method || 'GET'} ${endpoint} failed:`, err);
            throw err;
        }
    }

    // Token & Auth State
    function getToken() {
        try {
            return localStorage.getItem(TOKEN_KEY);
        } catch (e) {
            return null;
        }
    }

    function setToken(token) {
        try {
            if (token) localStorage.setItem(TOKEN_KEY, token);
            else localStorage.removeItem(TOKEN_KEY);
        } catch (e) {}
    }

    function getUser() {
        try {
            const raw = localStorage.getItem(USER_KEY);
            return raw ? JSON.parse(raw) : null;
        } catch (e) {
            return null;
        }
    }

    function setUser(user) {
        try {
            if (user) localStorage.setItem(USER_KEY, JSON.stringify(user));
            else localStorage.removeItem(USER_KEY);
        } catch (e) {}
    }

    function isAuthenticated() {
        return Boolean(getToken());
    }

    function logout() {
        setToken(null);
        setUser(null);
        window.location.href = 'login.html';
    }

    // API Namespaces
    const MahtoMechAPI = {
        BASE_URL: API_BASE_URL,
        getToken,
        setToken,
        getUser,
        setUser,
        isAuthenticated,
        logout,
        request,

        // Health check
        health: () => request('/health'),

        // Authentication
        auth: {
            register: async (userData) => {
                const res = await request('/auth/register', {
                    method: 'POST',
                    body: userData
                });
                if (res.data && res.data.token) {
                    setToken(res.data.token);
                    setUser(res.data.user);
                }
                return res;
            },
            login: async (credentials) => {
                const res = await request('/auth/login', {
                    method: 'POST',
                    body: credentials
                });
                if (res.data && res.data.token) {
                    setToken(res.data.token);
                    setUser(res.data.user);
                }
                return res;
            },
            adminLogin: async (credentials) => {
                const res = await request('/auth/admin/login', {
                    method: 'POST',
                    body: credentials
                });
                if (res.data && res.data.token) {
                    setToken(res.data.token);
                    setUser(res.data.admin);
                }
                return res;
            }
        },

        // User Profile & Dashboard
        users: {
            getProfile: () => request('/users/profile'),
            updateProfile: (data) => request('/users/profile', { method: 'PUT', body: data }),
            changePassword: (passwords) => request('/users/change-password', { method: 'PUT', body: passwords }),
            getDashboard: () => request('/users/dashboard')
        },

        // Vehicles
        vehicles: {
            getAll: () => request('/vehicles'),
            getById: (id) => request(`/vehicles/${id}`),
            create: (data) => request('/vehicles', { method: 'POST', body: data }),
            update: (id, data) => request(`/vehicles/${id}`, { method: 'PUT', body: data }),
            delete: (id) => request(`/vehicles/${id}`, { method: 'DELETE' })
        },

        // Services
        services: {
            getAll: (params = {}) => {
                const query = new URLSearchParams(params).toString();
                return request(`/services${query ? '?' + query : ''}`);
            },
            getCategories: () => request('/services/categories'),
            getById: (id) => request(`/services/${id}`)
        },

        // Service Bookings
        bookings: {
            getAll: () => request('/bookings'),
            getById: (id) => request(`/bookings/${id}`),
            create: (data) => request('/bookings', { method: 'POST', body: data }),
            cancel: (id) => request(`/bookings/${id}/cancel`, { method: 'PUT' })
        },

        // Products & Parts Catalog
        products: {
            getAll: (params = {}) => {
                const query = new URLSearchParams(params).toString();
                return request(`/products${query ? '?' + query : ''}`);
            },
            getById: (id) => request(`/products/${id}`),
            getBySku: (sku) => request(`/products/sku/${encodeURIComponent(sku)}`)
        },

        // Product Categories
        categories: {
            getAll: () => request('/categories'),
            getBySlug: (slug) => request(`/categories/${slug}`)
        },

        // Cart
        cart: {
            get: () => request('/cart'),
            addItem: (productId, quantity = 1) => request('/cart/items', {
                method: 'POST',
                body: { product_id: productId, quantity }
            }),
            updateItem: (productId, quantity) => request(`/cart/items/${productId}`, {
                method: 'PUT',
                body: { quantity }
            }),
            removeItem: (productId) => request(`/cart/items/${productId}`, {
                method: 'DELETE'
            }),
            clear: () => request('/cart', { method: 'DELETE' })
        },

        // Shipping Addresses
        addresses: {
            getAll: () => request('/addresses'),
            getById: (id) => request(`/addresses/${id}`),
            create: (data) => request('/addresses', { method: 'POST', body: data }),
            update: (id, data) => request(`/addresses/${id}`, { method: 'PUT', body: data }),
            setDefault: (id) => request(`/addresses/${id}/default`, { method: 'PUT' }),
            delete: (id) => request(`/addresses/${id}`, { method: 'DELETE' })
        },

        // Orders
        orders: {
            getAll: (params = {}) => {
                const query = new URLSearchParams(params).toString();
                return request(`/orders${query ? '?' + query : ''}`);
            },
            getById: (id) => request(`/orders/${id}`),
            create: (orderData) => request('/orders/checkout', { method: 'POST', body: orderData }),
            checkout: (orderData) => request('/orders/checkout', { method: 'POST', body: orderData }),
            buyNow: (buyNowData) => request('/orders/buy-now', { method: 'POST', body: buyNowData }),
            cancel: (id, reason) => request(`/orders/${id}/cancel`, {
                method: 'PUT',
                body: { reason }
            })
        },

        // Payments
        payments: {
            createOrder: (orderId) => request('/payments/create-order', {
                method: 'POST',
                body: { order_id: orderId }
            }),
            verify: (paymentData) => request('/payments/verify', {
                method: 'POST',
                body: paymentData
            }),
            reportFailure: (orderId, errorDescription) => request('/payments/failed', {
                method: 'POST',
                body: { order_id: orderId, error_description: errorDescription }
            })
        },

        // Contact Messages
        contact: {
            submit: (data) => request('/contact', { method: 'POST', body: data })
        },

        // Notifications
        notifications: {
            getAll: () => request('/notifications'),
            markAsRead: (id) => request(`/notifications/${id}/read`, { method: 'PUT' }),
            markAllAsRead: () => request('/notifications/read-all', { method: 'PUT' }),
            delete: (id) => request(`/notifications/${id}`, { method: 'DELETE' })
        },

        // Admin Management
        admin: {
            getStats: () => request('/admin/dashboard'),
            getUsers: (params = {}) => {
                const query = new URLSearchParams(params).toString();
                return request(`/admin/users${query ? '?' + query : ''}`);
            },
            getUserDetails: (id) => request(`/admin/users/${id}`),
            updateUserStatus: (id, isActive) => request(`/admin/users/${id}/status`, {
                method: 'PUT',
                body: { is_active: isActive }
            }),
            getAllOrders: (params = {}) => {
                const query = new URLSearchParams(params).toString();
                return request(`/orders/admin/all${query ? '?' + query : ''}`);
            },
            updateOrderStatus: (id, statusData) => request(`/orders/${id}/status`, {
                method: 'PUT',
                body: statusData
            }),
            getAllBookings: (params = {}) => {
                const query = new URLSearchParams(params).toString();
                return request(`/bookings/admin/all${query ? '?' + query : ''}`);
            },
            updateBookingStatus: (id, statusData) => request(`/bookings/${id}/status`, {
                method: 'PUT',
                body: statusData
            }),
            createService: (data) => request('/services', { method: 'POST', body: data }),
            updateService: (id, data) => request(`/services/${id}`, { method: 'PUT', body: data }),
            deleteService: (id) => request(`/services/${id}`, { method: 'DELETE' }),
            createProduct: (data) => request('/products', { method: 'POST', body: data }),
            updateProduct: (id, data) => request(`/products/${id}`, { method: 'PUT', body: data }),
            deleteProduct: (id) => request(`/products/${id}`, { method: 'DELETE' })
        }
    };

    window.MahtoMechAPI = MahtoMechAPI;

})(window);
