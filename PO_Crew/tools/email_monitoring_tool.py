from crewai.tools import BaseTool
from typing import Type, List, Dict, Any, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from email import message_from_bytes
import os
import imaplib
import json
import re
from datetime import datetime

load_dotenv()

def connect_to_gmail_imap(user: str, password: str):
    """Connect to Gmail IMAP server"""
    imap_url = 'imap.gmail.com'
    try:
        mail = imaplib.IMAP4_SSL(imap_url)
        mail.login(user, password)
        mail.select('inbox')  # Connect to the inbox
        return mail
    except Exception as e:
        raise Exception(f"Failed to connect to Gmail IMAP: {str(e)}")

class FetchEmailsInput(BaseModel):
    """Input schema for FetchEmailsTool."""
    # No parameters needed - tool is now fixed to last 50 emails with attachments only

class FetchEmailsTool(BaseTool):
    name: str = "Fetch Emails Tool"
    description: str = (
        "Fetches up to the last 50 unread emails from Gmail inbox and saves only those with attachments. "
        "Returns sender, subject, body content, and saved attachment paths."
    )
    args_schema: Type[BaseModel] = FetchEmailsInput

    def _run(self) -> str:
        """
        Fetch up to the last 50 unread emails and save only those with attachments.
        Returns:
            JSON string with emails that have attachments, including sender, subject, body, and attachment paths
        """
        try:
            user = os.getenv('supemail')
            password = os.getenv('suppassword')
            
            if not user or not password:
                return json.dumps({
                    "status": "error",
                    "message": "Email credentials not found. Please set 'email' and 'password' in environment variables."
                })

            # Connect to Gmail
            mail = connect_to_gmail_imap(user, password)
            
            # Search for unread emails only and exclude emails sent by self
            status, messages = mail.search(None, 'UNSEEN', f'NOT FROM "{user}"')
            if status != 'OK':
                raise Exception(f"Failed to search emails: {status}")
                
            email_ids = messages[0].split()
            
            # Get last 50 emails
            email_ids = email_ids[-50:] if len(email_ids) > 50 else email_ids
            
            emails_with_attachments = []
            processed_count = 0

            for email_id in reversed(email_ids):  # Process latest first
                try:
                    status, msg_data = mail.fetch(email_id, '(RFC822)')
                    if status != 'OK':
                        continue
                        
                    for response_part in msg_data:
                        if isinstance(response_part, tuple):
                            email_message = message_from_bytes(response_part[1])
                            
                            # Extract email details
                            from_header = email_message.get('From', 'Unknown')
                            subject_header = email_message.get('Subject', 'No Subject')
                            date_header = email_message.get('Date', '')
                            
                            # Skip if email is from the authenticated user (additional check)
                            if user.lower() in from_header.lower():
                                continue
                            
                            body = ""
                            file_paths = []

                            # Extract body content and attachments
                            if email_message.is_multipart():
                                for part in email_message.walk():
                                    content_type = part.get_content_type()
                                    
                                    if content_type == "text/plain" and not body:
                                        try:
                                            body = part.get_payload(decode=True).decode('utf-8')
                                        except (UnicodeDecodeError, AttributeError):
                                            body = str(part.get_payload())
                                    
                                    # Handle attachments - save all attachments
                                    elif (content_type == "application/octet-stream" or 
                                          part.get('Content-Disposition') is not None):
                                        filename = part.get_filename()
                                        if filename:
                                            # Clean filename for security
                                            filename = re.sub(r'[^\w\-_\.]', '_', filename)
                                            # Create attachments directory if it doesn't exist
                                            project_root = os.getcwd()
                                            attachments_dir = os.path.join(project_root, "data", "email_attachments")
                                            os.makedirs(attachments_dir, exist_ok=True)
                                            filepath = os.path.join(attachments_dir, f"{email_id.decode()}_{filename}")
                                            try:
                                                with open(filepath, 'wb') as f:
                                                    f.write(part.get_payload(decode=True))
                                                file_paths.append(filepath)
                                            except Exception as e:
                                                print(f"Failed to save attachment {filename}: {e}")
                            else:
                                try:
                                    body = email_message.get_payload(decode=True).decode('utf-8')
                                except (UnicodeDecodeError, AttributeError):
                                    body = str(email_message.get_payload())

                            # Only save emails with attachments
                            if file_paths:
                                email_detail = {
                                    "sender": from_header,
                                    "subject": subject_header,
                                    "body": body,
                                    "attachment_paths": file_paths,
                                    "date": date_header
                                }
                                
                                emails_with_attachments.append(email_detail)
                            
                            processed_count += 1
                            
                except Exception as e:
                    print(f"Failed to process email {email_id}: {e}")
                    continue

            # Close connection
            mail.close()
            mail.logout()
            
            # Prepare response
            if not emails_with_attachments:
                result = {
                    "status": "success",
                    "total_emails_processed": processed_count,
                    "emails_with_attachments_count": 0,
                    "timestamp": datetime.now().isoformat(),
                    "message": "There were no purchase orders to be found",
                    "emails": []
                }
            else:
                result = {
                    "status": "success",
                    "total_emails_processed": processed_count,
                    "emails_with_attachments_count": len(emails_with_attachments),
                    "timestamp": datetime.now().isoformat(),
                    "emails": emails_with_attachments
                }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            })

class EmailMonitoringTool(BaseTool):
    """Simplified email monitoring tool - fetches unread emails with attachments"""
    name: str = "EmailMonitoringTool"
    description: str = (
        "Fetches up to the last 50 unread emails and saves only those with attachments."
    )

    def _run(self, **kwargs) -> str:
        """
        Fetch up to the last 50 unread emails and save only those with attachments
        """
        fetch_tool = FetchEmailsTool()
        return fetch_tool._run()
        

if __name__ == "__main__":
    # Test the FetchEmailsTool
    tool = FetchEmailsTool()
    result = tool._run()
    print(result)
    
    # # Test the legacy EmailMonitoringTool
    # legacy_tool = EmailMonitoringTool()
    # legacy_result = legacy_tool._run()
    # print(legacy_result)
