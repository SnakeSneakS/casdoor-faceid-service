from __future__ import annotations

from .api import app
from .config import Settings


def main() -> None:
    import os

    import uvicorn

    settings = Settings.from_env(os.environ)
    uvicorn.run(app, host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()
