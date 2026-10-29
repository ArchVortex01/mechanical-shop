/* ==========================================================================
   MahtoMech Admin Panel — Messages Module
   GET /api/contact/admin/all  |  PUT /api/contact/admin/:id/status  |  DELETE /api/contact/admin/:id
   ========================================================================== */

let messagesStatusFilter = '';

async function loadMessages() {
    tableLoading('messagesBody', 6);

    const res = await API.messages.list({ status: messagesStatusFilter });

    if (!res || !res.ok) {
        tableError('messagesBody', 6, res?.data?.message || 'Failed to load messages.');
        return;
    }

    const d = res.data.data || res.data || {};
    const messages = d.messages || d.contacts || d.items || d || [];

    if (!messages.length) {
        tableEmpty('messagesBody', 6, '✉️', 'No messages found.');
        return;
    }

    // Update sidebar badge
    const newCount = messages.filter(m => (m.status || m.contact_status) === 'new').length;
    const badge = document.getElementById('msgBadge');
    if (badge) {
        badge.style.display = newCount > 0 ? 'inline-flex' : 'none';
        badge.textContent   = newCount;
    }

    document.getElementById('messagesBody').innerHTML = messages.map(m => {
        const status  = m.status || m.contact_status || 'new';
        const preview = (m.message || '').slice(0, 60) + ((m.message || '').length > 60 ? '…' : '');
        return `
        <tr style="${status === 'new' ? 'background:rgba(255,102,0,0.04)' : ''}">
            <td>
                <div class="table-cell-bold">${escHtml(m.name || m.customer_name || '—')}</div>
                <div style="font-size:0.75rem;color:var(--text-muted)">${escHtml(m.email || '—')}</div>
            </td>
            <td style="font-weight:${status==='new'?'600':'400'}">${escHtml(m.subject || '—')}</td>
            <td style="color:var(--text-muted);font-size:0.84rem;max-width:200px">${escHtml(preview)}</td>
            <td>${statusBadge(status)}</td>
            <td>${fmtDate(m.created_at)}</td>
            <td>
                <div class="table-actions">
                    <button class="btn btn-outline btn-sm" onclick="openMessageModal(${m.id})">
                        👁️ View
                    </button>
                    <button class="btn btn-danger btn-icon btn-sm" title="Delete" onclick="deleteMessage(${m.id}, '${escHtml(m.name || '')}')">
                        🗑️
                    </button>
                </div>
            </td>
        </tr>
    `;
    }).join('');
}

// ── Message Detail Modal ──────────────────────────────────────────────────────
async function openMessageModal(id) {
    document.getElementById('messageId').value = id;
    document.getElementById('messageDetails').innerHTML = '<p style="color:var(--text-muted)">Loading…</p>';
    document.getElementById('messageResponse').value = '';
    openModal('messageModal');

    // Find from current DOM data or re-fetch list
    const res = await API.messages.list({});
    if (!res || !res.ok) return;

    const d = res.data.data || res.data || {};
    const msgs = d.messages || d.contacts || d.items || d || [];
    const m    = msgs.find(x => x.id === id);
    if (!m) return;

    const status = m.status || m.contact_status || 'new';
    document.getElementById('messageStatusUpdate').value = status;
    document.getElementById('messageResponse').value     = m.admin_response || '';

    document.getElementById('messageDetails').innerHTML = `
        <div style="display:grid;gap:12px;font-size:0.88rem">
            <div style="display:flex;gap:8px"><strong style="color:var(--text-primary);min-width:70px">From:</strong> <span>${escHtml(m.name || '—')} — ${escHtml(m.email || '')} ${m.phone ? '· ' + escHtml(m.phone) : ''}</span></div>
            <div style="display:flex;gap:8px"><strong style="color:var(--text-primary);min-width:70px">Subject:</strong> <span>${escHtml(m.subject || '—')}</span></div>
            <div style="display:flex;gap:8px"><strong style="color:var(--text-primary);min-width:70px">Date:</strong> <span>${fmtDateTime(m.created_at)}</span></div>
            <div style="background:var(--bg-surface);padding:14px;border-radius:var(--radius-md);border:1px solid var(--border-subtle);color:var(--text-secondary);line-height:1.7;white-space:pre-wrap">${escHtml(m.message || '—')}</div>
        </div>
    `;

    // Mark as read automatically if new
    if (status === 'new') {
        await API.messages.updateStatus(id, { status: 'read' });
        loadMessages();
    }
}

// ── Save Message Response ─────────────────────────────────────────────────────
document.getElementById('saveMessageBtn')?.addEventListener('click', async () => {
    const id = document.getElementById('messageId').value;
    const body = {
        status:         document.getElementById('messageStatusUpdate').value,
        admin_response: document.getElementById('messageResponse').value.trim()
    };

    const btn = document.getElementById('saveMessageBtn');
    btn.disabled = true; btn.textContent = 'Saving…';

    const res = await API.messages.updateStatus(id, body);

    btn.disabled = false; btn.textContent = 'Save Response';

    if (!res || !res.ok) {
        toast.error('Save Failed', res?.data?.message || 'Could not save response.');
        return;
    }
    toast.success('Saved', 'Message status & response updated.');
    closeModal('messageModal');
    loadMessages();
});

// ── Delete Message ────────────────────────────────────────────────────────────
function deleteMessage(id, name) {
    confirmAction('Delete Message', `Delete message from "${name}"? This cannot be undone.`, async () => {
        const res = await API.messages.remove(id);
        if (!res || !res.ok) { toast.error('Delete Failed', res?.data?.message || 'Could not delete message.'); return; }
        toast.success('Deleted', 'Message removed.');
        closeModal('messageModal');
        loadMessages();
    });
}

document.getElementById('deleteMessageBtn')?.addEventListener('click', () => {
    const id = document.getElementById('messageId').value;
    deleteMessage(id, '');
});

// ── Filter ────────────────────────────────────────────────────────────────────
document.getElementById('msgStatusFilter')?.addEventListener('change', (e) => {
    messagesStatusFilter = e.target.value;
    loadMessages();
});

// ── Register ──────────────────────────────────────────────────────────────────
SECTION_LOADERS['messages'] = loadMessages;

