/* ==========================================================================
   MahtoMech Admin Panel — Central API Client
   All backend communication goes through this file.
   ========================================================================== */

const API_BASE_URL = window.MAHTOMECH_API_BASE_URL ||
    (function() {
        try {
            const custom = localStorage.getItem('mm_api_base_url');
            if (custom) return custom.replace(/\/+$/, '');
        } catch (e) {}
        if (window.location && window.location.protocol.startsWith('http')) {
            if (window.location.port === '8000' || window.location.port === '') {
                return '/api';
            }
        }
        return 'http://localhost:8000/api';
    })();

// ── Auth helpers ─────────────────────────────────────────────────────────────
function getToken() {
    return localStorage.getItem('adminToken') || localStorage.getItem('mm_auth_token');
}

function getAuthHeaders(isJson = true) {
    const headers = {};
    if (isJson) headers['Content-Type'] = 'application/json';
    const token = getToken();
    if (token) headers['Authorization'] = `Bearer ${token}`;
    return headers;
}

// ── Core request wrapper ─────────────────────────────────────────────────────
async function apiRequest(method, endpoint, body = null) {
    const options = {
        method,
        headers: getAuthHeaders()
    };
    if (body) options.body = JSON.stringify(body);

    try {
        const res = await fetch(`${API_BASE_URL}${endpoint}`, options);

        // Token expired / unauthorized
        if (res.status === 401) {
            localStorage.removeItem('adminToken');
            localStorage.removeItem('adminUser');
            localStorage.removeItem('mm_auth_token');
            localStorage.removeItem('mm_auth_user');
            window.location.href = 'login.html';
            return;
        }

        const data = await res.json();
        return { ok: res.ok, status: res.status, data };
    } catch (err) {
        console.error(`API Error [${method} ${endpoint}]:`, err);
        return { ok: false, status: 0, data: { success: false, message: 'Cannot connect to server. Is the backend running?' } };
    }
}

// ── Convenience methods ──────────────────────────────────────────────────────
const API = {
    get:    (ep)         => apiRequest('GET',    ep),
    post:   (ep, body)   => apiRequest('POST',   ep, body),
    put:    (ep, body)   => apiRequest('PUT',    ep, body),
    patch:  (ep, body)   => apiRequest('PATCH',  ep, body),
    delete: (ep)         => apiRequest('DELETE', ep),

    // ── Auth ──────────────────────────────────────────────────────────────────
    auth: {
        adminLogin: (email, password) =>
            apiRequest('POST', '/auth/admin/login', { email, password })
    },

    // ── Dashboard ─────────────────────────────────────────────────────────────
    dashboard: {
        stats: () => API.get('/admin/dashboard')
    },

    // ── Users ─────────────────────────────────────────────────────────────────
    users: {
        list:       (params = {}) => API.get('/admin/users' + buildQuery(params)),
        getById:    (id)          => API.get(`/admin/users/${id}`),
        setStatus:  (id, is_active) => API.put(`/admin/users/${id}/status`, { is_active })
    },

    // ── Products ──────────────────────────────────────────────────────────────
    products: {
        list:   (params = {}) => API.get('/products' + buildQuery(params)),
        create: (body)        => API.post('/products', body),
        update: (id, body)    => API.put(`/products/${id}`, body),
        remove: (id)          => API.delete(`/products/${id}`)
    },

    // ── Categories ────────────────────────────────────────────────────────────
    categories: {
        list:   ()         => API.get('/categories'),
        create: (body)     => API.post('/categories', body),
        update: (id, body) => API.put(`/categories/${id}`, body),
        remove: (id)       => API.delete(`/categories/${id}`)
    },

    // ── Inventory ─────────────────────────────────────────────────────────────
    inventory: {
        list:        (params = {}) => API.get('/admin/inventory' + buildQuery(params)),
        updateStock: (id, stock_quantity) => API.put(`/admin/inventory/${id}`, { stock_quantity })
    },

    // ── Orders ────────────────────────────────────────────────────────────────
    orders: {
        list:         (params = {}) => API.get('/orders/admin/all' + buildQuery(params)),
        updateStatus: (id, body)    => API.put(`/orders/${id}/status`, body)
    },

    // ── Payments ──────────────────────────────────────────────────────────────
    payments: {
        list: (params = {}) => API.get('/admin/payments' + buildQuery(params))
    },

    // ── Services ─────────────────────────────────────────────────────────────
    services: {
        list:   (params = {}) => API.get('/services' + buildQuery(params)),
        create: (body)        => API.post('/services', body),
        update: (id, body)    => API.put(`/services/${id}`, body),
        remove: (id)          => API.delete(`/services/${id}`)
    },

    // ── Bookings ─────────────────────────────────────────────────────────────
    bookings: {
        list:         (params = {}) => API.get('/bookings/admin/all' + buildQuery(params)),
        updateStatus: (id, body)    => API.put(`/bookings/${id}/status`, body)
    },

    // ── Vehicles ─────────────────────────────────────────────────────────────
    vehicles: {
        list: (params = {}) => API.get('/admin/vehicles' + buildQuery(params))
    },

    // ── Reports ───────────────────────────────────────────────────────────────
    reports: {
        sales: () => API.get('/admin/reports')
    },

    // ── Contact / Messages ────────────────────────────────────────────────────
    messages: {
        list:         (params = {}) => API.get('/contact/admin/all' + buildQuery(params)),
        updateStatus: (id, body)    => API.put(`/contact/admin/${id}/status`, body),
        remove:       (id)          => API.delete(`/contact/admin/${id}`)
    }
};

// ── Query string builder ─────────────────────────────────────────────────────
function buildQuery(params) {
    const clean = Object.entries(params).filter(([, v]) => v !== '' && v != null);
    if (!clean.length) return '';
    return '?' + clean.map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`).join('&');
}

