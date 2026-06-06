from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class ProofStates(StatesGroup):
    waiting_proof = State()
