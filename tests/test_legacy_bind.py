from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import repositories
from app.db.enums import Protocol
from app.db.models import BindRequest, Server, ServerInbound, User
from app.db.repositories import BindRequestRepository
from app.services import bind_requests, provisioning
from app.services.panel_updater import MockPanelUpdater
from app.services.subscription_link import (
    parse_subscription_public_id,
    subscription_link_example,
)


@pytest.mark.parametrize(
    "link,expected",
    [
        ("https://host:2096/sub/AB12CD34", "AB12CD34"),
        ("https://host:2096/subscribe/legacy-id", "legacy-id"),
        ("https://host/sub/path/MYID99", "MYID99"),
        ("https://mind-forge.tech:49152/podpiso4kasub/dsh", "dsh"),
        ("MYID99", "MYID99"),
        ("dsh", "dsh"),
        ("", None),
        ("https://host/", None),
        ("not a url", None),
        ("ok", None),
        ("ab", None),
    ],
)
def test_parse_subscription_public_id(link: str, expected: str | None):
    assert parse_subscription_public_id(link) == expected


def test_subscription_link_example_is_abstract():
    assert subscription_link_example() == "https://example.com:2096/sub/ID"


async def test_create_bind_request(session: AsyncSession):
    user = User(
        telegram_id=555001,
        username="legacy",
        first_name="Legacy",
        onboarding_done=False,
    )
    session.add(user)
    await session.commit()

    await bind_requests.create_request(
        session,
        user,
        "https://panel.example:2096/sub/LEGACY42",
    )
    repo = BindRequestRepository(session)
    pending = await repo.latest_waiting_for_user(user.id)
    assert pending is not None
    assert pending.public_id == "LEGACY42"
    assert pending.request_code.startswith("BIND-")
    assert user.onboarding_done is False


async def test_create_bind_request_skips_duplicate_code(
    session: AsyncSession, monkeypatch
):
    existing_user = User(telegram_id=555010, onboarding_done=True)
    new_user = User(telegram_id=555011, onboarding_done=False)
    session.add_all([existing_user, new_user])
    await session.flush()
    session.add(
        BindRequest(
            user_id=existing_user.id,
            subscription_link="https://panel.example:2096/sub/OLDID",
            public_id="OLDID",
            request_code="BIND-DEADBEEF",
        )
    )
    await session.commit()

    tokens = iter(["deadbeef", "cafebabe"])
    monkeypatch.setattr(repositories.secrets, "token_hex", lambda n: next(tokens))

    req = await bind_requests.create_request(
        session, new_user, "https://panel.example:2096/sub/NEWID"
    )

    assert req.request_code == "BIND-CAFEBABE"


async def test_reject_bind_request_resets_onboarding(session: AsyncSession):
    user = User(telegram_id=555003, onboarding_done=False)
    session.add(user)
    await session.commit()

    req = await bind_requests.create_request(
        session, user, "https://panel.example:2096/sub/LEGACY42"
    )
    assert user.onboarding_done is False

    user.onboarding_done = True
    await session.commit()

    rejected = await bind_requests.reject_request(
        session, req.id, actor_user_id=None
    )
    await session.refresh(user)

    assert rejected.status.value == "rejected"
    assert user.onboarding_done is False
    repo = BindRequestRepository(session)
    assert await repo.latest_waiting_for_user(user.id) is None


async def test_create_bind_request_rejects_invalid_link(session: AsyncSession):
    user = User(telegram_id=555002, onboarding_done=False)
    session.add(user)
    await session.commit()

    with pytest.raises(bind_requests.BindRequestError):
        await bind_requests.create_request(session, user, "это не ссылка")

    assert user.onboarding_done is False
    repo = BindRequestRepository(session)
    assert await repo.latest_waiting_for_user(user.id) is None


async def test_create_bind_request_rejects_taken_public_id(session: AsyncSession):
    owner = User(telegram_id=1, public_id="TAKEN01", onboarding_done=True)
    applicant = User(telegram_id=2, onboarding_done=False)
    session.add_all([owner, applicant])
    await session.commit()

    with pytest.raises(bind_requests.BindRequestError):
        await bind_requests.create_request(
            session, applicant, "https://x/sub/TAKEN01"
        )


async def test_approve_bind_request_syncs_all_servers(
    session: AsyncSession, monkeypatch
):
    user = User(telegram_id=555100, onboarding_done=True)
    session.add(user)
    await session.commit()

    req = await bind_requests.create_request(
        session, user, "https://panel.example:2096/sub/LEGACY99"
    )

    ru = Server(
        name="ru",
        country="RU",
        panel_url="http://ru.local:2053",
        username="a",
        password="b",
        enabled=True,
    )
    de = Server(
        name="de",
        country="DE",
        panel_url="http://de.local:2053",
        username="a",
        password="b",
        enabled=True,
    )
    session.add_all([ru, de])
    await session.flush()
    for srv in (ru, de):
        session.add(
            ServerInbound(
                server_id=srv.id,
                inbound_id=1,
                protocol=Protocol.VLESS,
                enabled=True,
            )
        )
    await session.commit()

    presences = [
        provisioning.ServerClientPresence(
            server=ru,
            info=provisioning.PanelClientInfo(
                email="legacy99",
                sub_id="LEGACY99",
                secret="sec-99",
                expiry_ms=1_900_000_000_000,
                enable=True,
                inbound_ids=[1],
            ),
        ),
    ]

    async def fake_presence(sess, public_id, timeout=15.0):
        return presences

    monkeypatch.setattr(
        provisioning, "find_client_presence_on_servers", fake_presence
    )

    updater = MockPanelUpdater()
    result = await bind_requests.approve_request(
        session, req.id, actor_user_id=None, updater=updater
    )

    assert result.applied is True
    assert user.public_id == "LEGACY99"
    assert len(updater.provisioned) == 2
