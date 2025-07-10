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
from datetime import datetime
import json

load_dotenv()

class PoEmailGeneratorInput(BaseModel):
    """Input schema for PoEmailGeneratorTool."""
    action: str = Field(default="send_po_email", description="Action to perform: send_po_email, create_email_draft")
    supplier_email: str = Field(description="Email address of the supplier")
    supplier_name: str = Field(description="Name of the supplier")
    po_number: Optional[str] = Field(default="", description="Purchase Order number")
    po_data: Optional[Dict] = Field(default={}, description="Purchase order data (items, quantities, pricing)")
    po_file_path: Optional[str] = Field(default="", description="Path to PDF purchase order file")
    delivery_date: Optional[str] = Field(default="", description="Expected delivery date")
    special_instructions: Optional[str] = Field(default="", description="Special delivery or handling instructions")
    cc_emails: Optional[List[str]] = Field(default=[], description="CC email addresses")
    urgent: Optional[bool] = Field(default=False, description="Mark as urgent priority")

class PoEmailGeneratorTool(BaseTool):
    name: str = "PoEmailGeneratorTool"
    description: str = (
        "Sends purchase order emails to suppliers with professional formatting and optional PDF attachments. "
        "Can create email drafts or send emails directly. Supports CC recipients, urgent marking, "
        "and includes purchase order details in both email body and optional PDF attachment."
    )
    args_schema: Type[BaseModel] = PoEmailGeneratorInput

    def _run(self, action: str = "send_po_email", supplier_email: str = "", supplier_name: str = "",
             po_number: str = "", po_data: Dict = {}, po_file_path: str = "",
             delivery_date: str = "", special_instructions: str = "", 
             cc_emails: List[str] = [], urgent: bool = False) -> str:
        """
        Generate and send purchase order emails to suppliers
        
        Args:
            action: Action to perform (send_po_email, create_email_draft)
            supplier_email: Email address of the supplier
            supplier_name: Name of the supplier
            po_number: Purchase Order number
            po_data: Purchase order data dictionary
            po_file_path: Path to PDF purchase order file
            delivery_date: Expected delivery date
            special_instructions: Special instructions
            cc_emails: List of CC email addresses
            urgent: Mark as urgent priority
        """
        try:
            if not supplier_email:
                return "Error: Supplier email address is required"
            
            if not supplier_name:
                return "Error: Supplier name is required"

            # Generate PO number if not provided
            if not po_number:
                po_number = self._generate_po_number()

            # Create email content
            email_content = self._create_email_content(
                supplier_name, po_number, po_data, delivery_date, special_instructions, urgent
            )

            if action == "create_email_draft":
                return self._create_email_draft(email_content, supplier_email, supplier_name, po_number)
            
            elif action == "send_po_email":
                return self._send_email(
                    email_content, supplier_email, supplier_name, po_number, 
                    po_file_path, cc_emails, urgent
                )
            
            else:
                return f"Error: Unknown action '{action}'. Supported actions: send_po_email, create_email_draft"

        except Exception as e:
            return f"Error in PoEmailGeneratorTool: {str(e)}"

    def _generate_po_number(self) -> str:
        """Generate a unique purchase order number"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M")
        return f"PO-{timestamp}"

    def _create_email_content(self, supplier_name: str, po_number: str, po_data: Dict,
                            delivery_date: str, special_instructions: str, urgent: bool) -> Dict[str, str]:
        """Create email subject and body content"""
        
        # Create subject line
        urgency_prefix = "[URGENT] " if urgent else ""
        subject = f"{urgency_prefix}Purchase Order {po_number} - {supplier_name}"
        
        # Create email body
        company_name = os.getenv('COMPANY_NAME', 'Your Company')
        sender_name = os.getenv('SENDER_NAME', 'Procurement Department')
        
        body = f"""Dear {supplier_name} Team,

I hope this email finds you well. We are pleased to send you our purchase order for your review and processing.

PURCHASE ORDER DETAILS:
"""
        
        if urgent:
            body += """
⚠️  URGENT PRIORITY ORDER ⚠️
This order requires expedited processing and delivery.
"""
        
        body += f"""
Purchase Order Number: {po_number}
Date: {datetime.now().strftime("%B %d, %Y")}
Company: {company_name}
"""
        
        if delivery_date:
            body += f"Requested Delivery Date: {delivery_date}\n"
        
        # Add items if available
        if po_data and 'items' in po_data:
            body += "\nORDER ITEMS:\n"
            body += "-" * 60 + "\n"
            total_amount = 0
            
            for idx, item in enumerate(po_data['items'], 1):
                item_name = item.get('item_name', item.get('name', f'Item {idx}'))
                quantity = item.get('quantity', item.get('qty', 0))
                unit_price = item.get('unit_price', item.get('price', 0))
                line_total = quantity * unit_price
                total_amount += line_total
                
                body += f"{idx}. {item_name}\n"
                body += f"   Quantity: {quantity}\n"
                body += f"   Unit Price: ${unit_price:.2f}\n"
                body += f"   Line Total: ${line_total:.2f}\n\n"
            
            body += "-" * 60 + "\n"
            body += f"TOTAL ORDER VALUE: ${total_amount:.2f}\n\n"
        
        # Add special instructions
        if special_instructions:
            body += f"SPECIAL INSTRUCTIONS:\n{special_instructions}\n\n"
        
        # Add standard terms
        body += """DELIVERY INFORMATION:
