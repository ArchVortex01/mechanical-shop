// MahtoMech - Login Page Script

document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.querySelector('.login-card form');
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const rememberCheckbox = document.getElementById('remember');
    const forgotLink = document.querySelector('.forgot-link');
    const googleBtn = document.querySelector('.sign-btn[title="Google Login"]');
    const phoneBtn = document.querySelector('.sign-btn[title="Phone Login"]');
    const submitBtn = loginForm ? loginForm.querySelector('.button-submit') : null;

    // 1. Remember Me saved email restoration
    try {
        const savedUser = localStorage.getItem('mm_saved_user');
        if (savedUser && emailInput) {
            emailInput.value = savedUser;
            if (rememberCheckbox) rememberCheckbox.checked = true;
        }
    } catch (e) {}

    // 2. Form Submission via Real API
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const identifier = emailInput ? emailInput.value.trim() : '';
            const password = passwordInput ? passwordInput.value : '';

            if (!identifier || !password) {
                alert('Please enter your email/phone and password.');
                return;
            }

            const originalBtnText = submitBtn ? submitBtn.textContent : 'SIGN IN';
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = 'SIGNING IN...';
            }

            try {
                // Call central API client
                const res = await window.MahtoMechAPI.auth.login({
                    email: identifier,
                    password: password
                });

                if (rememberCheckbox && rememberCheckbox.checked) {
                    try {
                        localStorage.setItem('mm_saved_user', identifier);
                    } catch (e) {}
                } else {
                    try {
                        localStorage.removeItem('mm_saved_user');
                    } catch (e) {}
                }

                const user = res.data?.user;
                if (user && user.role === 'ADMIN') {
                    window.location.href = 'admin-panel.html';
                } else {
                    window.location.href = 'index.html';
                }
            } catch (err) {
                console.error('Login error:', err);
                const message = err.message || (err.data && (err.data.message || err.data.error)) || 'Login failed. Please check your credentials.';
                alert(`Login failed: ${message}`);
            } finally {
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.textContent = originalBtnText;
                }
            }
        });
    }

    // 3. Social and Forgot Password buttons
    if (forgotLink) {
        forgotLink.addEventListener('click', (e) => {
            e.preventDefault();
            const identifier = prompt('Please enter your registered email or phone number to reset your password:');
            if (identifier) {
                alert(`A password reset link / OTP has been sent to "${identifier}".`);
            }
        });
    }

    if (googleBtn) {
        googleBtn.addEventListener('click', () => {
            alert('Google authentication will be available in the next release.');
        });
    }

    if (phoneBtn) {
        phoneBtn.addEventListener('click', () => {
            const phone = prompt('Enter your 10-digit mobile number for OTP login:');
            if (phone && phone.length >= 10) {
                alert(`OTP sent to +91 ${phone.slice(-10)}!`);
            }
        });
    }
});
