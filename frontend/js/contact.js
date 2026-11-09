// MahtoMech - Contact Page Script

document.addEventListener('DOMContentLoaded', () => {
    const contactForm = document.querySelector('.contact-form form');
    const submitBtn = contactForm ? contactForm.querySelector('.button-send') : null;

    if (contactForm) {
        contactForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const name = document.getElementById('name')?.value.trim();
            const email = document.getElementById('email')?.value.trim();
            const phone = document.getElementById('phone')?.value.trim() || '';
            const subject = document.getElementById('subject')?.value.trim();
            const category = document.getElementById('category')?.value || 'General Inquiry';
            const message = document.getElementById('message')?.value.trim();

            if (!name || !email || !subject || !message) {
                alert('Please fill out all required fields marked with an asterisk (*).');
                return;
            }

            const originalBtnText = submitBtn ? submitBtn.textContent : 'SEND MESSAGE';
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = 'SENDING MESSAGE...';
            }

            try {
                // Submit to backend via central API client
                await window.MahtoMechAPI.contact.submit({
                    name,
                    email,
                    phone,
                    subject,
                    category,
                    message
                });

                // Success feedback
                alert(`📨 Message Sent Successfully!\n\nThank you, ${name}! We have received your inquiry regarding "${subject}". Our support team will get back to you at ${email} shortly.`);
                contactForm.reset();
            } catch (err) {
                console.error('Contact form error:', err);
                const errorMsg = err.message || (err.data && (err.data.message || err.data.error)) || 'Failed to send message. Please try again later.';
                alert(`Error: ${errorMsg}`);
            } finally {
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.textContent = originalBtnText;
                }
            }
        });
    }
});
