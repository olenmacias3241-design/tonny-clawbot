"""AI provider interface and implementations."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from src.utils.config import get_settings
from src.utils.logger import log


class AIProvider(ABC):
    """Abstract AI provider interface."""

    @abstractmethod
    async def generate_response(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate a response from the AI model."""
        pass


class OpenAIProvider(AIProvider):
    """OpenAI provider implementation."""

    def __init__(self):
        settings = get_settings()
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key not configured")

        # Support OpenRouter and other OpenAI-compatible APIs
        client_kwargs = {"api_key": settings.openai_api_key}

        # Check if using OpenRouter (key starts with sk-or-)
        if settings.openai_api_key.startswith("sk-or-"):
            client_kwargs["base_url"] = "https://openrouter.ai/api/v1"
            self.using_openrouter = True
            log.info("Using OpenRouter API endpoint")
        # Check if using Groq (key starts with gsk_)
        elif settings.openai_api_key.startswith("gsk_"):
            client_kwargs["base_url"] = "https://api.groq.com/openai/v1"
            self.using_openrouter = False
            log.info("Using Groq API endpoint (FREE)")
        else:
            self.using_openrouter = False

        self.client = AsyncOpenAI(**client_kwargs)
        self.model = settings.openai_model
        log.info(f"OpenAI provider initialized with model: {self.model}")

    def _resolve_model(self, model: Optional[str]) -> str:
        """OpenRouter 需使用完整模型 ID（如 openai/gpt-4o-mini），此处做短名映射。"""
        use = model or self.model
        if not getattr(self, "using_openrouter", False):
            return use
        openrouter_ids = {
            "gpt-4o-mini": "openai/gpt-4o-mini",
            "gpt-3.5-turbo": "openai/gpt-3.5-turbo",
            "gpt-4o": "openai/gpt-4o",
            "gpt-4-turbo": "openai/gpt-4-turbo",
            "llama-3.1-8b-instant": "meta-llama/llama-3.1-8b-instant",
            "llama-3.1-70b-versatile": "meta-llama/llama-3.1-70b-versatile",
            "llama-3.3-70b-versatile": "meta-llama/llama-3.3-70b-instruct",
        }
        return openrouter_ids.get(use, use)

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        model: Optional[str] = None,
        **kwargs,
    ) -> str:
        """Generate a response using OpenAI."""
        try:
            use_model = self._resolve_model(model)
            response = await self.client.chat.completions.create(
                model=use_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )
            return response.choices[0].message.content
        except Exception as e:
            log.error(f"OpenAI API error: {e}")
            raise


class AnthropicProvider(AIProvider):
    """Anthropic Claude provider implementation."""

    def __init__(self):
        settings = get_settings()
        if not settings.anthropic_api_key:
            raise ValueError("Anthropic API key not configured")

        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.model = settings.anthropic_model
        log.info(f"Anthropic provider initialized with model: {self.model}")

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs,
    ) -> str:
        """Generate a response using Anthropic Claude."""
        try:
            # Separate system messages from user/assistant messages
            system_messages = [m["content"] for m in messages if m["role"] == "system"]
            conversation_messages = [m for m in messages if m["role"] != "system"]

            system_prompt = "\n".join(system_messages) if system_messages else None

            response = await self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=conversation_messages,
                **kwargs,
            )
            return response.content[0].text
        except Exception as e:
            log.error(f"Anthropic API error: {e}")
            raise


def get_ai_provider(provider_name: str = None) -> AIProvider:
    """Get an AI provider instance."""
    settings = get_settings()
    provider_name = provider_name or settings.default_ai_provider

    if provider_name == "openai":
        return OpenAIProvider()
    elif provider_name == "anthropic":
        return AnthropicProvider()
    else:
        raise ValueError(f"Unknown AI provider: {provider_name}")
