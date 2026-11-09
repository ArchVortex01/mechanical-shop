// MahtoMech - Home Page Script

document.addEventListener('DOMContentLoaded', () => {
    const heroSearchInput = document.getElementById('heroSearch');

    // Global Search Function
    window.handleSearch = function() {
        const query = heroSearchInput ? heroSearchInput.value.trim() : '';
        if (query) {
            window.location.href = `buy-parts.html?q=${encodeURIComponent(query)}`;
        } else {
            if (heroSearchInput) {
                heroSearchInput.focus();
                heroSearchInput.placeholder = "Please type something to search...";
                setTimeout(() => {
                    heroSearchInput.placeholder = "Search parts, services, vehicles...";
                }, 2000);
            }
        }
    };

    // Allow Enter key to trigger search
    if (heroSearchInput) {
        heroSearchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                window.handleSearch();
            }
        });
    }
});

