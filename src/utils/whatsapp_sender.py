"""WhatsApp sending utility using Twilio or WhatsApp Business API."""

import httpx
from typing import Optional, List
from src.utils.config import get_settings
from src.utils.logger import log

try:
    from twilio.rest import Client as TwilioClient
    TWILIO_SDK_AVAILABLE = True
except ImportError:
    TWILIO_SDK_AVAILABLE = False
    log.warning("Twilio SDK not installed. Install with: pip install twilio")


class WhatsAppSender:
    """WhatsApp message sender supporting both Twilio and Business API."""

    def __init__(self):
        self.settings = get_settings()
        self._validate_config()

    def _validate_config(self):
        """Validate WhatsApp configuration."""
        has_twilio = (
            self.settings.twilio_account_sid
            and self.settings.twilio_auth_token
            and self.settings.whatsapp_from
        )
        has_business = (
            self.settings.whatsapp_business_token and self.settings.whatsapp_phone_id
        )

        if not has_twilio and not has_business:
            log.warning("No WhatsApp credentials configured - WhatsApp sending disabled")
        elif has_twilio:
            log.info("WhatsApp configured with Twilio")
        elif has_business:
            log.info("WhatsApp configured with Business API")

    def send_message(
        self,
        to: str,
        message: str,
        media_url: Optional[str] = None,
        use_business_api: bool = False,
    ) -> bool:
        """
        Send a WhatsApp message.

        Args:
            to: Recipient phone number (format: +1234567890 or whatsapp:+1234567890)
            message: Message text
            media_url: Optional media URL
            use_business_api: Use Business API instead of Twilio

        Returns:
            True if message was sent successfully
        """
        if use_business_api or (
            self.settings.whatsapp_business_token and not self.settings.twilio_account_sid
        ):
            return self.send_message_via_business_api(to, message)
        else:
            return self.send_message_via_twilio(to, message, media_url)

    def send_message_via_twilio(
        self, to: str, message: str, media_url: Optional[str] = None
    ) -> bool:
        """
        Send WhatsApp message via Twilio using official SDK.

        Args:
            to: Recipient phone number
            message: Message text
            media_url: Optional media URL

        Returns:
            True if message was sent successfully
        """
        if not all(
            [
                self.settings.twilio_account_sid,
                self.settings.twilio_auth_token,
                self.settings.whatsapp_from,
            ]
        ):
            log.error("Twilio credentials not configured")
            return False

        if not TWILIO_SDK_AVAILABLE:
            log.error("Twilio SDK not installed. Install with: pip install twilio")
            return False

        try:
            # Initialize Twilio client
            client = TwilioClient(
                self.settings.twilio_account_sid,
                self.settings.twilio_auth_token
            )

            # Ensure phone numbers have whatsapp: prefix
            from_number = self.settings.whatsapp_from
            to_number = to if to.startswith("whatsapp:") else f"whatsapp:{to}"

            # Twilio Sandbox requires Content Templates
            # Using the default appointment reminder template
            message_params = {
                'from_': from_number,
                'to': to_number,
                'content_sid': 'HXb5b62575e6e4ff6129ad7c8efe1f983e',  # Twilio's sample template
                'content_variables': f'{{"1":"{message[:50]}","2":"Claw Bot"}}'
            }

            if media_url:
                message_params['media_url'] = [media_url]

            # Send message using Twilio SDK
            twilio_message = client.messages.create(**message_params)

            log.info(f"WhatsApp message sent via Twilio SDK. SID: {twilio_message.sid}, Status: {twilio_message.status}")
            return True

        except Exception as e:
            log.error(f"Failed to send WhatsApp via Twilio SDK: {e}")
            return False

    def send_message_via_business_api(self, to: str, message: str) -> bool:
        """
        Send WhatsApp message via WhatsApp Business API.

        Args:
            to: Recipient phone number
            message: Message text

        Returns:
            True if message was sent successfully
        """
        if not all(
            [self.settings.whatsapp_business_token, self.settings.whatsapp_phone_id]
        ):
            log.error("WhatsApp Business API credentials not configured")
            return False

        try:
            url = f"https://graph.facebook.com/v18.0/{self.settings.whatsapp_phone_id}/messages"

            headers = {
                "Authorization": f"Bearer {self.settings.whatsapp_business_token}",
                "Content-Type": "application/json",
            }

            # Remove whatsapp: prefix and + if present
            recipient = to.replace("whatsapp:", "").replace("+", "")

            payload = {
                "messaging_product": "whatsapp",
                "to": recipient,
                "type": "text",
                "text": {"body": message},
            }

            response = httpx.post(url, json=payload, headers=headers, timeout=10.0)
            response.raise_for_status()

            log.info(f"WhatsApp message sent via Business API to {to}")
            return True

        except Exception as e:
            log.error(f"Failed to send WhatsApp via Business API: {e}")
            return False

    def send_template_message(
        self,
        to: str,
        template_name: str,
        language_code: str = "en",
        parameters: Optional[List[str]] = None,
    ) -> bool:
        """
        Send a WhatsApp template message (Business API only).

        Args:
            to: Recipient phone number
            template_name: Template name
            language_code: Template language code
            parameters: Template parameters

        Returns:
            True if message was sent successfully
        """
        if not all(
            [self.settings.whatsapp_business_token, self.settings.whatsapp_phone_id]
        ):
            log.error("WhatsApp Business API credentials not configured")
            return False

        try:
            url = f"https://graph.facebook.com/v18.0/{self.settings.whatsapp_phone_id}/messages"

            headers = {
                "Authorization": f"Bearer {self.settings.whatsapp_business_token}",
                "Content-Type": "application/json",
            }

            # Remove whatsapp: prefix and + if present
            recipient = to.replace("whatsapp:", "").replace("+", "")

            # Build template components
            components = []
            if parameters:
                components.append(
                    {
                        "type": "body",
                        "parameters": [{"type": "text", "text": p} for p in parameters],
                    }
                )

            payload = {
                "messaging_product": "whatsapp",
                "to": recipient,
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {"code": language_code},
                    "components": components,
                },
            }

            response = httpx.post(url, json=payload, headers=headers, timeout=10.0)
            response.raise_for_status()

            log.info(f"WhatsApp template sent via Business API to {to}")
            return True

        except Exception as e:
            log.error(f"Failed to send WhatsApp template: {e}")
            return False
