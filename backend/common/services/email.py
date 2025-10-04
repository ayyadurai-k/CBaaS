import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class SMTPEmailService:
    """
    Service class for sending transactional emails via SMTP (Django EmailMessage).
    """

    def send_password_reset_email(
        self,
        to_email: str,
        reset_url: str,
        user_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send password reset email.
        """
        subject = "Reset Your Password - CBaaS"
        greeting = f"Hi {user_name}," if user_name else "Hi,"

        context = {
            "greeting": greeting,
            "reset_url": reset_url,
            "user_name": user_name,
            "to_email": to_email,
        }

        try:
            logger.debug(f"Preparing to send password reset email to {to_email} with reset_url: {reset_url} and user_name: {user_name}")
            text_body = render_to_string("emails/password_reset.txt", context)
            html_body = render_to_string("emails/password_reset.html", context)

            logger.debug(f"Rendered text_body: {text_body}")
            logger.debug(f"Rendered html_body: {html_body}")

            email = EmailMultiAlternatives(
                subject=subject,
                body=text_body,
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                to=[to_email],
            )
            logger.debug(f"EmailMultiAlternatives created with subject: {subject}, from_email: {getattr(settings, 'DEFAULT_FROM_EMAIL', None)}, to: {[to_email]}")
            if html_body:
                email.attach_alternative(html_body, "text/html")
                logger.debug("HTML alternative attached to email.")

            email.send(fail_silently=False)
            logger.info(f"Password reset email successfully sent to {to_email}")
            logger.info(f"Password reset email sent to {to_email}")
            return {"success": True, "to": to_email}

        except Exception as e:
            logger.error(f"Exception occurred while sending password reset email to {to_email}: {str(e)}", exc_info=True)
            logger.error(f"Failed to send password reset email to {to_email}: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}


# Singleton instance
smtp_service = SMTPEmailService()
