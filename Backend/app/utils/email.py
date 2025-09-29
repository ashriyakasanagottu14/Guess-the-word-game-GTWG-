import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Template
from typing import List, Optional
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Email service for sending emails using SMTP."""
    
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.SMTP_FROM_EMAIL
        self.from_name = settings.SMTP_FROM_NAME

    async def send_email(
        self,
        to_emails: List[str],
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """
        Send an email to the specified recipients.
        
        Args:
            to_emails: List of recipient email addresses
            subject: Email subject
            html_content: HTML content of the email
            text_content: Plain text content (optional)
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            # Validate email configuration
            if not all([self.smtp_username, self.smtp_password, self.from_email]):
                logger.error("Email configuration is incomplete. Please check SMTP settings in .env file.")
                logger.error("Required: SMTP_USERNAME, SMTP_PASSWORD, SMTP_FROM_EMAIL")
                return False

            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.from_name} <{self.from_email}>"
            message["To"] = ", ".join(to_emails)

            # Add text content if provided
            if text_content:
                text_part = MIMEText(text_content, "plain")
                message.attach(text_part)

            # Add HTML content
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)

            # Send email
            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                start_tls=True,
                username=self.smtp_username,
                password=self.smtp_password,
            )

            logger.info(f"Email sent successfully to {to_emails}")
            return True

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to send email: {error_msg}")
            
            # Provide specific guidance for common Gmail errors
            if "Username and Password not accepted" in error_msg or "BadCredentials" in error_msg:
                logger.error("Gmail Authentication Failed! Please check:")
                logger.error("1. Enable 2-Factor Authentication on your Gmail account")
                logger.error("2. Generate an App Password (not your regular Gmail password)")
                logger.error("3. Use the App Password in SMTP_PASSWORD")
                logger.error("4. Ensure SMTP_USERNAME is your full Gmail address")
                logger.error("Visit: https://support.google.com/accounts/answer/185833")
            elif "Connection refused" in error_msg:
                logger.error("SMTP Connection Failed! Check SMTP_HOST and SMTP_PORT settings")
            elif "authentication failed" in error_msg.lower():
                logger.error("Authentication failed! Verify SMTP_USERNAME and SMTP_PASSWORD")
            
            return False

    async def send_otp_email(self, to_email: str, otp: str, username: str = None) -> bool:
        """
        Send OTP email for password reset.
        
        Args:
            to_email: Recipient email address
            otp: The OTP code
            username: Username (optional)
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        subject = "Password Reset OTP - Guess The Word Game"
        
        # HTML template for OTP email
        html_template = Template("""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Password Reset OTP</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }
                .container {
                    background-color: #f9f9f9;
                    padding: 30px;
                    border-radius: 10px;
                    border: 1px solid #ddd;
                }
                .header {
                    text-align: center;
                    color: #2c3e50;
                    margin-bottom: 30px;
                }
                .otp-box {
                    background-color: #3498db;
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 8px;
                    margin: 20px 0;
                    font-size: 24px;
                    font-weight: bold;
                    letter-spacing: 3px;
                }
                .warning {
                    background-color: #fff3cd;
                    border: 1px solid #ffeaa7;
                    color: #856404;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 20px 0;
                }
                .footer {
                    text-align: center;
                    margin-top: 30px;
                    color: #666;
                    font-size: 14px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎮 Guess The Word Game</h1>
                    <h2>Password Reset Request</h2>
                </div>
                
                {% if username %}
                <p>Hello <strong>{{ username }}</strong>,</p>
                {% else %}
                <p>Hello,</p>
                {% endif %}
                
                <p>You have requested to reset your password. Please use the following One-Time Password (OTP) to complete the process:</p>
                
                <div class="otp-box">
                    {{ otp }}
                </div>
                
                <div class="warning">
                    <strong>⚠️ Important:</strong>
                    <ul>
                        <li>This OTP is valid for <strong>10 minutes</strong> only</li>
                        <li>Do not share this code with anyone</li>
                        <li>If you didn't request this reset, please ignore this email</li>
                    </ul>
                </div>
                
                <p>Enter this OTP in the password reset form to create your new password.</p>
                
                <div class="footer">
                    <p>Thank you for playing Guess The Word Game!</p>
                    <p><em>This is an automated email. Please do not reply.</em></p>
                </div>
            </div>
        </body>
        </html>
        """)
        
        # Plain text version
        text_content = f"""
        Guess The Word Game - Password Reset OTP
        
        {'Hello ' + username + ',' if username else 'Hello,'}
        
        You have requested to reset your password. Please use the following OTP to complete the process:
        
        OTP: {otp}
        
        Important:
        - This OTP is valid for 10 minutes only
        - Do not share this code with anyone
        - If you didn't request this reset, please ignore this email
        
        Enter this OTP in the password reset form to create your new password.
        
        Thank you for playing Guess The Word Game!
        """
        
        html_content = html_template.render(otp=otp, username=username)
        
        return await self.send_email(
            to_emails=[to_email],
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )


# Create a singleton instance
email_service = EmailService()
