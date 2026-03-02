#!/usr/bin/env python3
"""Direct Twilio SDK test - matches user's working code exactly"""

import os
from twilio.rest import Client

# Use credentials from .env (do not commit real values)
account_sid = os.environ.get('TWILIO_ACCOUNT_SID', 'YOUR_ACCOUNT_SID')
auth_token = os.environ.get('TWILIO_AUTH_TOKEN', 'YOUR_AUTH_TOKEN')

# Initialize client
client = Client(account_sid, auth_token)

try:
    # Use exact same parameters as user's working example
    message = client.messages.create(
        from_='whatsapp:+14155238886',
        content_sid='HXb5b62575e6e4ff6129ad7c8efe1f983e',
        content_variables='{"1":"Test","2":"Claw Bot"}',
        to='whatsapp:+85252975457'  # User's phone number from their example
    )

    print(f"✅ Success!")
    print(f"Message SID: {message.sid}")
    print(f"Status: {message.status}")
    print(f"To: {message.to}")
    print(f"From: {message.from_}")

except Exception as e:
    print(f"❌ Error: {e}")
    print(f"Error type: {type(e)}")
