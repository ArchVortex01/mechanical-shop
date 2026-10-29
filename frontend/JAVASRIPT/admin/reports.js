/* ==========================================================================
   MahtoMech Admin Panel — Reports Module
   GET /api/admin/reports
   ========================================================================== */

async function loadReports() {
    // Reset stat cards
    ['rpt-today-rev','rpt-month-rev','rpt-today-orders','rpt-month-orders'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.textContent = '…';
    });
    document.getElementById('topProductsList').innerHTML = '<p style="color:var(--text-muted)">Loading…</p>';
    document.getElementById('ordersByStatus').innerHTML  = '<p style="color:var(--text-muted)">Loading…</p>';

    const res = await API.reports.sales();

    if (!res || !res.ok) {
        toast.error('Reports Error', res?.data?.message || 'Failed to load reports.');
        document.getElementById('topProductsList').innerHTML = '<p style="color:var(--status-danger)">⚠️ Could not load report data.</p>';
        document.getElementById('ordersByStatus').innerHTML  = '<p style="color:var(--status-danger)">⚠️ Could not load report data.</p>';
        return;
    }

    const d = res.data.data || res.data || {};

    // ── Revenue stats ────────────────────────────────────────────────────────
    const daily   = d.daily_sales   || {};
    const monthly = d.monthly_sales || {};

    setTextEl('rpt-today-rev',   fmtCurrency(daily.revenue   || daily.total_revenue  || 0));
    setTextEl('rpt-month-rev',   fmtCurrency(monthly.revenue || monthly.total_revenue || 0));
    setTextEl('rpt-today-orders',  daily.orders   ?? daily.total_orders   ?? '0');
    setTextEl('rpt-month-orders',  monthly.orders ?? monthly.total_orders ?? '0');

    // ── Top Products ─────────────────────────────────────────────────────────
    const topProducts = d.top_products || [];
    const topEl = document.getElementById('topProductsList');
    if (!topProducts.length) {
        topEl.innerHTML = '<p style="color:var(--text-muted);font-size:0.88rem">No sales data available yet.</p>';
    } else {
        topEl.innerHTML = topProducts.map((p, i) => `
            <div style="display:flex;align-items:center;gap:12px;padding:10px 0;border-bottom:1px solid var(--border-subtle)">
                <span style="width:28px;height:28px;background:var(--primary-light);border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:0.8rem;font-weight:700;color:var(--primary);flex-shrink:0">${i + 1}</span>
                <div style="flex:1;overflow:hidden">
                    <div style="font-weight:600;color:var(--text-primary);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${escHtml(p.name)}</div>
                    <div style="font-size:0.76rem;color:var(--text-muted)">${p.total_sold || p.quantity_sold || 0} sold</div>
                </div>
                <div style="font-weight:700;color:var(--primary);white-space:nowrap">${fmtCurrency(p.total_revenue || p.revenue || 0)}</div>
            </div>
        `).join('');
    }

    // ── Orders by Status ─────────────────────────────────────────────────────
    const ordersByStatus = d.orders_by_status || [];
    const statusEl = document.getElementById('ordersByStatus');
    if (!ordersByStatus.length) {
        statusEl.innerHTML = '<p style="color:var(--text-muted);font-size:0.88rem">No order data available yet.</p>';
    } else {
        const STATUS_COLORS = {
            pending:    'var(--status-warning)',
            confirmed:  'var(--status-info)',
            processing: 'var(--status-purple)',
            shipped:    'var(--status-info)',
            delivered:  'var(--status-success)',
            cancelled:  'var(--status-danger)'
        };
        statusEl.innerHTML = ordersByStatus.map(s => `
            <div style="display:flex;align-items:center;justify-content:space-between;padding:10px 0;border-bottom:1px solid var(--border-subtle)">
                <div style="display:flex;align-items:center;gap:10px">
                    <span style="width:10px;height:10px;border-radius:50%;background:${STATUS_COLORS[s.status] || 'var(--text-muted)'}"></span>
                    <span style="text-transform:capitalize;font-weight:500;color:var(--text-secondary)">${escHtml(s.status || '—')}</span>
                </div>
                <span style="font-weight:700;color:var(--text-primary)">${s.count || s.total || 0}</span>
            </div>
        `).join('');
    }
}

function setTextEl(id, val) {
    const el = document.getElementById(id);
    if (el) el.textContent = val ?? '—';
}

// ── Register ──────────────────────────────────────────────────────────────────
SECTION_LOADERS['reports'] = loadReports;

