/* ==========================================================================
   MahtoMech Admin Panel — Services Module
   GET /api/services  |  POST /api/services  |  PUT /api/services/:id  |  DELETE /api/services/:id
   ========================================================================== */

async function loadServices() {
    tableLoading('servicesBody', 6);

    const res = await API.services.list({ limit: 100 });

    if (!res || !res.ok) {
        tableError('servicesBody', 6, res?.data?.message || 'Failed to load services.');
        return;
    }

    const services = res.data.data || res.data.services || res.data || [];

    if (!services.length) {
        tableEmpty('servicesBody', 6, '🔧', 'No services found. Add your first service.');
        return;
    }

    document.getElementById('servicesBody').innerHTML = services.map(s => `
        <tr>
            <td>
                <div class="table-cell-bold">${escHtml(s.name)}</div>
                ${s.description ? `<div style="font-size:0.75rem;color:var(--text-muted);max-width:240px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${escHtml(s.description)}</div>` : ''}
            </td>
            <td>${escHtml(s.category || s.service_category || '—')}</td>
            <td class="table-cell-bold">${fmtCurrency(s.base_price || s.price)}</td>
            <td>${s.duration_minutes ? `${s.duration_minutes} min` : '—'}</td>
            <td>${statusBadge(s.is_active !== false ? 'active' : 'inactive')}</td>
            <td>
                <div class="table-actions">
                    <button class="btn btn-secondary btn-icon btn-sm" title="Edit" onclick="editService(${s.id})">✏️</button>
                    <button class="btn btn-danger btn-icon btn-sm" title="Delete" onclick="deleteService(${s.id}, '${escHtml(s.name)}')">🗑️</button>
                </div>
            </td>
        </tr>
    `).join('');
}

// ── Add Service ───────────────────────────────────────────────────────────────
document.getElementById('addServiceBtn')?.addEventListener('click', () => {
    document.getElementById('serviceModalTitle').textContent = 'Add Service';
    document.getElementById('serviceForm').reset();
    document.getElementById('serviceId').value = '';
    document.getElementById('svcIsActive').checked = true;
    openModal('serviceModal');
});

// ── Edit Service ──────────────────────────────────────────────────────────────
async function editService(id) {
    document.getElementById('serviceModalTitle').textContent = 'Edit Service';
    document.getElementById('serviceId').value = id;

    const res = await API.get(`/services/${id}`);
    if (!res || !res.ok) { toast.error('Error', 'Could not load service details.'); return; }
    const s = res.data.data || res.data.service || res.data;

    document.getElementById('svcName').value        = s.name || '';
    document.getElementById('svcCategory').value    = s.category || s.service_category || '';
    document.getElementById('svcDescription').value = s.description || '';
    document.getElementById('svcPrice').value       = s.base_price || s.price || '';
    document.getElementById('svcDuration').value    = s.duration_minutes || '';
    document.getElementById('svcIsActive').checked  = s.is_active !== false;

    openModal('serviceModal');
}

// ── Save Service ──────────────────────────────────────────────────────────────
document.getElementById('saveServiceBtn')?.addEventListener('click', async () => {
    const id    = document.getElementById('serviceId').value;
    const name  = document.getElementById('svcName').value.trim();
    const price = parseFloat(document.getElementById('svcPrice').value);

    if (!name)        { toast.warning('Validation', 'Service name is required.'); return; }
    if (isNaN(price)) { toast.warning('Validation', 'Valid base price is required.'); return; }

    const body = {
        name,
        category:         document.getElementById('svcCategory').value.trim(),
        description:      document.getElementById('svcDescription').value.trim(),
        base_price:       price,
        duration_minutes: parseInt(document.getElementById('svcDuration').value) || null,
        is_active:        document.getElementById('svcIsActive').checked
    };

    const btn = document.getElementById('saveServiceBtn');
    btn.disabled = true; btn.textContent = 'Saving…';

    const res = id
        ? await API.services.update(id, body)
        : await API.services.create(body);

    btn.disabled = false; btn.textContent = 'Save Service';

    if (!res || !res.ok) {
        toast.error('Save Failed', res?.data?.message || 'Could not save service.');
        return;
    }
    toast.success('Success', `Service ${id ? 'updated' : 'created'} successfully.`);
    closeModal('serviceModal');
    loadServices();
});

// ── Delete Service ────────────────────────────────────────────────────────────
function deleteService(id, name) {
    confirmAction('Delete Service', `Delete service "${name}"?`, async () => {
        const res = await API.services.remove(id);
        if (!res || !res.ok) { toast.error('Delete Failed', res?.data?.message || 'Could not delete service.'); return; }
        toast.success('Deleted', `Service "${name}" removed.`);
        loadServices();
    });
}

// ── Register ──────────────────────────────────────────────────────────────────
SECTION_LOADERS['services'] = loadServices;

