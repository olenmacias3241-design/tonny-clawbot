"""Telegram Bot API sending utility."""

import httpx
from typing import Optional, Dict, Any
from src.utils.config import get_settings
from src.utils.logger import log


class TelegramSender:
    """Telegram message sender using Bot API."""

    def __init__(self):
        self.settings = get_settings()
        self._validate_config()
        if self.settings.telegram_bot_token:
            self.api_url = f"https://api.telegram.org/bot{self.settings.telegram_bot_token}"

    def _validate_config(self):
        """Validate Telegram configuration."""
        if not self.settings.telegram_bot_token:
            log.warning("TELEGRAM_BOT_TOKEN not configured - Telegram sending disabled")
        if not self.settings.telegram_default_chat_id:
            log.warning("TELEGRAM_DEFAULT_CHAT_ID not configured - will need to specify chat_id in requests")

    def send_message(
        self,
        text: str,
        chat_id: Optional[str] = None,
        parse_mode: str = "Markdown",
        disable_notification: bool = False,
    ) -> bool:
        """
        Send a Telegram message.

        Args:
            text: Message text
            chat_id: Recipient chat ID (uses default if not specified)
            parse_mode: Message formatting (Markdown, HTML, or None)
            disable_notification: Send silently

        Returns:
            True if message was sent successfully
        """
        if not self.settings.telegram_bot_token:
            log.error("Telegram bot token not configured")
            return False

        recipient = chat_id or self.settings.telegram_default_chat_id
        if not recipient:
            log.error("No chat_id specified and no default configured")
            return False

        try:
            url = f"{self.api_url}/sendMessage"
            payload = {
                "chat_id": recipient,
                "text": text,
                "parse_mode": parse_mode,
                "disable_notification": disable_notification,
            }

            response = httpx.post(url, json=payload, timeout=10.0)
            response.raise_for_status()

            log.info(f"Telegram message sent successfully to chat_id: {recipient}")
            return True

        except Exception as e:
            log.error(f"Failed to send Telegram message: {e}")
            return False

    def send_photo(
        self,
        photo_url: str,
        caption: Optional[str] = None,
        chat_id: Optional[str] = None,
    ) -> bool:
        """
        Send a photo via Telegram.

        Args:
            photo_url: URL of the photo
            caption: Photo caption
            chat_id: Recipient chat ID (uses default if not specified)

        Returns:
            True if photo was sent successfully
        """
        if not self.settings.telegram_bot_token:
            log.error("Telegram bot token not configured")
            return False

        recipient = chat_id or self.settings.telegram_default_chat_id
        if not recipient:
            log.error("No chat_id specified and no default configured")
            return False

        try:
            url = f"{self.api_url}/sendPhoto"
            payload = {
                "chat_id": recipient,
                "photo": photo_url,
            }

            if caption:
                payload["caption"] = caption

            response = httpx.post(url, json=payload, timeout=10.0)
            response.raise_for_status()

            log.info(f"Telegram photo sent successfully to chat_id: {recipient}")
            return True

        except Exception as e:
            log.error(f"Failed to send Telegram photo: {e}")
            return False

    def get_updates(self) -> Dict[str, Any]:
        """
        Get bot updates (useful for finding chat_id).

        Returns:
            Dictionary containing updates
        """
        if not self.settings.telegram_bot_token:
            return {"error": "Telegram bot token not configured"}

        try:
            url = f"{self.api_url}/getUpdates"
            response = httpx.get(url, timeout=10.0)
            response.raise_for_status()
            return response.json()

        except Exception as e:
            log.error(f"Failed to get Telegram updates: {e}")
            return {"error": str(e)}
