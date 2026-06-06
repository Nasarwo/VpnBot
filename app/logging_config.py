from __future__ import annotations

import logging

_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"


def setup_logging(level: str = "INFO", xui_debug: bool = False) -> None:
    """Настраивает логирование приложения.

    - корневой логгер: WARNING (чтобы сторонние библиотеки не шумели);
    - логи приложения (app.*): заданный уровень;
    - aiogram: INFO;
    - httpx/httpcore: WARNING, либо DEBUG если включён xui_debug.
    """
    resolved = getattr(logging, level.upper(), logging.INFO)

    root = logging.getLogger()
    root.setLevel(logging.WARNING)

    if not root.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(_FORMAT))
        root.addHandler(handler)
    else:
        for handler in root.handlers:
            handler.setFormatter(logging.Formatter(_FORMAT))

    logging.getLogger("app").setLevel(resolved)
    logging.getLogger("__main__").setLevel(resolved)
    logging.getLogger("aiogram").setLevel(logging.INFO)

    http_level = logging.DEBUG if xui_debug else logging.WARNING
    logging.getLogger("httpx").setLevel(http_level)
    logging.getLogger("httpcore").setLevel(http_level)
