"""
Postmark Email Service for sending transactional emails
Documentation: https://postmarkapp.com/developer/user-guide/send-email-with-api
"""
import logging
import requests
from pathlib import Path
from typing import Dict, Any, Optional
from django.conf import settings
from django.template import Template, Context

logger = logging.getLogger(__name__)


class PostmarkEmailService:
    """
    Service class for sending emails via Postmark API
    """
    
    def __init__(self):
        self.api_key = getattr(settings, 'POSTMARK_API_KEY', None)
        self.api_url = 'https://api.postmarkapp.com/email'
        self.from_email = getattr(settings, 'POSTMARK_FROM_EMAIL', None)
        
        # Template directory
        self.template_dir = Path(__file__).parent.parent / 'templates' / 'emails'
        
        if not self.api_key:
            logger.error("POSTMARK_API_KEY not configured in settings")
        if not self.from_email:
            logger.error("POSTMARK_FROM_EMAIL not configured in settings")
    
    def _load_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        Load and render an email template
        
        Args:
            template_name: Name of the template file (without extension)
            context: Template context variables
            
        Returns:
            Rendered template content
        """
        template_path = self.template_dir / f"{template_name}"
        
        try:
            with open(template_path, 'r', encoding='utf-8') as file:
                template_content = file.read()
            
            template = Template(template_content)
            return template.render(Context(context))
            
        except FileNotFoundError:
            logger.error(f"Email template not found: {template_path}")
            raise
        except Exception as e:
            logger.error(f"Error rendering email template {template_path}: {str(e)}")
            raise
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        text_body: str,
        html_body: Optional[str] = None,
        from_email: Optional[str] = None,
        tag: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send email via Postmark API
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            text_body: Plain text email body
            html_body: HTML email body (optional)
            from_email: Sender email (optional, uses default if not provided)
            tag: Email tag for tracking (optional)
            
        Returns:
            Dict containing response data or error information
        """
        if not self.api_key:
            error_msg = "Postmark API key not configured"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
        
        # Use provided from_email or fallback to configured default
        sender_email = from_email or self.from_email
        if not sender_email:
            error_msg = "No from email configured"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
        
        # Prepare email payload
        payload = {
            "From": sender_email,
            "To": to_email,
            "Subject": subject,
            "TextBody": text_body
        }
        
        # Add optional fields
        if html_body:
            payload["HtmlBody"] = html_body
        if tag:
            payload["Tag"] = tag
        
        # Prepare headers
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Postmark-Server-Token": self.api_key
        }
        
        try:
            logger.info(f"Sending email to {to_email} via Postmark")
            response = requests.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            response_data = response.json()
            
            if response.status_code == 200:
                logger.info(f"Email sent successfully to {to_email}. MessageID: {response_data.get('MessageID')}")
                return {
                    "success": True,
                    "message_id": response_data.get("MessageID"),
                    "to": response_data.get("To"),
                    "submitted_at": response_data.get("SubmittedAt")
                }
            else:
                error_msg = f"Postmark API error: {response_data.get('Message', 'Unknown error')}"
                logger.error(f"Failed to send email to {to_email}: {error_msg}")
                return {
                    "success": False,
                    "error": error_msg,
                    "error_code": response_data.get("ErrorCode")
                }
                
        except requests.exceptions.Timeout:
            error_msg = "Postmark API request timed out"
            logger.error(f"Timeout sending email to {to_email}")
            return {"success": False, "error": error_msg}
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error sending email: {str(e)}"
            logger.error(f"Network error sending email to {to_email}: {error_msg}")
            return {"success": False, "error": error_msg}
            
        except Exception as e:
            error_msg = f"Unexpected error sending email: {str(e)}"
            logger.exception(f"Unexpected error sending email to {to_email}")
            return {"success": False, "error": error_msg}
    
    def send_password_reset_email(
        self,
        to_email: str,
        reset_url: str,
        user_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send password reset email with professional template
        
        Args:
            to_email: User's email address
            reset_url: Password reset URL with token
            user_name: User's name for personalization (optional)
            
        Returns:
            Dict containing response data or error information
        """
        subject = "Reset Your Password - CBaaS"
        
        # Personalize greeting
        greeting = f"Hi {user_name}," if user_name else "Hi,"
        
        # Template context
        context = {
            'greeting': greeting,
            'reset_url': reset_url,
            'user_name': user_name,
            'to_email': to_email
        }
        
        try:
            # Load and render templates
            text_body = self._load_template('password_reset.txt', context)
            html_body = self._load_template('password_reset.html', context)
            
            return self.send_email(
                to_email=to_email,
                subject=subject,
                text_body=text_body,
                html_body=html_body,
                tag="password-reset"
            )
            
        except Exception as e:
            error_msg = f"Error loading email template: {str(e)}"
            logger.error(f"Failed to load email template for {to_email}: {error_msg}")
            return {"success": False, "error": error_msg}


# Singleton instance for app-wide usage
postmark_service = PostmarkEmailService()
