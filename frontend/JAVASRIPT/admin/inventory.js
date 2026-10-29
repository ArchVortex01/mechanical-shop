/* ==========================================================================
   MahtoMech Admin Panel — Inventory Module
   GET /api/admin/inventory  |  PUT /api/admin/inventory/:id
   ========================================================================== */

let inventoryStockFilter = '';

async function loadInventory() {
    tableLoading('inventoryBody', 5);

    const res = await API.inventory.list({ stock_status: inventoryStockFilter });

    if (!res || !res.ok) {
        tableError('inventoryBody', 5, res?.data?.message || 'Failed to load inventory.');
        return;
    }

    const d = res.data.data || res.data || {};
    const items   = d.products || d.items || d || [];
    const summary = d.summary  || {};

    // Summary counts
    setText('inv-out', summary.out_of_stock ?? '—');
    setText('inv-low', summary.low_stock    ?? '—');
    setText('inv-in',  summary.in_stock     ?? '—');

    if (!items.length) {
        tableEmpty('inventoryBody', 5, '📦', 'No inventory records found.');
        return;
    }

    document.getElementById('inventoryBody').innerHTML = items.map(p => {
        const qty    = p.stock_quantity ?? 0;
        const status = qty === 0 ? 'out_of_stock' : qty < 10 ? 'low_stock' : 'in_stock';
        return `
        <tr>
            <td>
                <div class="table-cell-bold">${escHtml(p.name)}</div>
                <div style="font-size:0.75rem;color:var(--text-muted)">${escHtml(p.sku || '—')}</div>
            </td>
            <td>${escHtml(p.category_name || p.category || '—')}</td>
            <td>
                <span style="font-size:1rem;font-weight:700;color:${qty === 0 ? 'var(--status-danger)' : qty < 10 ? 'var(--status-warning)' : 'var(--status-success)'}">
                    ${qty}
                </span>
            </td>
            <td>${statusBadge(status)}</td>
            <td>
                <button class="btn btn-outline btn-sm" onclick="openStockModal(${p.id}, '${escHtml(p.name)}', ${qty})">
                    📝 Update
                </button>
            </td>
        </tr>
    `;
    }).join('');
}

// ── Stock Update Modal ────────────────────────────────────────────────────────
function openStockModal(id, name, currentQty) {
    document.getElementById('stockProductId').value   = id;
    document.getElementById('stockProductName').textContent = name;
    document.getElementById('stockQty').value         = currentQty;
    openModal('stockModal');
}

document.getElementById('saveStockBtn')?.addEventListener('click', async () => {
    const id  = document.getElementById('stockProductId').value;
    const qty = parseInt(document.getElementById('stockQty').value);

    if (isNaN(qty) || qty < 0) {
        toast.warning('Validation', 'Stock quantity must be 0 or more.');
        return;
    }

    const btn = document.getElementById('saveStockBtn');
    btn.disabled = true; btn.textContent = 'Updating…';

    const res = await API.inventory.updateStock(id, qty);

    btn.disabled = false; btn.textContent = 'Update Stock';

    if (!res || !res.ok) {
        toast.error('Update Failed', res?.data?.message || 'Could not update stock.');
        return;
    }
    toast.success('Stock Updated', `Stock set to ${qty} units.`);
    closeModal('stockModal');
    loadInventory();
});

// ── Filter ────────────────────────────────────────────────────────────────────
document.getElementById('stockFilter')?.addEventListener('change', (e) => {
    inventoryStockFilter = e.target.value;
    loadInventory();
});

// ── Helper (shares setText from dashboard.js — safe since both loaded) ────────
function setText(id, val) {
    const el = document.getElementById(id);
    if (el) el.textContent = val ?? '—';
}

// ── Register ──────────────────────────────────────────────────────────────────
SECTION_LOADERS['inventory'] = loadInventory;

