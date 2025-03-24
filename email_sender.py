import smtplib
import os
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

def send_feedback_email(sender_name, message_content):
    """Send a simple feedback email using SMTP.
    
    Args:
        sender_name: Name of the person sending feedback
        message_content: The feedback message
    
    Returns:
        Boolean indicating success and a message
    """
    try:
        # Get email credentials from environment variables
        gmail_user = os.getenv('GMAIL_USER')
        gmail_password = os.getenv('GMAIL_PASSWORD')
        
        if not gmail_user or not gmail_password:
            return False, "Email credentials not configured in .env file"
        
        # Set up the email content
        subject = f'Assignment Tool Feedback from {sender_name}'
        body = f"""
Feedback from Assignment Automation Tool

From: {sender_name}

Message:
{message_content}
        """
        
        # Create email
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = gmail_user
        msg['To'] = gmail_user  # Sending to yourself
        
        # Connect to Gmail and send
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(gmail_user, gmail_password)
        server.send_message(msg)
        server.quit()
        
        return True, "Feedback sent successfully!"
        
    except Exception as e:
        return False, f"Error sending email: {str(e)}"