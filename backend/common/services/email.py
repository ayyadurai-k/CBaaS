"""
Postmark Email Service for sending transactional emails
Documentation: https://postmarkapp.com/developer/user-guide/send-email-with-api
"""
import logging
import requests
from typing import Dict, Any, Optional
from django.conf import settings

logger = logging.getLogger(__name__)


class PostmarkEmailService:
    """
    Service class for sending emails via Postmark API
    """
    
    def __init__(self):
        self.api_key = getattr(settings, 'POSTMARK_API_KEY', None)
        self.api_url = 'https://api.postmarkapp.com/email'
        self.from_email = getattr(settings, 'POSTMARK_FROM_EMAIL', None)
        
        if not self.api_key:
            logger.error("POSTMARK_API_KEY not configured in settings")
        if not self.from_email:
            logger.error("POSTMARK_FROM_EMAIL not configured in settings")
    
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
        
        # Plain text version
        text_body = f"""{greeting}

We received a request to reset the password for your CBaaS account.

Click the link below to reset your password:
{reset_url}

This link will expire in 1 hour for security reasons.

If you didn't request this password reset, you can safely ignore this email. Your password will remain unchanged.

If you're having trouble clicking the link, copy and paste the URL into your web browser.

Best regards,
The CBaaS Team

---
This is an automated email. Please do not reply to this email address.
"""

        # HTML version with better formatting
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reset Your Password</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #3B82F6; color: white; padding: 30px 20px; text-align: center; border-radius: 8px 8px 0 0; }}
        .content {{ background-color: #ffffff; padding: 40px 30px; border: 1px solid #e5e7eb; border-top: none; }}
        .button {{ display: inline-block; background-color: #3B82F6; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; font-weight: 600; margin: 20px 0; }}
        .button:hover {{ background-color: #2563EB; }}
        .footer {{ background-color: #f8fafc; padding: 20px; text-align: center; font-size: 14px; color: #6b7280; border-radius: 0 0 8px 8px; border: 1px solid #e5e7eb; border-top: none; }}
        .warning {{ background-color: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin: 20px 0; border-radius: 4px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1 style="margin: 0; font-size: 24px;">Reset Your Password</h1>
    </div>
    
    <div class="content">
        <p>{greeting}</p>
        
        <p>We received a request to reset the password for your <strong>CBaaS</strong> account.</p>
        
        <p>Click the button below to reset your password:</p>
        
        <p style="text-align: center;">
            <a href="{reset_url}" class="button">Reset Password</a>
        </p>
        
        <div class="warning">
            <strong>⏰ Important:</strong> This link will expire in 1 hour for security reasons.
        </div>
        
        <p>If you didn't request this password reset, you can safely ignore this email. Your password will remain unchanged.</p>
        
        <p>If you're having trouble clicking the button, copy and paste this URL into your web browser:</p>
        <p style="word-break: break-all; background-color: #f3f4f6; padding: 10px; border-radius: 4px; font-family: monospace; font-size: 12px;">
            {reset_url}
        </p>
        
        <p>Best regards,<br>
        <strong>The CBaaS Team</strong></p>
    </div>
    
    <div class="footer">
        This is an automated email. Please do not reply to this email address.
    </div>
</body>
</html>
"""

        return self.send_email(
            to_email=to_email,
            subject=subject,
            text_body=text_body,
            html_body=html_body,
            tag="password-reset"
        )


# Singleton instance for app-wide usage
postmark_service = PostmarkEmailService()
