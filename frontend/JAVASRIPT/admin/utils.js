/* ==========================================================================
   MahtoMech Admin Panel — Utilities
   Toast notifications, Modal helpers, Formatters, Pagination builder
   ========================================================================== */

// ── Toast Notifications ──────────────────────────────────────────────────────
const TOAST_ICONS = {
    success: '✅',
    error:   '❌',
    warning: '⚠️',
    info:    'ℹ️'
};

function showToast(type, title, message = '', duration = 4000) {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast-item toast-${type}`;
    toast.innerHTML = `
        <span class="toast-icon">${TOAST_ICONS[type] || 'ℹ️'}</span>
        <div class="toast-content">
            <div class="toast-title">${escHtml(title)}</div>
            ${message ? `<div class="toast-message">${escHtml(message)}</div>` : ''}
        </div>
        <span class="toast-close" onclick="this.parentElement.remove()">×</span>
    `;
    container.appendChild(toast);

    setTimeout(() => toast.remove(), duration);
}

const toast = {
    success: (title, msg) => showToast('success', title, msg),
    error:   (title, msg) => showToast('error',   title, msg),
    warning: (title, msg) => showToast('warning', title, msg),
    info:    (title, msg) => showToast('info',    title, msg)
};

// ── Modal Helpers ────────────────────────────────────────────────────────────
function openModal(id) {
    const modal = document.getElementById(id);
    if (modal) modal.classList.add('active');
}

function closeModal(id) {
    const modal = document.getElementById(id);
    if (modal) modal.classList.remove('active');
}

// Close any modal via [data-modal] buttons and backdrop click
document.addEventListener('click', (e) => {
    const closeBtn = e.target.closest('[data-modal]');
    if (closeBtn) {
        closeModal(closeBtn.dataset.modal);
        return;
    }
    // Click on backdrop itself
    if (e.target.classList.contains('modal-backdrop')) {
        e.target.classList.remove('active');
    }
});

// ── Formatters ───────────────────────────────────────────────────────────────
function fmtCurrency(amount) {
    const n = parseFloat(amount) || 0;
    return '₹' + n.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function fmtDate(dateStr) {
    if (!dateStr) return '—';
    return new Date(dateStr).toLocaleDateString('en-IN', {
        day: '2-digit', month: 'short', year: 'numeric'
    });
}

function fmtDateTime(dateStr) {
    if (!dateStr) return '—';
    return new Date(dateStr).toLocaleString('en-IN', {
        day: '2-digit', month: 'short', year: 'numeric',
        hour: '2-digit', minute: '2-digit'
    });
}

function escHtml(str) {
    if (str == null) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

// ── Status Badge ─────────────────────────────────────────────────────────────
const STATUS_CLASS = {
    // order statuses
    pending:    'badge-warning',
    confirmed:  'badge-info',
    processing: 'badge-purple',
    shipped:    'badge-info',
    delivered:  'badge-success',
    cancelled:  'badge-danger',
    // payment
    paid:       'badge-success',
    failed:     'badge-danger',
    refunded:   'badge-neutral',
    // bookings
    in_progress:'badge-purple',
    completed:  'badge-success',
    // stock
    in_stock:   'badge-success',
    low_stock:  'badge-warning',
    out_of_stock:'badge-danger',
    // users/products
    active:     'badge-success',
    inactive:   'badge-danger',
    // messages
    new:        'badge-warning',
    read:       'badge-neutral',
    resolved:   'badge-success'
};

function statusBadge(status) {
    const cls  = STATUS_CLASS[status] || 'badge-neutral';
    const label = (status || 'unknown').replace(/_/g, ' ');
    return `<span class="badge ${cls}">${escHtml(label)}</span>`;
}

// ── Table loading / empty / error states ─────────────────────────────────────
function tableLoading(tbodyId, cols, message = 'Loading...') {
    const el = document.getElementById(tbodyId);
    if (el) el.innerHTML = `<tr><td colspan="${cols}" class="table-empty">${message}</td></tr>`;
}

function tableEmpty(tbodyId, cols, icon = '📋', message = 'No records found.') {
    const el = document.getElementById(tbodyId);
    if (el) el.innerHTML = `<tr><td colspan="${cols}" class="table-empty"><span class="empty-icon">${icon}</span>${escHtml(message)}</td></tr>`;
}

function tableError(tbodyId, cols, message = 'Failed to load data.') {
    const el = document.getElementById(tbodyId);
    if (el) el.innerHTML = `<tr><td colspan="${cols}" class="table-empty" style="color:var(--status-danger)">⚠️ ${escHtml(message)}</td></tr>`;
}

// ── Pagination Builder ────────────────────────────────────────────────────────
function buildPagination(containerId, infoId, currentPage, totalPages, totalCount, onPageChange) {
    const info = document.getElementById(infoId);
    if (info) info.textContent = `${totalCount} result${totalCount !== 1 ? 's' : ''}`;

    const container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = '';

    if (totalPages <= 1) return;

    const makeBtn = (label, page, disabled = false, active = false) => {
        const btn = document.createElement('button');
        btn.className = 'page-btn' + (active ? ' active' : '');
        btn.textContent = label;
        btn.disabled = disabled;
        if (!disabled && !active) {
            btn.addEventListener('click', () => onPageChange(page));
        }
        return btn;
    };

    container.appendChild(makeBtn('‹', currentPage - 1, currentPage === 1));

    const range = pageRange(currentPage, totalPages);
    range.forEach(p => {
        if (p === '...') {
            const span = document.createElement('span');
            span.textContent = '…';
            span.style.padding = '0 4px';
            span.style.color = 'var(--text-muted)';
            container.appendChild(span);
        } else {
            container.appendChild(makeBtn(p, p, false, p === currentPage));
        }
    });

    container.appendChild(makeBtn('›', currentPage + 1, currentPage === totalPages));
}

function pageRange(current, total) {
    if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1);
    const pages = [];
    pages.push(1);
    if (current > 3) pages.push('...');
    for (let i = Math.max(2, current - 1); i <= Math.min(total - 1, current + 1); i++) pages.push(i);
    if (current < total - 2) pages.push('...');
    pages.push(total);
    return pages;
}

// ── Confirm dialog helper ─────────────────────────────────────────────────────
let _confirmCallback = null;
function confirmAction(title, text, callback) {
    document.getElementById('confirmTitle').textContent = title;
    document.getElementById('confirmText').textContent  = text;
    _confirmCallback = callback;
    openModal('confirmModal');
}
document.addEventListener('click', (e) => {
    if (e.target.id === 'confirmActionBtn' && _confirmCallback) {
        _confirmCallback();
        _confirmCallback = null;
        closeModal('confirmModal');
    }
});

// ── Debounce ─────────────────────────────────────────────────────────────────
function debounce(fn, delay = 400) {
    let timer;
    return (...args) => {
        clearTimeout(timer);
        timer = setTimeout(() => fn(...args), delay);
    };
}

// ── Initials avatar ──────────────────────────────────────────────────────────
function initials(name) {
    if (!name) return '?';
    return name.trim().split(/\s+/).map(w => w[0]).slice(0, 2).join('').toUpperCase();
}

