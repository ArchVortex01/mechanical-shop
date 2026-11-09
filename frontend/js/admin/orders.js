/* ==========================================================================
   MahtoMech Admin Panel — Orders Module
   GET /api/orders/admin/all  |  PUT /api/orders/:id/status
   ========================================================================== */

let ordersPage = 1;
let ordersSearch = '';
let ordersStatusFilter = '';

async function loadOrders() {
    tableLoading('ordersBody', 7);

    const res = await API.orders.list({
        search:       ordersSearch,
        order_status: ordersStatusFilter,
        page:         ordersPage,
        limit:        15
    });

    if (!res || !res.ok) {
        tableError('ordersBody', 7, res?.data?.message || 'Failed to load orders.');
        return;
    }

    const d = res.data.data || res.data || {};
    const orders     = d.orders || d.items || d || [];
    const total      = d.total  || d.count || orders.length;
    const totalPages = d.total_pages || Math.ceil(total / 15) || 1;

    if (!orders.length) {
        tableEmpty('ordersBody', 7, '🛍️', 'No orders found.');
        buildPagination('ordersPagination', 'ordersPaginInfo', 1, 1, 0, () => {});
        return;
    }

    document.getElementById('ordersBody').innerHTML = orders.map(o => `
        <tr>
            <td class="table-cell-code">#${escHtml(o.order_number || o.id)}</td>
            <td>
                <div class="table-cell-bold">${escHtml(o.customer_name || o.full_name || '—')}</div>
                <div style="font-size:0.75rem;color:var(--text-muted)">${escHtml(o.customer_email || o.email || '')}</div>
            </td>
            <td class="table-cell-bold">${fmtCurrency(o.grand_total || o.total_amount)}</td>
            <td>${statusBadge(o.order_status || o.status)}</td>
            <td>${statusBadge(o.payment_status)}</td>
            <td>${fmtDate(o.created_at)}</td>
            <td>
                <button class="btn btn-outline btn-sm" onclick="openOrderModal(${o.id}, '${escHtml(o.order_number || o.id)}', '${o.order_status || o.status}', '${o.payment_status}')">
                    ✏️ Update
                </button>
            </td>
        </tr>
    `).join('');

    buildPagination('ordersPagination', 'ordersPaginInfo', ordersPage, totalPages, total, (pg) => {
        ordersPage = pg;
        loadOrders();
    });
}

// ── Order Update Modal ────────────────────────────────────────────────────────
function openOrderModal(id, ref, orderStatus, paymentStatus) {
    document.getElementById('orderId').value          = id;
    document.getElementById('orderModalRef').textContent = ref;
    document.getElementById('orderStatusUpdate').value   = orderStatus || 'pending';
    document.getElementById('orderPaymentUpdate').value  = paymentStatus || 'pending';
    document.getElementById('orderNotes').value          = '';
    openModal('orderModal');
}

document.getElementById('saveOrderBtn')?.addEventListener('click', async () => {
    const id = document.getElementById('orderId').value;
    const body = {
        order_status:   document.getElementById('orderStatusUpdate').value,
        payment_status: document.getElementById('orderPaymentUpdate').value,
        notes:          document.getElementById('orderNotes').value.trim()
    };

    const btn = document.getElementById('saveOrderBtn');
    btn.disabled = true; btn.textContent = 'Updating…';

    const res = await API.orders.updateStatus(id, body);

    btn.disabled = false; btn.textContent = 'Update Order';

    if (!res || !res.ok) {
        toast.error('Update Failed', res?.data?.message || 'Could not update order.');
        return;
    }
    toast.success('Order Updated', 'Order status has been updated.');
    closeModal('orderModal');
    loadOrders();
});

// ── Search & Filter ───────────────────────────────────────────────────────────
document.getElementById('orderSearch')?.addEventListener('input', debounce((e) => {
    ordersSearch = e.target.value.trim();
    ordersPage   = 1;
    loadOrders();
}));

document.getElementById('orderStatusFilter')?.addEventListener('change', (e) => {
    ordersStatusFilter = e.target.value;
    ordersPage         = 1;
    loadOrders();
});

// ── Register ──────────────────────────────────────────────────────────────────
SECTION_LOADERS['orders'] = loadOrders;

