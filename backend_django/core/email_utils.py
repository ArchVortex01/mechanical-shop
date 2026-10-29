import logging
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)

def send_email(to_email, subject, text_content, html_content=None):
    if not getattr(settings, 'EMAIL_HOST_USER', None) or settings.EMAIL_HOST_USER == 'your_email@gmail.com':
        print(f"📨 [MOCK EMAIL DISPATCHED]")
        print(f"   To: {to_email}")
        print(f"   Subject: {subject}")
        print(f"   Preview: {text_content[:100]}...")
        return True
        
    try:
        send_mail(
            subject=subject,
            message=text_content,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', '"MahtoMech" <no-reply@mahtomech.in>'),
            recipient_list=[to_email],
            html_message=html_content,
            fail_silently=False,
        )
        print(f"📧 Email sent to {to_email}")
        return True
    except Exception as e:
        print(f"❌ Failed to send email to {to_email}: {str(e)}")
        return False

def send_booking_confirmation_email(to_email, booking):
    subject = f"Booking Confirmation - {booking.booking_ref}"
    text = f"""Hello {booking.user.name},

Your service booking for {booking.service.name} has been successfully received.
Booking Reference: {booking.booking_ref}
Date: {booking.booking_date}
Time: {booking.booking_time}

Our team will review the details and confirm the appointment shortly.

Thank you,
MahtoMech Team
"""
    html = f"""
    <h2>Booking Confirmation</h2>
    <p>Hello {booking.user.name},</p>
    <p>Your service booking for <strong>{booking.service.name}</strong> has been successfully received.</p>
    <ul>
        <li><strong>Reference:</strong> {booking.booking_ref}</li>
        <li><strong>Date:</strong> {booking.booking_date}</li>
        <li><strong>Time:</strong> {booking.booking_time}</li>
    </ul>
    <p>Our team will review the details and confirm the appointment shortly.</p>
    <br/>
    <p>Thank you,<br/>MahtoMech Team</p>
    """
    
    return send_email(to_email, subject, text, html)
