// MahtoMech - Checkout Script

document.addEventListener('DOMContentLoaded', () => {
    const subtotalEl = document.getElementById('subtotal');
    const shippingEl = document.getElementById('shipping');
    const taxEl = document.getElementById('tax');
    const discountRow = document.getElementById('discountRow');
    const discountEl = document.getElementById('discount');
    const totalAmountEl = document.getElementById('totalAmount');
    const checkoutForm = document.getElementById('checkoutForm');
    const paymentMethods = document.querySelectorAll('.payment-method-selected');
    const submitBtn = checkoutForm ? checkoutForm.querySelector('.checkout-button') : null;

    // 1. Load cart values from localStorage or default
    let subtotal = 5346;
    let tax = 963;
    let discount = 0;

    try {
        const storedSubtotal = localStorage.getItem('mm_cart_subtotal');
        const storedTax = localStorage.getItem('mm_cart_tax');
        if (storedSubtotal) subtotal = parseInt(storedSubtotal, 10);
        if (storedTax) tax = parseInt(storedTax, 10);
    } catch (e) {}

    function formatPrice(num) {
        return '₹' + num.toLocaleString('en-IN');
    }

    function updateTotal() {
        const shipping = subtotal > 2000 ? 0 : (subtotal === 0 ? 0 : 150);
        const grandTotal = Math.max(0, subtotal + tax + shipping - discount);

        if (subtotalEl) subtotalEl.textContent = formatPrice(subtotal);
        if (shippingEl) shippingEl.textContent = shipping === 0 ? 'FREE' : formatPrice(shipping);
        if (taxEl) taxEl.textContent = formatPrice(tax);
        if (totalAmountEl) totalAmountEl.textContent = formatPrice(grandTotal);

        if (discount > 0 && discountRow && discountEl) {
            discountRow.style.display = 'flex';
            discountEl.textContent = '-' + formatPrice(discount);
        } else if (discountRow) {
            discountRow.style.display = 'none';
        }
    }

    updateTotal();

    // 2. Payment Method Selection
    let selectedPaymentMethod = 'card';
    paymentMethods.forEach((method, index) => {
        if (index === 0) method.classList.add('active'); // Default to Card

        method.addEventListener('click', () => {
            paymentMethods.forEach(m => m.classList.remove('active'));
            method.classList.add('active');
            selectedPaymentMethod = method.getAttribute('data-method') || method.querySelector('.payment-name')?.textContent.trim() || 'card';
        });
    });

    // 3. Promo Code Application
    window.applyPromo = function() {
        const promoInput = document.getElementById('promoCode');
        if (!promoInput) return;

        const code = promoInput.value.trim().toUpperCase();
        if (code === 'SAVE10' || code === 'MAHTO10') {
            discount = 500;
            updateTotal();
            alert(`🎉 Success! Promo code "${code}" applied. ₹500 discount added to your total.`);
        } else if (code) {
            alert('Invalid promo code. Try using "SAVE10" or "MAHTO10".');
        } else {
            alert('Please enter a promo code.');
        }
    };

    // 4. Real Backend Order Checkout
    if (checkoutForm) {
        checkoutForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const termsAgree = document.getElementById('termsAgree');
            if (termsAgree && !termsAgree.checked) {
                alert('Please accept the Terms & Conditions to complete your order.');
                return;
            }

            const fullName = document.getElementById('fullName')?.value.trim() || 'Customer';
            const email = document.getElementById('email')?.value.trim() || '';
            const phone = document.getElementById('phone')?.value.trim() || '';
            const country = document.getElementById('country')?.value || 'India';
            const address = document.getElementById('address')?.value.trim() || '';
            const city = document.getElementById('city')?.value.trim() || '';
            const state = document.getElementById('state')?.value.trim() || '';
            const pinCode = document.getElementById('pinCode')?.value.trim() || '';
            const landmark = document.getElementById('landmark')?.value.trim() || '';

            // Retrieve items from local storage cart
            let cartItems = [];
            try {
                if (window.MM_Cart && typeof window.MM_Cart.get === 'function') {
                    cartItems = window.MM_Cart.get() || [];
                } else {
                    const raw = localStorage.getItem('mm_cart_items');
                    if (raw) cartItems = JSON.parse(raw);
                }
            } catch (err) {}

            const checkoutPayload = {
                fullName,
                email,
                phone,
                country,
                address,
                city,
                state,
                pinCode,
                landmark,
                payment_method: selectedPaymentMethod,
                items: cartItems
            };

            const originalBtnHtml = submitBtn ? submitBtn.innerHTML : 'PROCEED TO PAYMENT';
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> PLACING ORDER...';
            }

            try {
                const res = await window.MahtoMechAPI.orders.checkout(checkoutPayload);
                const orderData = res.data || {};
                const orderNumber = orderData.order_number || ('ORD-' + orderData.order_id);

                // Clear cart locally
                try {
                    if (window.MM_Cart && typeof window.MM_Cart.set === 'function') {
                        window.MM_Cart.set([]);
                    }
                    localStorage.removeItem('mm_cart_items');
                    localStorage.removeItem('mm_cart_total');
                    localStorage.removeItem('mm_cart_subtotal');
                    localStorage.removeItem('mm_cart_tax');
                } catch (e) {}

                alert(`✅ ORDER PLACED SUCCESSFULLY!\n\nOrder Number: ${orderNumber}\nThank you, ${fullName}!\n\nA confirmation receipt has been sent to your email and phone number.`);
                window.location.href = 'index.html';
            } catch (err) {
                console.error('Checkout error:', err);
                const message = err.message || (err.data && (err.data.message || err.data.error)) || 'Failed to place order. Please try again.';
                alert(`Order Error: ${message}`);
            } finally {
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalBtnHtml;
                }
            }
        });
    }
});
