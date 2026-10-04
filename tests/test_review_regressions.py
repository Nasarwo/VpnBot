from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.bot import notify, texts
from app.db.enums import PaymentStatus, Protocol
from app.db.models import PaymentRequest, PendingServerUpdate, ServerInbound
from app.services import pending_updates, provisioning
from app.services.panel_updater import MockPanelUpdater, PanelUpdateError
from app.services.xui_client import XuiClient, XuiError
from app.services.xui_updater import XuiPanelUpdater
from tests.test_admin_confirm import FakeBot
from tests.test_xui_updater import _server, _spec


class ReadOnlyPanel:
    def __init__(self, inbounds=None, error=None):
        self.inbounds = inbounds or []
        self.error = error

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        pass

    async def list_inbounds(self):
        if self.error:
            raise self.error
        return self.inbounds


async def test_import_reconciles_deleted_disabled_and_new_inbounds(session, server, monkeypatch):
    for iid, enabled in [(1, True), (2, False), (3, True), (22, True)]:
        session.add(ServerInbound(
            server_id=server.id, inbound_id=iid, protocol=Protocol.VLESS, enabled=enabled,
        ))
    await session.flush()
    panel = ReadOnlyPanel([
        {"id": 1, "protocol": "vless", "enable": True},
        {"id": 2, "protocol": "vless", "enable": True},
        {"id": 3, "protocol": "vless", "enable": False},
        {"id": 27, "protocol": "vless", "enable": True},
    ])
    monkeypatch.setattr(provisioning, "XuiClient", lambda **_: panel)
    summary = await provisioning.import_inbounds(session, server)
    rows = (await session.scalars(select(ServerInbound))).all()
    assert {r.inbound_id: r.enabled for r in rows} == {
        1: True, 2: False, 3: False, 22: False, 27: True,
    }
    assert (22, "vless", "disabled") in summary
    assert "22" in texts.admin_import_inbounds(server.id, summary)
    assert (27, "vless", "added") in summary


async def test_import_network_failure_preserves_targets(session, server, monkeypatch):
    configured = ServerInbound(
        server_id=server.id, inbound_id=22, protocol=Protocol.VLESS, enabled=True,
    )
    session.add(configured)
    await session.flush()
    monkeypatch.setattr(
        provisioning, "XuiClient", lambda **_: ReadOnlyPanel(error=XuiError("unreachable")),
    )
    with pytest.raises(PanelUpdateError):
        await provisioning.import_inbounds(session, server)
    assert configured.enabled is True


@pytest.mark.parametrize("single_server", [True, False])
async def test_provisioning_carries_telegram_identity(
    session, user, vpn_client, server, single_server,
):
    inbound = ServerInbound(
        server_id=server.id, inbound_id=1, protocol=Protocol.VLESS, enabled=True,
    )
    session.add(inbound)
    await session.flush()
    await session.refresh(server, ["inbounds"])

    class Capture(MockPanelUpdater):
        async def provision_server(self, server, spec, expiry_ms):
            assert spec.telegram_id == user.telegram_id
            await super().provision_server(server, spec, expiry_ms)

    updater = Capture()
    expiry = datetime.now(UTC) + timedelta(days=30)
    if single_server:
        result = await provisioning.apply_access_to_server(
            session, vpn_client, "PUB123", server, expiry, updater,
        )
        assert result.ok
    else:
        results = await provisioning.apply_access(session, vpn_client, "PUB123", expiry, updater)
        assert all(r.ok for r in results)
    assert len(updater.provisioned) == 1


async def test_pending_reconciles_memberships_and_never_shortens_newer_expiry(
    session, vpn_client, server,
):
    for iid in (1, 27):
        session.add(ServerInbound(
            server_id=server.id, inbound_id=iid, protocol=Protocol.VLESS, enabled=True,
        ))
    old = datetime.now(UTC) + timedelta(days=30)
    newer = old + timedelta(days=180)
    vpn_client.expires_at = newer
    update = PendingServerUpdate(
        vpn_client_id=vpn_client.id, server_id=server.id,
        target_expires_at=old, status="pending", attempts=0,
    )
    session.add(update)
    await session.flush()

    class Capture(MockPanelUpdater):
        async def provision_server(self, server, spec, expiry_ms):
            assert expiry_ms == int(newer.timestamp() * 1000)
            await super().provision_server(server, spec, expiry_ms)

    updater = Capture()
    result = await pending_updates.apply_pending_update(session, update, updater)
    assert result.ok
    assert update.status == "applied"
    assert updater.provisioned[0][2] == (1, 27)
    assert updater.calls == []


