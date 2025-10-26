from twilio.rest import Client
import os
from dotenv import load_dotenv

load_dotenv()

# Twilio credentials
account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
whatsapp_number = os.getenv('WHATSAPP_PHONE_NUMBER')

client = Client(account_sid, auth_token)

def send_whatsapp_alert(to_number, message):
    """
    Send a WhatsApp message using Twilio
    :param to_number: Recipient's phone number (including country code)
    :param message: Message content
    """
    try:
        # Format the 'to' number for WhatsApp
        to_whatsapp_number = f"whatsapp:{to_number}"
        from_whatsapp_number = f"whatsapp:{whatsapp_number}"
        
        message = client.messages.create(
            from_=from_whatsapp_number,
            body=message,
            to=to_whatsapp_number
        )
        
        return True, message.sid
    except Exception as e:
        return False, str(e)