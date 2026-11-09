// MahtoMech - Buy Parts Page Script

document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('parts-Search');
    const sortSelect = document.getElementById('sortBy');
    const priceSelect = document.querySelector('.buy-parts-price');
    const partsCount = document.querySelector('.parts-count strong');
    const allCards = Array.from(document.querySelectorAll('.car-card, .bike-card, .truck-card, .tractor-card, .bus-card'));

    // 1. Initial count calculation
    function updateCount() {
        const visibleCards = allCards.filter(card => card.style.display !== 'none');
        if (partsCount) {
            partsCount.textContent = visibleCards.length;
        }
    }

    // 2. Filter & Search Function
    function filterProducts() {
        const query = searchInput ? searchInput.value.toLowerCase().trim() : '';
        const priceRange = priceSelect ? priceSelect.value : '';

        allCards.forEach(card => {
            const title = card.querySelector('h3') ? card.querySelector('h3').textContent.toLowerCase() : '';
            const desc = card.querySelector('p') ? card.querySelector('p').textContent.toLowerCase() : '';
            const priceText = card.querySelector('h4') ? card.querySelector('h4').textContent : '';
            const rawPrice = parseInt(priceText.replace(/[^\d]/g, ''), 10) || 0;

            const matchesQuery = !query || title.includes(query) || desc.includes(query);

            let matchesPrice = true;
            if (priceRange === '0-500') matchesPrice = rawPrice <= 500;
            else if (priceRange === '500-2000') matchesPrice = rawPrice > 500 && rawPrice <= 2000;
            else if (priceRange === '2000-5000') matchesPrice = rawPrice > 2000 && rawPrice <= 5000;
            else if (priceRange === '5000+') matchesPrice = rawPrice > 5000;

            if (matchesQuery && matchesPrice) {
                card.style.display = '';
            } else {
                card.style.display = 'none';
            }
        });

        updateCount();
    }

    // 3. Sorting Function
    function sortProducts() {
        const sortVal = sortSelect ? sortSelect.value : 'trending';
        const sections = document.querySelectorAll('.buy-car-parts, .buy-bike-parts, .buy-truck-parts, .buy-tractor-parts, .buy-bus-parts');

        sections.forEach(sec => {
            const cards = Array.from(sec.children);
            cards.sort((a, b) => {
                const priceA = parseInt((a.querySelector('h4')?.textContent || '0').replace(/[^\d]/g, ''), 10) || 0;
                const priceB = parseInt((b.querySelector('h4')?.textContent || '0').replace(/[^\d]/g, ''), 10) || 0;

                if (sortVal === 'price-asc') return priceA - priceB;
                if (sortVal === 'price-desc') return priceB - priceA;
                return 0;
            });
            cards.forEach(card => sec.appendChild(card));
        });
    }

    // Event listeners for search, filter, and sort
    if (searchInput) searchInput.addEventListener('input', filterProducts);
    if (priceSelect) priceSelect.addEventListener('change', filterProducts);
    if (sortSelect) sortSelect.addEventListener('change', sortProducts);

    // Read query parameter from URL (e.g. ?q=oil)
    const urlParams = new URLSearchParams(window.location.search);
    const searchParam = urlParams.get('q');
    if (searchParam && searchInput) {
        searchInput.value = searchParam;
        filterProducts();
    } else {
        updateCount();
    }

    // 4. Category Tags Filter (e.g., Engine, Brake System, etc.)
    const tagContainers = document.querySelectorAll('.car-item, .bike-item, .truck-item, .tractor-item, .bus-item');
    tagContainers.forEach(container => {
        const buttons = container.querySelectorAll('button');
        buttons.forEach(btn => {
            btn.addEventListener('click', () => {
                buttons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');

                const filterTag = btn.textContent.trim().toLowerCase();
                const parentSection = container.closest('.vehicle-section');
                if (parentSection) {
                    const cards = parentSection.querySelectorAll('.car-card, .bike-card, .truck-card, .tractor-card, .bus-card');
                    cards.forEach(card => {
                        const title = card.querySelector('h3')?.textContent.toLowerCase() || '';
                        const desc = card.querySelector('p')?.textContent.toLowerCase() || '';
                        if (filterTag === 'all' || title.includes(filterTag) || desc.includes(filterTag)) {
                            card.style.display = '';
                        } else {
                            card.style.display = 'none';
                        }
                    });
                    updateCount();
                }
            });
        });
    });

    // 5. Add to Cart & Buy Buttons
    allCards.forEach(card => {
        const buttons = card.querySelectorAll('.card-body button');
        const cartBtn = buttons[0];
        const buyBtn = buttons[1];

        const title = card.querySelector('h3')?.textContent.trim() || 'Vehicle Part';
        const priceText = card.querySelector('h4')?.textContent.split(' ')[0].trim() || '₹0';
        const imageSrc = card.querySelector('.card-image img')?.getAttribute('src') || '';

        function addToCart(showFeedback = true) {
            let cart = MM_Cart.get() || [];
            const existing = cart.find(item => item.title === title);
            if (existing) {
                existing.qty = (existing.qty || 1) + 1;
            } else {
                cart.push({
                    title: title,
                    price: priceText,
                    image: imageSrc,
                    qty: 1
                });
            }
            MM_Cart.set(cart);

            if (showFeedback && cartBtn) {
                const originalText = cartBtn.innerHTML;
                cartBtn.innerHTML = '✓ ADDED';
                cartBtn.style.background = '#22c55e';
                cartBtn.style.borderColor = '#22c55e';
                setTimeout(() => {
                    cartBtn.innerHTML = originalText;
                    cartBtn.style.background = '';
                    cartBtn.style.borderColor = '';
                }, 1200);
            }
        }

        if (cartBtn) {
            cartBtn.addEventListener('click', () => addToCart(true));
        }

        if (buyBtn) {
            buyBtn.addEventListener('click', () => {
                addToCart(false);
                window.location.href = 'checkout.html';
            });
        }
    });
});