async def test_disabled_server_is_not_reenabled_by_pending_payment(session, vpn_client, server):
    server.enabled = False
    update = PendingServerUpdate(
        vpn_client_id=vpn_client.id, server_id=server.id,
        target_expires_at=datetime.now(UTC) + timedelta(days=30), status="pending", attempts=0,
    )
    session.add(update)
    await session.flush()
    updater = MockPanelUpdater()
    result = await pending_updates.apply_pending_update(session, update, updater)
    assert not result.ok
    assert update.status == "pending"
    assert updater.calls == updater.provisioned == []


async def test_stale_inbound_is_rejected_before_client_creation(monkeypatch):
    updater = XuiPanelUpdater()
    monkeypatch.setattr(updater, "_client", lambda _: ReadOnlyPanel([
        {"id": 10, "protocol": "vless", "enable": True},
    ]))
    with pytest.raises(PanelUpdateError, match="/importinbounds 1"):
        await updater.provision_server(_server(), _spec(), 123)


@pytest.mark.parametrize("obj", [None, {}, [{"protocol": "vless"}]])
async def test_malformed_inbounds_is_not_treated_as_empty_panel(httpx_mock, obj):
    httpx_mock.add_response(
        method="GET", url="http://panel.local/panel/api/inbounds/list",
        json={"success": True, "obj": obj},
    )
    async with XuiClient("http://panel.local", "admin", "secret") as client:
        client._logged_in = True
        with pytest.raises(XuiError, match="список inbound"):
            await client.list_inbounds()


async def test_deferred_payment_notification_does_not_claim_full_access(vpn_client, user):
    bot = FakeBot()
    await notify.notify_user_extended(bot, user.telegram_id, vpn_client, pending_servers=2)
    text = bot.messages[0]["text"]
    assert "Оплата учтена" in text
    assert "Доступ продлён" not in text
    assert "2" in text
    payment = PaymentRequest(
        payment_code="PAY-REVIEW", amount=850, period_days=180,
        status=PaymentStatus.APPLIED, last_error="Deferred servers",
    )
    assert "ожидается синхронизация" in texts.admin_payment_card(payment, user)


@pytest.mark.parametrize("status,body", [
    (500, {"success": False, "msg": "internal error"}),
    (200, {"success": False, "msg": "database unavailable"}),
    (200, []),
])
async def test_client_read_failure_is_not_misreported_as_missing(httpx_mock, status, body):
    httpx_mock.add_response(
        method="GET", url="http://panel.local/panel/api/clients/get/PUB123",
        status_code=status, json=body,
    )
    async with XuiClient("http://panel.local", "admin", "secret", max_retries=1) as client:
        client._logged_in = True
        with pytest.raises(XuiError):
            await client.get_client_record("PUB123")


async def test_capability_failure_does_not_fall_back_to_legacy_writes(httpx_mock):
    httpx_mock.add_response(
        method="GET", url="http://panel.local/panel/api/clients/get/__caps_probe__",
        status_code=503,
    )
    async with XuiClient("http://panel.local", "admin", "secret", max_retries=1) as client:
        client._logged_in = True
        with pytest.raises(XuiError, match="503"):
            await client.supports_clients_api()


async def test_provision_command_preserves_unlimited_subscription(
    session, user, vpn_client, monkeypatch,
):
    from types import SimpleNamespace
    from unittest.mock import AsyncMock

    from app.bot import admin_handlers
    from app.config import Settings

    apply = AsyncMock(return_value=[])
    monkeypatch.setattr(admin_handlers.provisioning, "apply_access", apply)
    message = SimpleNamespace(answer=AsyncMock())
    command = SimpleNamespace(args=str(user.telegram_id))
    await admin_handlers.provision_user(message, command, session, Settings())
    assert apply.await_args.args[3] is None


async def test_provision_command_does_not_create_unpaid_unlimited_client(
    session, user, monkeypatch,
):
    from types import SimpleNamespace
    from unittest.mock import AsyncMock

    from app.bot import admin_handlers
    from app.config import Settings

    apply = AsyncMock()
    monkeypatch.setattr(admin_handlers.provisioning, "apply_access", apply)
    await admin_handlers.provision_user(
        SimpleNamespace(answer=AsyncMock()),
        SimpleNamespace(args=str(user.telegram_id)), session, Settings(),
    )
    apply.assert_not_called()


