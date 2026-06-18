from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class ProofStates(StatesGroup):
    waiting_proof = State()


class OnboardingStates(StatesGroup):
    waiting_legacy_link = State()


class AdminStates(StatesGroup):
    # Мастер добавления сервера: админ присылает одну строку с полями через «|».
    waiting_server_line = State()
    # Рассылка: админ присылает текст сообщения для всех пользователей.
    waiting_broadcast = State()
    # Удаление подписки: админ присылает Telegram ID пользователя.
    waiting_delete_subscription_tg_id = State()