Please confirm receipt of this purchase order and provide:
1. Order acknowledgment with expected delivery date
2. Tracking information once items are shipped
3. Any changes to pricing or availability

PAYMENT TERMS:
Payment will be processed according to our standard terms upon receipt and verification of goods.

Please don't hesitate to contact us if you have any questions regarding this order.

Thank you for your continued partnership.

Best regards,
"""
        
        body += f"{sender_name}\n"
        body += f"{company_name}\n"
        
        contact_email = os.getenv('CONTACT_EMAIL', '')
        contact_phone = os.getenv('CONTACT_PHONE', '')
        
        if contact_email:
            body += f"Email: {contact_email}\n"
        if contact_phone:
            body += f"Phone: {contact_phone}\n"
        
        return {
            "subject": subject,
            "body": body
        }

    def _create_email_draft(self, email_content: Dict[str, str], supplier_email: str, 
                          supplier_name: str, po_number: str) -> str:
        """Create an email draft for review"""
        draft = f"""
EMAIL DRAFT FOR REVIEW:
======================

TO: {supplier_email}
SUBJECT: {email_content['subject']}

BODY:
{email_content['body']}

======================
Draft created for Purchase Order {po_number} to {supplier_name}
Review the content above and use action='send_po_email' to send the email.
"""
        return draft

    def _send_email(self, email_content: Dict[str, str], supplier_email: str, supplier_name: str,
                   po_number: str, po_file_path: str, cc_emails: List[str], urgent: bool) -> str:
        """Send the purchase order email"""
        
        # Get email configuration from environment
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        sender_email = os.getenv('SENDER_EMAIL', os.getenv('email', ''))
        sender_password = os.getenv('SENDER_PASSWORD', os.getenv('password', ''))
        sender_name = os.getenv('SENDER_NAME', 'Procurement Department')
        
        if not sender_email or not sender_password:
            return "Error: Email credentials not configured. Please set SENDER_EMAIL and SENDER_PASSWORD environment variables."
        
        try:
            # Create message
            message = MIMEMultipart()
            message["From"] = formataddr((sender_name, sender_email))
            message["To"] = supplier_email
            message["Subject"] = email_content["subject"]
            
            # Add CC recipients
            if cc_emails:
                message["Cc"] = ", ".join(cc_emails)
            
            # Add urgency header if urgent
            if urgent:
                message["X-Priority"] = "1"
                message["X-MSMail-Priority"] = "High"
            
            # Add body
            message.attach(MIMEText(email_content["body"], "plain"))
            
            # Add PDF attachment if provided
            if po_file_path and os.path.exists(po_file_path):
                with open(po_file_path, "rb") as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= PO_{po_number}.pdf'
                )
                message.attach(part)
            
            # Create recipient list (TO + CC)
            recipients = [supplier_email] + cc_emails
            
            # Send email
            context = ssl.create_default_context()
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls(context=context)
                server.login(sender_email, sender_password)
                text = message.as_string()
                server.sendmail(sender_email, recipients, text)
            
            attachment_info = f" with PDF attachment ({os.path.basename(po_file_path)})" if po_file_path and os.path.exists(po_file_path) else ""
            cc_info = f" (CC: {', '.join(cc_emails)})" if cc_emails else ""
            urgency_info = " [URGENT]" if urgent else ""
            
            return f"SUCCESS: Purchase Order email sent to {supplier_email}{cc_info}{urgency_info}\nPO Number: {po_number}\nSubject: {email_content['subject']}{attachment_info}"
        
        except smtplib.SMTPAuthenticationError:
            return "Error: Email authentication failed. Please check your email credentials."
        except smtplib.SMTPRecipientsRefused:
            return f"Error: Recipient email address '{supplier_email}' was refused by the server."
        except Exception as e:
            return f"Error sending email: {str(e)}"


# Test the tool
if __name__ == "__main__":
    tool = PoEmailGeneratorTool()
    
    # Test data
    test_po_data = {
        "items": [
            {"item_name": "Widget A", "quantity": 100, "unit_price": 5.50},
            {"item_name": "Component B", "quantity": 50, "unit_price": 12.00},
            {"item_name": "Material C", "quantity": 200, "unit_price": 2.25}
        ]
    }

    
    # Test email draft creation
    print("Testing email draft creation:")
    result = tool._run(
        action="send_po_email",
        supplier_email="supplier@example.com",
        supplier_name="ABC Supplies Inc",
        po_number="PO-2024001",
        po_data=test_po_data,
        delivery_date="2024-02-15",
        special_instructions="Please deliver to loading dock B. Contact security for access.",
        urgent=True,
        po_file_path=r'C:\Users\ilasy\crewai\poagent\PO-20250525-6370.pdf'
    )
    print(result)
    print("\n" + "="*80 + "\n")
