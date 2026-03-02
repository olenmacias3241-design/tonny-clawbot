"""Notification models for email, Telegram, and WhatsApp."""

from pydantic import BaseModel, EmailStr
from typing import Optional, List, Union


class EmailRequest(BaseModel):
    """Email sending request model."""

    to: Union[str, List[str]]
    subject: str
    body: str
    html: bool = False
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None


class TelegramRequest(BaseModel):
    """Telegram message request model."""

    text: str
    chat_id: Optional[str] = None
    parse_mode: str = "Markdown"
    disable_notification: bool = False


class TelegramPhotoRequest(BaseModel):
    """Telegram photo request model."""

    photo_url: str
    caption: Optional[str] = None
    chat_id: Optional[str] = None


class WhatsAppRequest(BaseModel):
    """WhatsApp message request model."""

    to: str
    message: str
    media_url: Optional[str] = None
    use_business_api: bool = False


class WhatsAppTemplateRequest(BaseModel):
    """WhatsApp template message request model."""

    to: str
    template_name: str
    language_code: str = "en"
    parameters: Optional[List[str]] = None


class NotificationResponse(BaseModel):
    """Notification response model."""

    success: bool
    message: str
    error: Optional[str] = None


class GenerateTableRequest(BaseModel):
    """生成表格请求。"""
    prompt: str
    format: str = "csv"


class GeneratePptRequest(BaseModel):
    """生成 PPT 请求。"""
    title: str
    topic: str = ""
