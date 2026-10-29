// MahtoMech - Booking Page Script

document.addEventListener('DOMContentLoaded', () => {
    const bookingForm = document.getElementById('booking-form');
    const dateInput = document.getElementById('serviceDate');
    const timeSlots = document.querySelectorAll('.time-slots button');
    const pickupOpts = document.querySelectorAll('.pickup-opt');
    const pickupVal = document.getElementById('pickupVal');
    const modal = document.getElementById('successModal');
    const bookingRef = document.getElementById('bookingRef');
    const submitBtn = bookingForm ? bookingForm.querySelector('button[type="submit"]') : null;

    // 1. Set minimum date to today and pre-fill service if navigated from services page
    if (dateInput) {
        const today = new Date().toISOString().split('T')[0];
        dateInput.min = today;
    }

    try {
        const preService = localStorage.getItem('mm_selected_service');
        const serviceSelect = document.getElementById('serviceType');
        if (preService && serviceSelect) {
            for (let opt of serviceSelect.options) {
                if (opt.text.toLowerCase().includes(preService.toLowerCase()) || preService.toLowerCase().includes(opt.text.toLowerCase())) {
                    opt.selected = true;
                    break;
                }
            }
            localStorage.removeItem('mm_selected_service');
        }
    } catch (e) {}

    // 2. Time Slot Selection
    let selectedTime = '';
    timeSlots.forEach(btn => {
        btn.addEventListener('click', () => {
            timeSlots.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            selectedTime = btn.textContent.trim();

            const errTime = document.getElementById('err-time');
            if (errTime) errTime.style.display = 'none';

            // Advance step indicator to Step 3
            updateStep(3);
        });
    });

    // 3. Pickup Option Toggle
    pickupOpts.forEach(opt => {
        opt.addEventListener('click', () => {
            pickupOpts.forEach(o => o.classList.remove('selected'));
            opt.classList.add('selected');
            if (pickupVal) {
                pickupVal.value = opt.getAttribute('data-pickup');
            }
        });
    });

    // 4. Step Indicator Tracker
    function updateStep(stepNum) {
        const steps = [document.getElementById('step1'), document.getElementById('step2'), document.getElementById('step3')];
        steps.forEach((st, idx) => {
            if (st) {
                if (idx + 1 <= stepNum) {
                    st.classList.add('active');
                } else {
                    st.classList.remove('active');
                }
            }
        });
    }

    // Input listeners to advance steps naturally
    const vehicleType = document.getElementById('VehicleType');
    if (vehicleType) {
        vehicleType.addEventListener('change', () => updateStep(2));
    }
    if (dateInput) {
        dateInput.addEventListener('change', () => updateStep(3));
    }

    // 5. Form Validation and Real API Submission
    if (bookingForm) {
        bookingForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            // Validate time slot
            if (!selectedTime) {
                const errTime = document.getElementById('err-time');
                if (errTime) errTime.style.display = 'block';
                const timeSlotContainer = document.querySelector('.time-slots');
                if (timeSlotContainer) timeSlotContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
                return;
            }

            const custName = document.getElementById('custName')?.value.trim() || '';
            const custPhone = document.getElementById('custPhone')?.value.trim() || '';
            const custEmail = document.getElementById('custEmail')?.value.trim() || '';
            const vehicleTypeVal = document.getElementById('VehicleType')?.value || '';
            const vehicleModelVal = document.getElementById('vehicleModel')?.value.trim() || '';
            const vehicleRegVal = document.getElementById('vehicleReg')?.value.trim() || '';
            const serviceTypeVal = document.getElementById('serviceType')?.value || '';
            const problemDescVal = document.getElementById('problemDesc')?.value.trim() || '';

            const bookingData = {
                cust_name: custName,
                cust_phone: custPhone,
                cust_email: custEmail,
                vehicle_type: vehicleTypeVal,
                vehicle_model: vehicleModelVal,
                vehicle_reg: vehicleRegVal,
                service_type: serviceTypeVal,
                problem_description: problemDescVal,
                booking_date: dateInput?.value,
                booking_time: selectedTime,
                pickup_option: pickupVal?.value || 'self'
            };

            const originalBtnText = submitBtn ? submitBtn.textContent : 'BOOK APPOINTMENT NOW';
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = 'SUBMITTING BOOKING...';
            }

            try {
                const res = await window.MahtoMechAPI.bookings.create(bookingData);
                const confirmedRef = res.data?.booking_ref || res.data?.id || ('MP-' + Math.floor(100000 + Math.random() * 900000));

                if (bookingRef) {
                    bookingRef.textContent = '#' + confirmedRef;
                }

                const modalText = document.getElementById('modalText');
                if (modalText && custName) {
                    modalText.innerHTML = `Thank you <strong>${custName}</strong>! Your service appointment has been booked for <strong>${dateInput?.value || 'selected date'}</strong> at <strong>${selectedTime}</strong>.<br>Our team will confirm within 30 minutes via WhatsApp & SMS.`;
                }

                // Show Confirmation Modal
                if (modal) {
                    modal.classList.add('show');
                }

                // Reset form fields
                bookingForm.reset();
                timeSlots.forEach(b => b.classList.remove('active'));
                selectedTime = '';
                updateStep(1);
            } catch (err) {
                console.error('Booking submission error:', err);
                const message = err.message || (err.data && (err.data.message || err.data.error)) || 'Failed to submit booking. Please try again.';
                alert(`Booking Error: ${message}`);
            } finally {
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.textContent = originalBtnText;
                }
            }
        });
    }
});
