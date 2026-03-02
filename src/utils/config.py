"""Configuration management for Claw Bot AI."""

from pydantic_settings import BaseSettings
from typing import Optional, List, Tuple
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings."""

    # Application
    app_name: str = "Claw Bot AI"
    app_version: str = "0.1.0"
    debug: bool = False

    # API Server
    host: str = "0.0.0.0"
    port: int = 8000

    # AI Provider Settings
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-3-opus-20240229"

    # Default AI Provider: "openai" or "anthropic"
    default_ai_provider: str = "openai"

    # Database
    database_url: str = "sqlite:///./claw_bot.db"

    # Redis
    redis_url: Optional[str] = None

    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/claw_bot.log"

    # Bot Settings
    max_context_messages: int = 10
    response_timeout: int = 30

    # Email Settings
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    email_from: Optional[str] = None

    # Telegram Settings
    telegram_bot_token: Optional[str] = None
    telegram_default_chat_id: Optional[str] = None

    # WhatsApp Settings (Twilio)
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    whatsapp_from: Optional[str] = None  # Format: whatsapp:+1234567890

    # WhatsApp Business API (alternative to Twilio)
    whatsapp_business_token: Optional[str] = None
    whatsapp_phone_id: Optional[str] = None

    # GitHub Integration
    github_token: Optional[str] = None
    github_default_owner: Optional[str] = None
    github_default_repo: Optional[str] = None
    # 多仓库：逗号分隔 "owner1/repo1,owner2/repo2"，优先于 default_owner/repo
    github_repos: Optional[str] = None

    # 聊天操控电脑（传统龙虾能力）：是否允许通过聊天执行白名单内命令
    enable_computer_control: bool = False
    # 允许的命令（逗号分隔），例如: ls,pwd,date,whoami,open
    allowed_commands: str = "ls,pwd,date,whoami"

    def get_github_repos(self) -> List[Tuple[str, str]]:
        """返回要同步的 (owner, repo) 列表。"""
        if self.github_repos:
            result = []
            for part in self.github_repos.strip().split(","):
                part = part.strip()
                if "/" in part:
                    owner, repo = part.split("/", 1)
                    result.append((owner.strip(), repo.strip()))
            if result:
                return result
        if self.github_default_owner and self.github_default_repo:
            return [(self.github_default_owner, self.github_default_repo)]
        return []

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