async def test_failed_binding_does_not_commit_partial_account_reassignment(
    session, user, monkeypatch,
):
    from app.services import bind_requests

    original = user.public_id
    request = await bind_requests.create_request(session, user, "https://example.test/sub/LEGACY")

    async def partially_bind(session, user, public_id, updater):
        user.public_id = public_id
        await session.flush()
        raise PanelUpdateError("one panel failed")

    monkeypatch.setattr(provisioning, "bind_user_by_public_id", partially_bind)
    result = await bind_requests.approve_request(session, request.id, None, MockPanelUpdater())
    assert not result.applied
    await session.refresh(user)
    assert user.public_id == original


async def test_disabled_inbounds_are_not_bypassed_by_mapping_retry(session, vpn_client, server):
    session.add(ServerInbound(
        server_id=server.id, inbound_id=1, protocol=Protocol.VLESS, enabled=False,
    ))
    update = PendingServerUpdate(
        vpn_client_id=vpn_client.id, server_id=server.id,
        target_expires_at=datetime.now(UTC) + timedelta(days=30), status="pending", attempts=0,
    )
    session.add(update)
    await session.flush()
    updater = MockPanelUpdater()
    result = await pending_updates.apply_pending_update(session, update, updater)
    assert not result.ok
    assert result.error == "no_enabled_inbounds"
    assert updater.calls == updater.provisioned == []


async def test_server_without_targets_is_reported_as_failed(session, user, server):
    vpn_client = await provisioning.ensure_vpn_client(session, user)
    updater = MockPanelUpdater()
    results = await provisioning.apply_access(
        session, vpn_client, "PUB123", datetime.now(UTC) + timedelta(days=30), updater,
    )
    assert len(results) == 1
    assert results[0].server_id == server.id
    assert not results[0].ok


async def test_failed_queue_items_back_off_until_next_retry(session, vpn_client, server):
    from app.db.repositories import PendingServerUpdateRepository

    update = PendingServerUpdate(
        vpn_client_id=vpn_client.id, server_id=server.id,
        target_expires_at=datetime.now(UTC) + timedelta(days=30), status="pending", attempts=0,
    )
    session.add(update)
    await session.flush()
    updater = MockPanelUpdater(fail_server_ids={server.id})
    result = await pending_updates.apply_pending_update(session, update, updater)
    assert not result.ok
    assert update.attempts == 1
    assert update.next_retry_at > datetime.now(UTC)
    assert await PendingServerUpdateRepository(session).list_pending_for_server(server.id) == []


async def test_confirmation_resumes_saved_target_after_process_interruption(
    session, user, vpn_client,
):
    from app.services import billing, payments

    payment = await payments.create_request(session, user.id, 850, 180)

    class Interrupted(MockPanelUpdater):
        async def update_expiry(self, *_args):
            raise RuntimeError("process interrupted after durable target commit")

    with pytest.raises(RuntimeError):
        await billing.confirm_payment(session, payment.id, user.id, Interrupted())
    await session.rollback()
    await session.refresh(payment)
    assert payment.status == PaymentStatus.CONFIRMED
    saved = payment.target_expires_at
    result = await billing.retry_payment(
        session, payment.id, None, MockPanelUpdater(), now=datetime.now(UTC) + timedelta(days=2),
    )
    assert result.applied
    assert result.new_expires_at.replace(tzinfo=UTC) == saved.replace(tzinfo=UTC)
    assert payment.status == PaymentStatus.APPLIED


async def test_failed_expiry_notice_is_retried(session, vpn_client, monkeypatch):
    from unittest.mock import AsyncMock

    from app.services import expiry

    vpn_client.expires_at = datetime.now(UTC) + timedelta(hours=12)
    await session.commit()
    send = AsyncMock(side_effect=[False, True])
    monkeypatch.setattr(expiry.notify, "notify_user_expiry", send)
    assert await expiry.process_expiry_notifications(session, FakeBot()) == 0
    assert vpn_client.expiry_notify_stage == 0
    assert await expiry.process_expiry_notifications(session, FakeBot()) == 1
    assert vpn_client.expiry_notify_stage == 1


