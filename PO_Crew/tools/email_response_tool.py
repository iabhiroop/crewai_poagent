from crewai.tools import BaseTool
from typing import Dict, Any, List, Optional, Type
from pydantic import BaseModel, Field
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formataddr
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import json

load_dotenv()

class EmailResponseInput(BaseModel):
    """Input schema for EmailResponseGeneratorTool."""
    subject: str = Field(description="Email subject line")
    body: str = Field(description="Email body content")
    recipient_email: str = Field(description="Recipient email address")
    recipient_name: Optional[str] = Field(default="", description="Recipient name (optional)")
    po_number: Optional[str] = Field(default="", description="Purchase order number (optional)")
    urgent: Optional[bool] = Field(default=False, description="Mark email as urgent/high priority")
    

class EmailResponseGeneratorTool(BaseTool):
    name: str = "EmailResponseGeneratorTool"
    description: str = (
        "Sends automated email responses for purchase orders and general business communications. "
        "This tool can send emails with custom subject, body, and recipient information. "
        "Supports urgent/high priority email marking. Uses supervisor email credentials for sending. "
        "Required parameters: subject, body, recipient_email. "
        "Optional parameters: recipient_name, po_number, urgent (default: false)."
    )
    args_schema: Type[BaseModel] = EmailResponseInput
    
    def _send_email(self, email_content: Dict[str, str], recipient_email: str, recipient_name: str,
                   po_number: str, response_type: str, urgent: bool) -> str:
        """Send the response email using supervisor credentials"""
        
        # Get email configuration from environment (using supervisor credentials)
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        sender_email = os.getenv('supemail', '')
        sender_password = os.getenv('suppassword', '')
        sender_name = os.getenv('SUPPLIER_SENDER_NAME', 'Production Department')
        
        if not sender_email or not sender_password:
            return "Error: Supervisor email credentials not configured. Please set 'supemail' and 'suppassword' environment variables."
        
        try:
            # Create message
            message = MIMEMultipart()
            message["From"] = formataddr((sender_name, sender_email))
            message["To"] = recipient_email
            message["Subject"] = email_content["subject"]
            
            # Add urgency header if urgent
            if urgent:
                message["X-Priority"] = "1"
                message["X-MSMail-Priority"] = "High"
                message["Importance"] = "High"
            
            # Add body
            message.attach(MIMEText(email_content["body"], "plain"))
            
            # Send email
            context = ssl.create_default_context()
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls(context=context)
                server.login(sender_email, sender_password)
                text = message.as_string()
                server.sendmail(sender_email, [recipient_email], text)
            
            urgency_info = " [URGENT]" if urgent else ""
            
            return f"SUCCESS: {response_type.title()} email sent to {recipient_email}{urgency_info}\nPO Number: {po_number}\nSubject: {email_content['subject']}"
        
        except smtplib.SMTPAuthenticationError:
            return "Error: Email authentication failed. Please check supervisor email credentials (supemail/supassword)."
        except smtplib.SMTPRecipientsRefused:
            return f"Error: Recipient email address '{recipient_email}' was refused by the server."
        except Exception as e:
            return f"Error sending email: {str(e)}"
    
    def _run(self, subject: str, body: str, recipient_email: str, 
             recipient_name: str = "", po_number: str = "", urgent: bool = False) -> str:
        """
        Send an email with the specified subject, body, and recipient.
        
        Args:
            subject: Email subject line
            body: Email body content
            recipient_email: Recipient email address
            recipient_name: Recipient name (optional)
            po_number: Purchase order number (optional)
            urgent: Mark email as urgent/high priority (optional)
            
        Returns:
            String indicating success or error message
        """
        try:
            # Validate required inputs
            if not subject or not body or not recipient_email:
                return "Error: Subject, body, and recipient_email are required parameters."
            
            # Validate email format (basic check)
            if "@" not in recipient_email or "." not in recipient_email:
                return f"Error: Invalid email format for recipient: {recipient_email}"
            
            # Create email content dictionary
            email_content = {
                "subject": subject,
                "body": body
            }
            
            # Add PO number to subject if provided
            if po_number:
                email_content["subject"] = f"[PO: {po_number}] {subject}"
            
            # Add urgency indicator to subject if urgent
            if urgent:
                email_content["subject"] = f"[URGENT] {email_content['subject']}"
            
            # Use recipient name if provided, otherwise use email
            display_name = recipient_name if recipient_name else recipient_email
            
            # Determine response type for logging
            response_type = "urgent email" if urgent else "email"
            
            # Send the email
            result = self._send_email(
                email_content=email_content,
                recipient_email=recipient_email,
                recipient_name=display_name,
                po_number=po_number or "N/A",
                response_type=response_type,
                urgent=urgent
            )
            
            return result
            
        except Exception as e:
            return f"Error in email processing: {str(e)}"