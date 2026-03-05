"""Main entry point for Claw Bot AI."""

import os
from pathlib import Path

# 尽早加载 .env，使 SADTALKER_PYTHON 等进入 os.environ
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent / ".env"
    if env_path.is_file():
        load_dotenv(env_path)
except ImportError:
    pass

import uvicorn
from src.utils.config import get_settings


def main():
    """Run the Claw Bot API server."""
    settings = get_settings()

    uvicorn.run(
        "src.handlers.api:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
