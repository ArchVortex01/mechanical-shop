/* ==========================================================================
   MahtoMech Admin Panel — Users Module
   GET /api/admin/users  |  PUT /api/admin/users/:id/status
   ========================================================================== */

let usersPage = 1;
let usersSearch = '';
let usersStatusFilter = '';

async function loadUsers() {
    tableLoading('usersBody', 6);

    const res = await API.users.list({
        search: usersSearch,
        status: usersStatusFilter,
        page:   usersPage,
        limit:  15
    });

    if (!res || !res.ok) {
        tableError('usersBody', 6, res?.data?.message || 'Failed to load users.');
        return;
    }

    const d = res.data.data || res.data || {};
    const users      = d.users  || d.items || d || [];
    const total      = d.total  || d.count || users.length;
    const totalPages = d.total_pages || Math.ceil(total / 15) || 1;

    if (!users.length) {
        tableEmpty('usersBody', 6, '👤', 'No users found.');
        buildPagination('usersPagination', 'usersPaginInfo', 1, 1, 0, () => {});
        return;
    }

    document.getElementById('usersBody').innerHTML = users.map(u => {
        const isActive = u.is_active !== false && u.status !== 'inactive';
        return `
        <tr>
            <td>
                <div style="display:flex;align-items:center;gap:10px">
                    <div style="width:34px;height:34px;border-radius:50%;background:var(--primary-light);border:1px solid var(--primary);display:flex;align-items:center;justify-content:center;font-weight:700;color:var(--primary);font-size:0.85rem;flex-shrink:0">
                        ${initials(u.full_name || u.name)}
                    </div>
                    <div>
                        <div class="table-cell-bold">${escHtml(u.full_name || u.name || '—')}</div>
                    </div>
                </div>
            </td>
            <td style="color:var(--text-muted)">${escHtml(u.email || '—')}</td>
            <td style="color:var(--text-muted)">${escHtml(u.phone || '—')}</td>
            <td>${statusBadge(isActive ? 'active' : 'inactive')}</td>
            <td>${fmtDate(u.created_at)}</td>
            <td>
                <button class="btn btn-sm ${isActive ? 'btn-danger' : 'btn-outline'}"
                    onclick="toggleUserStatus(${u.id}, '${escHtml(u.full_name || u.name)}', ${isActive})">
                    ${isActive ? '🚫 Deactivate' : '✅ Activate'}
                </button>
            </td>
        </tr>
    `;
    }).join('');

    buildPagination('usersPagination', 'usersPaginInfo', usersPage, totalPages, total, (pg) => {
        usersPage = pg;
        loadUsers();
    });
}

// ── Toggle User Status ────────────────────────────────────────────────────────
function toggleUserStatus(id, name, currentlyActive) {
    const action = currentlyActive ? 'Deactivate' : 'Activate';
    confirmAction(`${action} User`, `Are you sure you want to ${action.toLowerCase()} "${name}"?`, async () => {
        const res = await API.users.setStatus(id, !currentlyActive);
        if (!res || !res.ok) {
            toast.error('Update Failed', res?.data?.message || 'Could not update user status.');
            return;
        }
        toast.success('Updated', `User "${name}" has been ${currentlyActive ? 'deactivated' : 'activated'}.`);
        loadUsers();
    });
}

// ── Search & Filter ───────────────────────────────────────────────────────────
document.getElementById('userSearch')?.addEventListener('input', debounce((e) => {
    usersSearch = e.target.value.trim();
    usersPage   = 1;
    loadUsers();
}));

document.getElementById('userStatusFilter')?.addEventListener('change', (e) => {
    usersStatusFilter = e.target.value;
    usersPage         = 1;
    loadUsers();
});

// ── Register ──────────────────────────────────────────────────────────────────
SECTION_LOADERS['users'] = loadUsers;

