// MahtoMech - Shared Main Script (Navigation & Global Cart)

// Cart Helper Functions
const MM_Cart = {
    KEY: 'mm_cart_items',
    get() {
        try {
            const data = localStorage.getItem(this.KEY);
            return data ? JSON.parse(data) : null;
        } catch (e) {
            return null;
        }
    },
    set(items) {
        try {
            localStorage.setItem(this.KEY, JSON.stringify(items));
            this.updateBadge();
        } catch (e) {}
    },
    count() {
        const items = this.get();
        if (!items || !Array.isArray(items)) return 4; // Default count from HTML if no local storage
        return items.reduce((sum, item) => sum + (item.qty || 1), 0);
    },
    updateBadge() {
        const badges = document.querySelectorAll('#Cardcount');
        const count = this.count();
        badges.forEach(b => {
            b.textContent = count;
        });
    }
};

document.addEventListener('DOMContentLoaded', () => {
    // 1. Mobile Navigation Toggle
    const navToggle = document.getElementById('navToggle');
    const navLink = document.querySelector('.nav-link');
    const navAction = document.querySelector('.nav-action');
    const header = document.querySelector('header');

    if (navToggle && navLink) {
        navToggle.addEventListener('click', (e) => {
            e.stopPropagation();
            const isOpen = navLink.classList.toggle('nav-open');
            if (navAction) navAction.classList.toggle('nav-open');
            navToggle.classList.toggle('active');
            navToggle.setAttribute('aria-expanded', isOpen);

            const icon = navToggle.querySelector('i');
            if (icon) {
                if (isOpen) {
                    icon.classList.remove('fa-bars');
                    icon.classList.add('fa-times');
                } else {
                    icon.classList.remove('fa-times');
                    icon.classList.add('fa-bars');
                }
            }
        });

        // Close menu when clicking any nav link
        navLink.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                navLink.classList.remove('nav-open');
                if (navAction) navAction.classList.remove('nav-open');
                navToggle.classList.remove('active');
                navToggle.setAttribute('aria-expanded', 'false');
                const icon = navToggle.querySelector('i');
                if (icon) {
                    icon.classList.remove('fa-times');
                    icon.classList.add('fa-bars');
                }
            });
        });

        // Close menu when clicking outside header
        document.addEventListener('click', (e) => {
            if (navLink.classList.contains('nav-open') && header && !header.contains(e.target)) {
                navLink.classList.remove('nav-open');
                if (navAction) navAction.classList.remove('nav-open');
                navToggle.classList.remove('active');
                navToggle.setAttribute('aria-expanded', 'false');
                const icon = navToggle.querySelector('i');
                if (icon) {
                    icon.classList.remove('fa-times');
                    icon.classList.add('fa-bars');
                }
            }
        });
    }

    // 2. Global Navbar Search Box
    const navbarSearch = document.getElementById('Searchbar');
    if (navbarSearch) {
        navbarSearch.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const query = navbarSearch.value.trim();
                if (query) {
                    window.location.href = `buy-parts.html?q=${encodeURIComponent(query)}`;
                }
            }
        });
    }

    // 3. Initialize Cart Badge from Local Storage
    MM_Cart.updateBadge();
});
