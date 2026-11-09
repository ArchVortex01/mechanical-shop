/* ==========================================================================
   MahtoMech Admin Panel — Dashboard
   Connects stat cards and recent orders table to GET /api/admin/dashboard
   ========================================================================== */

async function loadDashboard() {
    // Set stat cards to loading
    ['stat-revenue','stat-orders','stat-bookings','stat-users','stat-products','stat-messages'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.textContent = '…';
    });

    tableLoading('recentOrdersBody', 5, '⏳ Loading recent orders...');

    const res = await API.dashboard.stats();

    if (!res || !res.ok) {
        toast.error('Dashboard Error', res?.data?.message || 'Failed to load dashboard data.');
        tableError('recentOrdersBody', 5, 'Could not load recent orders.');
        return;
    }

    const d = res.data.data || {};

    // ── Stat Cards ──────────────────────────────────────────────────────────
    setText('stat-revenue',  fmtCurrency(d.total_revenue || 0));
    setText('stat-orders',   d.total_orders    ?? '0');
    setText('stat-bookings', d.total_bookings  ?? '0');
    setText('stat-users',    d.total_users     ?? '0');
    setText('stat-products', d.total_products  ?? '0');
    setText('stat-messages', d.total_messages  ?? '0');

    // Sub-texts
    setText('stat-orders-today',   d.orders_today   != null ? `${d.orders_today} today`   : '');
    setText('stat-bookings-today', d.bookings_today != null ? `${d.bookings_today} today` : '');
    setText('stat-users-new',      d.new_users      != null ? `${d.new_users} new`        : '');
    setText('stat-messages-new',   d.new_messages   != null ? `${d.new_messages} unread`  : '');

    // Low stock badge in sidebar
    const lowStock = d.low_stock_products || 0;
    setText('stat-low-stock', `${lowStock} low stock`);
    const badge = document.getElementById('lowStockBadge');
    if (badge) {
        badge.style.display = lowStock > 0 ? 'inline-flex' : 'none';
        badge.textContent   = lowStock;
    }

    // Message badge
    const newMsgs = d.new_messages || 0;
    const msgBadge = document.getElementById('msgBadge');
    if (msgBadge) {
        msgBadge.style.display = newMsgs > 0 ? 'inline-flex' : 'none';
    }

    // ── Recent Orders ───────────────────────────────────────────────────────
    const orders = d.recent_orders || [];
    if (!orders.length) {
        tableEmpty('recentOrdersBody', 5, '🛍️', 'No orders yet.');
        return;
    }

    const tbody = document.getElementById('recentOrdersBody');
    if (!tbody) return;
    tbody.innerHTML = orders.map(o => `
        <tr>
            <td class="table-cell-code">#${escHtml(o.order_number || o.id)}</td>
            <td>${escHtml(o.customer_name || o.full_name || '—')}</td>
            <td class="table-cell-bold">${fmtCurrency(o.total_amount || o.grand_total)}</td>
            <td>${statusBadge(o.order_status || o.status)}</td>
            <td>${fmtDate(o.created_at)}</td>
        </tr>
    `).join('');
}

// ── Helper ────────────────────────────────────────────────────────────────────
function setText(id, val) {
    const el = document.getElementById(id);
    if (el) el.textContent = val ?? '—';
}

// ── Register with app router ──────────────────────────────────────────────────
SECTION_LOADERS['dashboard'] = loadDashboard;

