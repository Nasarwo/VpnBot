from __future__ import annotations

from aiogram import Router

from app.bot import admin_handlers, user_handlers


def build_root_router() -> Router:
    root = Router(name="root")
    root.include_router(admin_handlers.router)
    root.include_router(user_handlers.router)
    return root