async def test_expiry_after_downtime_sends_only_current_notice(session, vpn_client, monkeypatch):
    from unittest.mock import AsyncMock

    from app.services import expiry

    vpn_client.expires_at = datetime.now(UTC) - timedelta(days=2)
    await session.commit()
    send = AsyncMock(return_value=True)
    monkeypatch.setattr(expiry.notify, "notify_user_expiry", send)
    assert await expiry.process_expiry_notifications(session, FakeBot()) == 1
    assert send.await_args.args[2] == 3
    assert vpn_client.expiry_notify_stage == 3


async def test_user_operations_serialize_and_release_on_failure(session, user):
    import asyncio

    from app.services.operation_lock import user_operation

    events = []
    entered = asyncio.Event()
    release = asyncio.Event()

    async def first():
        with pytest.raises(RuntimeError):
            async with user_operation(session, user.id):
                events.append("first")
                entered.set()
                await release.wait()
                raise RuntimeError("interrupted")

    async def second():
        await entered.wait()
        async with user_operation(session, user.id):
            events.append("second")

    tasks = [asyncio.create_task(first()), asyncio.create_task(second())]
    await entered.wait()
    await asyncio.sleep(0)
    assert events == ["first"]
    release.set()
    await asyncio.gather(*tasks)
    assert events == ["first", "second"]


async def test_new_payment_includes_interrupted_reserved_period(session, user, vpn_client):
    from app.services import billing, payments

    original = datetime.now(UTC) + timedelta(days=10)
    vpn_client.expires_at = original
    interrupted = await payments.create_request(session, user.id, 850, 180)
    interrupted.status = PaymentStatus.CONFIRMED
    interrupted.target_expires_at = original + timedelta(days=180)
    interrupted.confirmed_at = datetime.now(UTC) - timedelta(minutes=10)
    await session.commit()
    new = await payments.create_request(session, user.id, 850, 180)
    result = await billing.confirm_payment(session, new.id, None, MockPanelUpdater())
    expected = original + timedelta(days=360)
    assert result.new_expires_at == expected
    await billing.recover_confirmed_payments(session, MockPanelUpdater())
    assert vpn_client.expires_at.replace(tzinfo=UTC) == expected
    assert interrupted.status == PaymentStatus.APPLIED


def test_panel_update_preserves_additional_client_policy_fields():
    from app.services.xui_payloads import merge_client_record_for_update

    fields = {"group": "staff", "comment": "keep", "limitHwid": 2,
              "resetDay": 5, "resetWeekday": 0, "resetMax": 4,
              "security": "auto", "reverse": {"tag": "reverse"}}
    original = {"id": 9, "uuid": "client-uuid", "email": "PUB", **fields}
    merged = merge_client_record_for_update(original, email="PUB", sub_id="PUB", expiry_ms=123)
    assert all(merged[key] == value for key, value in fields.items())
    assert merged["id"] == "client-uuid"


async def test_attach_success_without_membership_is_not_provisioning_success():
    from app.services.xui_client import XuiError
    from app.services.xui_updater import XuiPanelUpdater

    class Panel:
        async def get_client_record(self, _email):
            return {"client": {"email": "PUB123", "id": "uuid-1"}, "inboundIds": [10]}

        async def update_client_record(self, *_args, **_kwargs):
            pass

        async def attach_client_record(self, *_args):
            pass

    with pytest.raises(XuiError, match="inbound-привязки"):
        await XuiPanelUpdater()._provision_new(Panel(), _spec(), [10, 11], None, 123)


@pytest.mark.parametrize("stored,expected", [
    ("", []), ("10.0.0.1/32,10.0.0.2/32", ["10.0.0.1/32", "10.0.0.2/32"]),
    ('["10.0.0.1/32"]', ["10.0.0.1/32"]),
])
def test_stored_tunnel_ips_are_normalized_for_client_api(stored, expected):
    from app.services.xui_payloads import sanitize_client_for_api

    assert sanitize_client_for_api({"allowedIPs": stored})["allowedIPs"] == expected


def test_stored_reverse_is_normalized_for_client_api():
    from app.services.xui_payloads import sanitize_client_for_api

    assert sanitize_client_for_api({"reverse": '{"tag":"reverse"}'})["reverse"] == {
        "tag": "reverse",
    }
