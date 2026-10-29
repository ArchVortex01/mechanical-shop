/* ==========================================================================
   MahtoMech Admin Panel — Bookings Module
   GET /api/bookings/admin/all  |  PUT /api/bookings/:id/status
   ========================================================================== */

let bookingsPage = 1;
let bookingsSearch = '';
let bookingsStatusFilter = '';

async function loadBookings() {
    tableLoading('bookingsBody', 7);

    const res = await API.bookings.list({
        search: bookingsSearch,
        status: bookingsStatusFilter,
        page:   bookingsPage,
        limit:  15
    });

    if (!res || !res.ok) {
        tableError('bookingsBody', 7, res?.data?.message || 'Failed to load bookings.');
        return;
    }

    const d = res.data.data || res.data || {};
    const bookings   = d.bookings || d.items || d || [];
    const total      = d.total    || d.count || bookings.length;
    const totalPages = d.total_pages || Math.ceil(total / 15) || 1;

    if (!bookings.length) {
        tableEmpty('bookingsBody', 7, '📅', 'No bookings found.');
        buildPagination('bookingsPagination', 'bookingsPaginInfo', 1, 1, 0, () => {});
        return;
    }

    document.getElementById('bookingsBody').innerHTML = bookings.map(b => `
        <tr>
            <td class="table-cell-code">${escHtml(b.booking_ref || b.booking_reference || b.id)}</td>
            <td>
                <div class="table-cell-bold">${escHtml(b.customer_name || b.full_name || '—')}</div>
                <div style="font-size:0.75rem;color:var(--text-muted)">${escHtml(b.customer_phone || b.phone || '')}</div>
            </td>
            <td>${escHtml(b.service_name || b.service || '—')}</td>
            <td>
                <div>${fmtDate(b.booking_date || b.scheduled_date)}</div>
                <div style="font-size:0.75rem;color:var(--text-muted)">${escHtml(b.booking_time || b.scheduled_time || '')}</div>
            </td>
            <td>${statusBadge(b.status || b.booking_status)}</td>
            <td>${b.estimated_cost ? fmtCurrency(b.estimated_cost) : '—'}</td>
            <td>
                <button class="btn btn-outline btn-sm" onclick="openBookingModal(${b.id}, '${escHtml(b.booking_ref || b.id)}', '${b.status || b.booking_status}', ${b.estimated_cost || 0})">
                    ✏️ Update
                </button>
            </td>
        </tr>
    `).join('');

    buildPagination('bookingsPagination', 'bookingsPaginInfo', bookingsPage, totalPages, total, (pg) => {
        bookingsPage = pg;
        loadBookings();
    });
}

// ── Booking Update Modal ──────────────────────────────────────────────────────
function openBookingModal(id, ref, status, cost) {
    document.getElementById('bookingId').value              = id;
    document.getElementById('bookingModalRef').textContent  = ref;
    document.getElementById('bookingStatusUpdate').value    = status || 'pending';
    document.getElementById('bookingCost').value            = cost || '';
    document.getElementById('bookingNotes').value           = '';
    openModal('bookingModal');
}

document.getElementById('saveBookingBtn')?.addEventListener('click', async () => {
    const id = document.getElementById('bookingId').value;
    const cost = document.getElementById('bookingCost').value;

    const body = {
        status:         document.getElementById('bookingStatusUpdate').value,
        estimated_cost: cost ? parseFloat(cost) : null,
        admin_notes:    document.getElementById('bookingNotes').value.trim()
    };

    const btn = document.getElementById('saveBookingBtn');
    btn.disabled = true; btn.textContent = 'Updating…';

    const res = await API.bookings.updateStatus(id, body);

    btn.disabled = false; btn.textContent = 'Update Booking';

    if (!res || !res.ok) {
        toast.error('Update Failed', res?.data?.message || 'Could not update booking.');
        return;
    }
    toast.success('Booking Updated', 'Booking status has been updated.');
    closeModal('bookingModal');
    loadBookings();
});

// ── Search & Filter ───────────────────────────────────────────────────────────
document.getElementById('bookingSearch')?.addEventListener('input', debounce((e) => {
    bookingsSearch = e.target.value.trim();
    bookingsPage   = 1;
    loadBookings();
}));

document.getElementById('bookingStatusFilter')?.addEventListener('change', (e) => {
    bookingsStatusFilter = e.target.value;
    bookingsPage         = 1;
    loadBookings();
});

// ── Register ──────────────────────────────────────────────────────────────────
SECTION_LOADERS['bookings'] = loadBookings;

