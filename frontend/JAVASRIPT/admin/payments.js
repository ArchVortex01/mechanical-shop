/* ==========================================================================
   MahtoMech Admin Panel — Payments Module
   GET /api/admin/payments
   ========================================================================== */

let paymentsPage = 1;
let paymentsSearch = '';
let paymentsStatusFilter = '';

async function loadPayments() {
    tableLoading('paymentsBody', 7);

    const res = await API.payments.list({
        search: paymentsSearch,
        status: paymentsStatusFilter,
        page:   paymentsPage,
        limit:  15
    });

    if (!res || !res.ok) {
        tableError('paymentsBody', 7, res?.data?.message || 'Failed to load payments.');
        return;
    }

    const d = res.data.data || res.data || {};
    const payments   = d.payments || d.items || d || [];
    const total      = d.total    || d.count || payments.length;
    const totalPages = d.total_pages || Math.ceil(total / 15) || 1;

    if (!payments.length) {
        tableEmpty('paymentsBody', 7, '💳', 'No payment records found.');
        buildPagination('paymentsPagination', 'paymentsPaginInfo', 1, 1, 0, () => {});
        return;
    }

    document.getElementById('paymentsBody').innerHTML = payments.map(p => `
        <tr>
            <td class="table-cell-code" style="font-size:0.78rem">${escHtml(p.razorpay_payment_id || p.payment_id || '—')}</td>
            <td class="table-cell-code">#${escHtml(p.order_number || p.order_id)}</td>
            <td>
                <div class="table-cell-bold">${escHtml(p.customer_name || p.full_name || '—')}</div>
                <div style="font-size:0.75rem;color:var(--text-muted)">${escHtml(p.customer_email || p.email || '')}</div>
            </td>
            <td class="table-cell-bold">${fmtCurrency(p.amount)}</td>
            <td>${statusBadge(p.payment_status || p.status)}</td>
            <td>${escHtml(p.payment_method || p.method || '—')}</td>
            <td>${fmtDateTime(p.paid_at || p.created_at)}</td>
        </tr>
    `).join('');

    buildPagination('paymentsPagination', 'paymentsPaginInfo', paymentsPage, totalPages, total, (pg) => {
        paymentsPage = pg;
        loadPayments();
    });
}

// ── Search & Filter ───────────────────────────────────────────────────────────
document.getElementById('paymentSearch')?.addEventListener('input', debounce((e) => {
    paymentsSearch = e.target.value.trim();
    paymentsPage   = 1;
    loadPayments();
}));

document.getElementById('paymentStatusFilter')?.addEventListener('change', (e) => {
    paymentsStatusFilter = e.target.value;
    paymentsPage         = 1;
    loadPayments();
});

// ── Register ──────────────────────────────────────────────────────────────────
SECTION_LOADERS['payments'] = loadPayments;

