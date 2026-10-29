/* ==========================================================================
   MahtoMech Admin Panel — Vehicles Module
   GET /api/admin/vehicles
   ========================================================================== */

let vehiclesPage = 1;
let vehiclesTypeFilter = '';

async function loadVehicles() {
    tableLoading('vehiclesBody', 6);

    const res = await API.vehicles.list({
        vehicle_type: vehiclesTypeFilter,
        page:         vehiclesPage,
        limit:        15
    });

    if (!res || !res.ok) {
        tableError('vehiclesBody', 6, res?.data?.message || 'Failed to load vehicles.');
        return;
    }

    const d = res.data.data || res.data || {};
    const vehicles   = d.vehicles || d.items || d || [];
    const total      = d.total    || d.count || vehicles.length;
    const totalPages = d.total_pages || Math.ceil(total / 15) || 1;

    if (!vehicles.length) {
        tableEmpty('vehiclesBody', 6, '🚗', 'No vehicles registered.');
        buildPagination('vehiclesPagination', 'vehiclesPaginInfo', 1, 1, 0, () => {});
        return;
    }

    const TYPE_ICON = { car: '🚗', bike: '🏍️', truck: '🚛', tractor: '🚜', other: '🚙' };

    document.getElementById('vehiclesBody').innerHTML = vehicles.map(v => `
        <tr>
            <td>
                <span style="font-size:1.2rem;margin-right:8px">${TYPE_ICON[v.vehicle_type] || '🚙'}</span>
                <span class="table-cell-bold">${escHtml(v.brand || '')} ${escHtml(v.model || '')}</span>
            </td>
            <td class="table-cell-code">${escHtml(v.registration_number || v.reg_number || '—')}</td>
            <td>
                <span class="badge badge-neutral">${escHtml(v.vehicle_type || '—')}</span>
            </td>
            <td>
                <div class="table-cell-bold">${escHtml(v.owner_name || v.customer_name || v.full_name || '—')}</div>
                <div style="font-size:0.75rem;color:var(--text-muted)">${escHtml(v.owner_email || v.customer_email || v.email || '')}</div>
            </td>
            <td>${v.year || '—'}</td>
            <td>${fmtDate(v.created_at)}</td>
        </tr>
    `).join('');

    buildPagination('vehiclesPagination', 'vehiclesPaginInfo', vehiclesPage, totalPages, total, (pg) => {
        vehiclesPage = pg;
        loadVehicles();
    });
}

// ── Filter ────────────────────────────────────────────────────────────────────
document.getElementById('vehicleTypeFilter')?.addEventListener('change', (e) => {
    vehiclesTypeFilter = e.target.value;
    vehiclesPage       = 1;
    loadVehicles();
});

// ── Register ──────────────────────────────────────────────────────────────────
SECTION_LOADERS['vehicles'] = loadVehicles;

