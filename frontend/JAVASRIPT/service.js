// MahtoMech - Service Page Script

document.addEventListener('DOMContentLoaded', () => {
    const serviceCards = document.querySelectorAll('.service-card-icon');

    serviceCards.forEach(card => {
        card.style.cursor = 'pointer';

        card.addEventListener('click', () => {
            const titleEl = card.querySelector('h3');
            const title = titleEl ? titleEl.textContent.trim() : '';

            if (title) {
                try {
                    localStorage.setItem('mm_selected_service', title);
                } catch (e) {}
                window.location.href = 'booking.html';
            }
        });
    });
});

