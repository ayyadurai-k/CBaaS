import logging
from celery import shared_task
from common.services.email import smtp_service

logger = logging.getLogger(__name__)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def send_password_reset_email_task(self, to_email: str, reset_url: str, user_name: str = None):
    """
    Asynchronous task to send password reset email.
    """
    try:
        result = smtp_service.send_password_reset_email(
            to_email=to_email,
            reset_url=reset_url,
            user_name=user_name,
        )
        
        if result.get("success"):
            logger.info(f"Password reset email sent successfully to {to_email}")
        else:
            logger.error(f"Failed to send password reset email to {to_email}: {result.get('error')}")
            # Raise exception to trigger retry
            raise Exception(f"Email sending failed: {result.get('error')}")
            
        return result
    except Exception as e:
        logger.error(f"Error in send_password_reset_email_task for {to_email}: {str(e)}")
        raise