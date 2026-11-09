// MahtoMech - Shopping Cart Script

document.addEventListener('DOMContentLoaded', () => {
    const cartCard = document.querySelector('.cart-card');
    const subtotalEl = document.querySelector('.summary-type:nth-of-type(1) span:last-child');
    const shippingEl = document.querySelector('.summary-type:nth-of-type(2) span:last-child');
    const taxEl = document.querySelector('.summary-type:nth-of-type(3) span:last-child');
    const totalEl = document.querySelector('.summary-total span:last-child');

    function parsePrice(str) {
        return parseInt(str.replace(/[^\d]/g, ''), 10) || 0;
    }

    function formatPrice(num) {
        return '₹' + num.toLocaleString('en-IN');
    }

    function recalculateCart() {
        const items = document.querySelectorAll('.cart-card-item');
        let subtotal = 0;
        let totalCount = 0;

        if (items.length === 0) {
            if (cartCard) {
                cartCard.innerHTML = `
                    <div style="text-align: center; padding: 50px 20px; background: #111217; border: 1px solid #1f2330; border-radius: 18px;">
                        <span style="font-size: 3rem; display: block; margin-bottom: 15px;">🛒</span>
                        <h3 style="color: #fff; margin-bottom: 10px;">Your Cart is Empty</h3>
                        <p style="color: #94a3b8; margin-bottom: 20px;">Browse our catalog and add the vehicle parts you need.</p>
                        <a href="buy-parts.html" class="continue-button" style="display: inline-flex; width: auto; padding: 12px 24px; background: #ff6600; border-color: #ff6600; color: white;">SHOP PARTS NOW</a>
                    </div>
                `;
            }
        }

        items.forEach(item => {
            const unitPrice = parsePrice(item.querySelector('.item-price')?.textContent || '0');
            const qtyInput = item.querySelector('.quantity-input');
            const qty = parseInt(qtyInput?.value, 10) || 1;
            const itemTotalEl = item.querySelector('.item-total');

            const itemTotal = unitPrice * qty;
            if (itemTotalEl) {
                itemTotalEl.textContent = formatPrice(itemTotal);
            }

            subtotal += itemTotal;
            totalCount += qty;
        });

        // 18% GST calculation
        const tax = Math.round(subtotal * 0.18);
        const shipping = (subtotal > 2000 || subtotal === 0) ? 0 : 150;
        const grandTotal = subtotal + tax + shipping;

        if (subtotalEl) subtotalEl.textContent = formatPrice(subtotal);
        if (shippingEl) shippingEl.textContent = shipping === 0 ? 'FREE' : formatPrice(shipping);
        if (taxEl) taxEl.textContent = formatPrice(tax);
        if (totalEl) totalEl.textContent = formatPrice(grandTotal);

        // Store active total in localStorage for checkout page
        try {
            localStorage.setItem('mm_cart_total', grandTotal);
            localStorage.setItem('mm_cart_subtotal', subtotal);
            localStorage.setItem('mm_cart_tax', tax);
        } catch (e) {}

        // Update badge count
        const badges = document.querySelectorAll('#Cardcount');
        badges.forEach(b => b.textContent = totalCount);
    }

    // Attach listeners to cart items
    function initCartItemControls() {
        const items = document.querySelectorAll('.cart-card-item');

        items.forEach(item => {
            const minusBtn = item.querySelector('.quantity-button:first-of-type');
            const plusBtn = item.querySelector('.quantity-button:last-of-type');
            const qtyInput = item.querySelector('.quantity-input');
            const removeBtn = item.querySelector('.remove-button');

            if (minusBtn && qtyInput) {
                minusBtn.addEventListener('click', () => {
                    let currentVal = parseInt(qtyInput.value, 10) || 1;
                    if (currentVal > 1) {
                        qtyInput.value = currentVal - 1;
                        recalculateCart();
                    }
                });
            }

            if (plusBtn && qtyInput) {
                plusBtn.addEventListener('click', () => {
                    let currentVal = parseInt(qtyInput.value, 10) || 1;
                    qtyInput.value = currentVal + 1;
                    recalculateCart();
                });
            }

            if (qtyInput) {
                qtyInput.addEventListener('change', () => {
                    let currentVal = parseInt(qtyInput.value, 10);
                    if (isNaN(currentVal) || currentVal < 1) {
                        qtyInput.value = 1;
                    }
                    recalculateCart();
                });
            }

            if (removeBtn) {
                removeBtn.addEventListener('click', () => {
                    item.style.transition = 'all 0.3s ease';
                    item.style.opacity = '0';
                    item.style.transform = 'scale(0.95)';
                    setTimeout(() => {
                        item.remove();
                        recalculateCart();
                    }, 300);
                });
            }
        });
    }

    initCartItemControls();
    recalculateCart();
});

