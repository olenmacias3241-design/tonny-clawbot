"""Main entry point for Claw Bot AI."""

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
