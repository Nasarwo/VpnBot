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
    # Удаление подписки: админ присылает внутренний ID клиента 3x-ui/subId.
    waiting_delete_subscription_client_id = State()
