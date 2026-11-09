/* ==========================================================================
   MahtoMech Admin Panel — App Shell
   Auth guard, Navigation SPA routing, Sidebar toggle, Global init
   ========================================================================== */

// ── Auth Guard ───────────────────────────────────────────────────────────────
(function authGuard() {
    const token = localStorage.getItem('adminToken') || localStorage.getItem('mm_auth_token');
    let user = {};
    try {
        user = JSON.parse(localStorage.getItem('adminUser') || localStorage.getItem('mm_auth_user') || '{}');
    } catch (_) {}

    if (!token || user.role !== 'ADMIN') {
        window.location.href = 'login.html';
        return;
    }
    // Populate admin info in sidebar
    try {
        const name = user.full_name || user.name || user.email || 'Admin';
        const avatarEl = document.getElementById('adminAvatar');
        const nameEl   = document.getElementById('adminName');
        if (avatarEl) avatarEl.textContent = initials(name);
        if (nameEl)   nameEl.textContent   = name;
    } catch (_) {}
})();

// ── Section Titles ────────────────────────────────────────────────────────────
const SECTION_META = {
    dashboard:  { title: 'Dashboard',           subtitle: 'Welcome back — overview of operations' },
    products:   { title: 'Products',            subtitle: 'Manage your vehicle parts catalog' },
    categories: { title: 'Categories',          subtitle: 'Organize products into categories' },
    inventory:  { title: 'Inventory',           subtitle: 'Stock levels & low-stock alerts' },
    orders:     { title: 'Orders',              subtitle: 'View & manage customer orders' },
    services:   { title: 'Services',            subtitle: 'Workshop service offerings' },
    bookings:   { title: 'Service Bookings',    subtitle: 'Appointment & booking management' },
    vehicles:   { title: 'Customer Vehicles',   subtitle: 'All registered vehicles' },
    payments:   { title: 'Payments',            subtitle: 'Transaction records & payment verification' },
    reports:    { title: 'Reports & Analytics', subtitle: 'Sales, orders, bookings summary' },
    users:      { title: 'Customers',           subtitle: 'Registered users & account management' },
    messages:   { title: 'Contact Messages',    subtitle: 'Customer inquiries & support' }
};

// ── Section loaders map (populated by each module) ────────────────────────────
const SECTION_LOADERS = {};

// ── SPA Navigation ────────────────────────────────────────────────────────────
let currentSection = null;

function navigate(sectionId) {
    if (sectionId === currentSection) return;
    currentSection = sectionId;

    // Update sidebar nav active state
    document.querySelectorAll('.sidebar .nav-link').forEach(a => {
        a.classList.toggle('active', a.dataset.section === sectionId);
    });

    // Show/hide view sections
    document.querySelectorAll('.view-section').forEach(sec => {
        sec.classList.toggle('active', sec.id === `section-${sectionId}`);
    });

    // Update page title
    const meta = SECTION_META[sectionId] || { title: sectionId, subtitle: '' };
    const titleEl    = document.getElementById('pageTitle');
    const subtitleEl = document.getElementById('pageSubtitle');
    if (titleEl)    titleEl.textContent    = meta.title;
    if (subtitleEl) subtitleEl.textContent = meta.subtitle;

    // Load section data
    if (SECTION_LOADERS[sectionId]) {
        SECTION_LOADERS[sectionId]();
    }

    // Close sidebar on mobile
    if (window.innerWidth <= 1024) closeSidebar();
}

// ── Sidebar Toggle (Mobile) ───────────────────────────────────────────────────
function openSidebar() {
    document.getElementById('sidebar').classList.add('open');
    document.getElementById('sidebarBackdrop').classList.add('active');
}

function closeSidebar() {
    document.getElementById('sidebar').classList.remove('open');
    document.getElementById('sidebarBackdrop').classList.remove('active');
}

document.getElementById('sidebarToggleBtn')?.addEventListener('click', () => {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.contains('open') ? closeSidebar() : openSidebar();
});

document.getElementById('sidebarBackdrop')?.addEventListener('click', closeSidebar);

// ── Sidebar nav-link click ────────────────────────────────────────────────────
document.querySelectorAll('.sidebar .nav-link[data-section]').forEach(link => {
    link.addEventListener('click', (e) => {
        e.preventDefault();
        navigate(link.dataset.section);
    });
});

// ── Logout ────────────────────────────────────────────────────────────────────
document.getElementById('logoutBtn')?.addEventListener('click', () => {
    confirmAction('Logout', 'Are you sure you want to log out?', () => {
        localStorage.removeItem('adminToken');
        localStorage.removeItem('adminUser');
        localStorage.removeItem('mm_auth_token');
        localStorage.removeItem('mm_auth_user');
        window.location.href = 'login.html';
    });
});

// ── Refresh button ────────────────────────────────────────────────────────────
document.getElementById('refreshBtn')?.addEventListener('click', () => {
    if (currentSection && SECTION_LOADERS[currentSection]) {
        SECTION_LOADERS[currentSection]();
        toast.info('Refreshed', 'Data has been reloaded.');
    }
});

// ── Global Search (navigate to section) ──────────────────────────────────────
document.getElementById('globalSearch')?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        const val = e.target.value.trim().toLowerCase();
        const sections = Object.keys(SECTION_META);
        const match = sections.find(s => s.includes(val) || SECTION_META[s].title.toLowerCase().includes(val));
        if (match) {
            navigate(match);
            e.target.value = '';
        }
    }
});

// ── Keyboard shortcut (Escape closes sidebar on mobile) ──────────────────────
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeSidebar();
});

// ── Boot: navigate to dashboard ───────────────────────────────────────────────
window.addEventListener('DOMContentLoaded', () => {
    navigate('dashboard');
});

