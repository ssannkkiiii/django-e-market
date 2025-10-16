from django.core.mail import send_mail
from django.conf import settings
from django.core.mail import EmailMessage
from django.utils import timezone
import logging
import threading
from typing import Optional

logger = logging.getLogger('apps.users')

def _send_email_async(subject: str, message: str, recipient_list: list, from_email: Optional[str] = None):
    def send():
        try:
            if not from_email:
                from_email = settings.DEFAULT_FROM_EMAIL
            
            if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
                logger.error("Email credentials not configured")
                return False
                
            send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=recipient_list,
                fail_silently=False,
            )
            logger.info(f"Email sent successfully to {recipient_list}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {recipient_list}: {str(e)}")
            return False
    
    thread = threading.Thread(target=send)
    thread.daemon = True
    thread.start()
    return thread

def send_otp_email(email: str, otp: str, async_send: bool = True) -> bool:

    try:
        subject = "Your OTP Code"
        message = f"Your OTP code is: {otp}\n\nThis code will expire in 5 minutes.\n\nIf you didn't request this code, please ignore this email."
        
        if async_send:
            _send_email_async(subject, message, [email])
            logger.info(f"OTP email queued for sending to {email}")
            return True
        else:
            if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
                logger.error("Email credentials not configured")
                return False
                
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            logger.info(f"OTP email sent successfully to {email}")
            return True
            
    except Exception as e:
        logger.error(f"Failed to send OTP email to {email}: {str(e)}")
        return False

def send_welcome_email(email: str, username: str, async_send: bool = True) -> bool:
   
    try:
        subject = "Welcome to our platform! 🎉"
        message = f"""Hello {username}!

        Welcome to our platform! Your registration was successful.

        We're excited to have you on board. You can now:
        - Browse our products
        - Make purchases
        - Track your orders
        - Update your profile

        If you have any questions, feel free to contact our support team.

        Best regards,
        The Team
        """
        
        if async_send:
            _send_email_async(subject, message, [email])
            logger.info(f"Welcome email queued for sending to {email}")
            return True
        else:
            if not getattr(settings, 'EMAIL_HOST_USER', None) or not getattr(settings, 'EMAIL_HOST_PASSWORD', None):
                logger.error("Email credentials not configured")
                return False
                
            send_mail(
                subject=subject,
                message=message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'),
                recipient_list=[email],
                fail_silently=False,
                timeout=getattr(settings, 'EMAIL_TIMEOUT', 30)
            )
            logger.info(f"Welcome email sent successfully to {email}")
            return True
            
    except Exception as e:
        logger.error(f"Failed to send welcome email to {email}: {str(e)}")
        return False
