"""Фоновая сверка расхода whitelist-услуги: полный обход аккаунтов пачками."""
from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
import pytest_asyncio
from sqlalchemy import func, select

from app import main as app_main
from app.bot import texts
from app.db.enums import Protocol, UserRole
from app.db.models import Server, ServerInbound, User, WhitelistAccount, WhitelistLedger
from app.services import whitelist
from app.services.panel_updater import MockPanelUpdater, PanelUpdateError, QuotaClientState
from tests.test_whitelist import EMAIL, _account, _buy, _pay

GIB = whitelist.GIB
START_FREE = 10 * GIB


@pytest_asyncio.fixture
async def wl_server(session) -> Server:
    srv = Server(
        name="Обход белых списков",
        panel_url="https://wl.example:2053",
        username="admin",
        password="secret",
        purpose="whitelist",
        enabled=True,
        inventory_status="ready",
    )
    session.add(srv)
    await session.flush()
    session.add(
        ServerInbound(
            server_id=srv.id, inbound_id=7, protocol=Protocol.VLESS, enabled=True,
            remark="Обход белых списков",
        )
    )
    await session.commit()
    return srv


class RecordingPanel(MockPanelUpdater):
    """Панель с журналом пакетных чтений и точками вмешательства в обход."""

    def __init__(self) -> None:
        super().__init__()
        self.batches: list[list[str]] = []
        self.errors: set[str] = set()
        self.unavailable_from_batch: int | None = None
        self.after_read = None  # async (batch_index, emails) -> None

    async def read_quota_clients(self, server, emails):
        index = len(self.batches)
        self.batches.append(list(emails))
        if self.unavailable_from_batch is not None and index >= self.unavailable_from_batch:
            raise PanelUpdateError("panel unavailable")
        result = {}
        for email in emails:
            if email in self.errors:
                result[email] = PanelUpdateError(f"read failed for {email}")
                continue
            state = self.quota_clients.get((server.id, email))
            result[email] = None if state is None else QuotaClientState(
                email=state.email, enable=state.enable, total_bytes=state.total_bytes,
                expiry_ms=state.expiry_ms, inbound_ids=list(state.inbound_ids),
                used_bytes=state.used_bytes, traffic_row_id=state.traffic_row_id,
                last_online_ms=state.last_online_ms,
            )
        if self.after_read is not None:
            await self.after_read(index, emails)
        return result

    @property
    def read_emails(self) -> list[str]:
        return [email for batch in self.batches for email in batch]


@pytest.fixture
def panel() -> RecordingPanel:
    return RecordingPanel()


def _email(index: int) -> str:
    return f"wl{index:04d}@local"


async def _add_account(
    session, server, panel, index: int, *, on_panel: bool = True, used: int = 0
) -> WhitelistAccount:
    user = User(
        telegram_id=10_000 + index, username=f"u{index}", first_name=f"U{index}",
        role=UserRole.USER, onboarding_done=True,
    )
    session.add(user)
    await session.flush()
    email = _email(index)
    account = WhitelistAccount(
        user_id=user.id, server_id=server.id, panel_email=email,
        free_bytes=START_FREE, paid_bytes=0, usage_checkpoint_bytes=0,
        traffic_row_id=500 + index, last_synced_at=None,
        desired_version=1, applied_version=1,
    )
    session.add(account)
    await session.flush()
    if on_panel:
        panel.quota_clients[(server.id, email)] = QuotaClientState(
            email, True, START_FREE, 0, [7], used_bytes=used, traffic_row_id=500 + index
        )
    return account


async def _populate(session, server, panel, count: int, *, first: int = 0, **kwargs):
    ids = [
        (await _add_account(session, server, panel, first + i, **kwargs)).id
        for i in range(count)
    ]
    await session.commit()
    return ids


async def _free(session, account_id: int) -> int:
    session.expire_all()
    return (await session.get(WhitelistAccount, account_id)).free_bytes


async def _reconciled(session, account_ids) -> list[bool]:
    return [await _free(session, i) == START_FREE - GIB for i in account_ids]


# --- Дефект: обработка ограничена одной пачкой ------------------------------------


async def test_more_than_one_batch_is_reconciled_in_one_pass(
    session, wl_server, panel
):
    accounts = await _populate(session, wl_server, panel, 250, used=GIB)
    await whitelist.reconcile_usage(session, panel)
    assert all(await _reconciled(session, accounts))


async def test_unreadable_head_does_not_starve_the_tail(session, wl_server, panel):
    """Аккаунты без клиента на панели не обновляют метку и не должны занимать пачку."""
    await _populate(session, wl_server, panel, 120, on_panel=False)
    healthy = await _populate(session, wl_server, panel, 30, first=1000, used=GIB)
    await whitelist.reconcile_usage(session, panel, limit=100)
    assert all(await _reconciled(session, healthy))
    assert len(panel.read_emails) == len(set(panel.read_emails)) == 150


class _Sleeps:
    def __init__(self) -> None:
        self.calls: list[float] = []

    async def __call__(self, seconds: float) -> None:
        self.calls.append(seconds)


async def _cycle(session, panel, **kwargs):
    kwargs.setdefault("batch_size", 100)
    kwargs.setdefault("status", whitelist.ReconcileStatus())
    return await whitelist.reconcile_cycle(session, panel, **kwargs)


# --- Ограниченные пачки, стабильная пагинация, пауза -------------------------------


async def test_batches_are_bounded_ordered_and_paused(session, wl_server, panel):
    await _populate(session, wl_server, panel, 250, used=GIB)
    sleeps = _Sleeps()
    report = await _cycle(session, panel, pause_seconds=0.5, sleep=sleeps)
    assert [len(batch) for batch in panel.batches] == [100, 100, 50]
    assert panel.read_emails == [_email(i) for i in range(250)]  # без повторов и пропусков
    assert sleeps.calls == [0.5, 0.5]  # между пачками, но не после последней
    assert report.complete and report.batches == 3
    assert (report.reconciled, report.skipped, report.errors) == (250, 0, 0)
    assert report.accounts == 250


async def test_accounts_without_panel_client_are_skipped_not_repeated(
    session, wl_server, panel
):
    await _populate(session, wl_server, panel, 120, on_panel=False)
    await _populate(session, wl_server, panel, 10, first=500, used=GIB)
    status = whitelist.ReconcileStatus()
    report = await _cycle(session, panel, status=status)
    assert (report.reconciled, report.skipped_no_client, report.errors) == (10, 120, 0)
    # Учёты без клиента на панели не сверены: подтверждённой свежести нет.
    assert status.last_complete_at is not None and status.last_success_at is None
    text = "\n".join(texts.reconcile_status_lines(status))
    assert "нет клиента на панели 120" in text and "все учёты сверены" not in text
    assert report.accounts == 130 and len(set(panel.read_emails)) == 130


async def test_empty_service_completes_without_reading_panel(session, wl_server, panel):
    report = await _cycle(session, panel)
    assert report.complete and report.accounts == 0 and panel.batches == []


async def test_server_not_ready_is_reported_without_reading(session, wl_server, panel):
    wl_server.inventory_status = "error"
    await session.commit()
    status = whitelist.ReconcileStatus()
    report = await _cycle(session, panel, status=status)
    assert report.aborted == "server_not_ready" and not report.complete
    assert panel.batches == [] and status.last_success_at is None


# --- Частичные ошибки -------------------------------------------------------------


async def test_read_errors_of_some_accounts_do_not_stop_the_rest(session, wl_server, panel):
    ids = await _populate(session, wl_server, panel, 230, used=GIB)
    broken = {_email(i) for i in (3, 150, 229)}
    panel.errors = broken
    status = whitelist.ReconcileStatus()
    report = await _cycle(session, panel, status=status)
    assert report.complete and report.errors == 3 and report.reconciled == 227
    reconciled = await _reconciled(session, ids)
    assert [i for i, ok in enumerate(reconciled) if not ok] == [3, 150, 229]
    # Обход дошёл до конца, но «чистым» не считается.
    assert status.last_complete_at is not None and status.last_success_at is None


async def test_exception_while_reconciling_one_account_does_not_stop_others(
    session, wl_server, panel, monkeypatch
):
    ids = await _populate(session, wl_server, panel, 120, used=GIB)
    bad_user = (await session.get(WhitelistAccount, ids[7])).user_id
    original = whitelist._reconcile_one

    async def flaky(session, user_id, *args, **kwargs):
        if user_id == bad_user:
            raise RuntimeError("boom")
        return await original(session, user_id, *args, **kwargs)

    monkeypatch.setattr(whitelist, "_reconcile_one", flaky)
    report = await _cycle(session, panel)
    assert report.complete and report.errors == 1 and report.reconciled == 119
    assert [i for i, ok in enumerate(await _reconciled(session, ids)) if not ok] == [7]


# --- Недоступная панель ------------------------------------------------------------


async def test_unavailable_panel_aborts_and_resumes_from_cursor_not_first_batch(
    session, wl_server, panel
):
    ids = await _populate(session, wl_server, panel, 450, used=GIB)
    panel.unavailable_from_batch = 1
    status = whitelist.ReconcileStatus()
    first = await _cycle(session, panel, status=status)
    assert first.aborted == "panel_unavailable" and not first.complete
    assert len(panel.batches) == 3  # одна успешная и две подряд неудачные — не больше
    assert first.reconciled == 100 and first.errors == 0 and first.remaining == 350
    assert status.last_complete_at is None and status.runs_aborted == 1

    panel.batches.clear()
    panel.unavailable_from_batch = None
    second = await _cycle(session, panel, status=status)
    assert second is first and second.complete and second.runs == 2
    # Первая пачка не читается повторно: обход продолжился с курсора.
    assert panel.read_emails == [_email(i) for i in range(100, 450)]
    assert all(await _reconciled(session, ids))
    assert (second.reconciled, second.errors) == (450, 0)
    assert status.last_success_at is not None and status.current is None


async def test_panel_down_for_whole_traversal_never_marks_success(session, wl_server, panel):
    await _populate(session, wl_server, panel, 300, used=GIB)
    panel.unavailable_from_batch = 0
    status = whitelist.ReconcileStatus()
    for _ in range(whitelist.RECONCILE_MAX_STALLED_RUNS):
        report = await _cycle(session, panel, status=status)
        assert report.aborted == "panel_unavailable" and report.cursor == 0
    assert status.last_success_at is None and status.last_complete_at is None
    assert status.runs_aborted == whitelist.RECONCILE_MAX_STALLED_RUNS


async def test_stalled_region_is_passed_instead_of_repeating_forever(
    session, wl_server, panel
):
    await _populate(session, wl_server, panel, 250, used=GIB)
    panel.unavailable_from_batch = 0
    status = whitelist.ReconcileStatus()
    for _ in range(whitelist.RECONCILE_MAX_STALLED_RUNS):
        assert (await _cycle(session, panel, status=status)).aborted
    final = await _cycle(session, panel, status=status)
    # Обход не застрял на первой пачке: область засчитана ошибками и пройдена.
    assert final.complete and final.errors == 250 and final.reconciled == 0
    assert status.last_success_at is None and status.last_complete_at is not None


async def test_recovered_panel_after_transient_batch_failure_continues(
    session, wl_server, panel
):
    ids = await _populate(session, wl_server, panel, 300, used=GIB)
    calls = {"n": 0}
    original = panel.read_quota_clients

    async def one_bad_batch(server, emails):
        calls["n"] += 1
        if calls["n"] == 2:
            raise PanelUpdateError("blip")
        return await original(server, emails)

    panel.read_quota_clients = one_bad_batch
    report = await _cycle(session, panel)
    # Одна неудачная пачка не прерывает обход; её учёты — ошибки этого обхода.
    assert report.complete and report.errors == 100 and report.reconciled == 200
    reconciled = await _reconciled(session, ids)
    assert not any(reconciled[100:200]) and all(reconciled[:100] + reconciled[200:])


# --- Изменение списка во время обхода ---------------------------------------------


async def test_list_changes_during_traversal(session, wl_server, panel):
    ids = await _populate(session, wl_server, panel, 300, used=GIB)
    added: list[int] = []

    async def mutate(index, emails):
        if index != 0:
            return
        # Удалены: уже прочитанный (в этой пачке) и ещё не посещённый учёт.
        await session.delete(await session.get(WhitelistAccount, ids[5]))
        await session.delete(await session.get(WhitelistAccount, ids[250]))
        added.extend(await _populate(session, wl_server, panel, 20, first=900, used=GIB))

    panel.after_read = mutate
    report = await _cycle(session, panel)
    assert report.complete and report.errors == 0
    assert report.skipped_gone == 1  # удалён после чтения пачки
    assert report.reconciled == 300 - 2 + 20  # 300 минус оба удалённых, плюс добавленные
    emails = panel.read_emails
    assert len(emails) == len(set(emails))  # никто не читался дважды
    assert _email(250) not in emails
    assert all(_email(900 + i) in emails for i in range(20))
    assert all(await _reconciled(session, [i for i in ids if i not in (ids[5], ids[250])]))
    assert all(await _reconciled(session, added))


async def test_server_replaced_during_traversal_aborts_instead_of_mixing_servers(
    session, wl_server, panel
):
    await _populate(session, wl_server, panel, 250, used=GIB)

    async def replace_server(index, emails):
        if index != 0:
            return
        wl_server.enabled = False
        new = Server(
            name="wl-2", panel_url="https://wl2.example:2053", username="a", password="b",
            purpose="whitelist", enabled=True, inventory_status="ready",
        )
        session.add(new)
        await session.flush()
        session.add(ServerInbound(server_id=new.id, inbound_id=7, protocol=Protocol.VLESS,
                                  enabled=True))
        await session.commit()

    panel.after_read = replace_server
    status = whitelist.ReconcileStatus()
    report = await _cycle(session, panel, status=status)
    assert report.aborted == "server_changed" and not report.complete
    assert status.current is None and len(panel.batches) == 1


# --- Конкурентные продление и покупка ---------------------------------------------


@pytest_asyncio.fixture
async def service_on(session, wl_server):
    config = await whitelist.get_config(session)
    config.service_enabled = True
    await whitelist.ensure_defaults(session)
    return config


@pytest.mark.parametrize("operation", ["purchase", "renewal"])
async def test_purchase_or_renewal_during_batch_read_is_not_overwritten_by_stale_reading(
    session, user, vpn_client, service_on, wl_server, panel, operation
):
    await _pay(session, user, panel)
    panel.consume(wl_server.id, EMAIL, 2 * GIB)
    await _populate(session, wl_server, panel, 150, first=700, used=GIB)
    done = False

    async def concurrent_operation(index, emails):
        nonlocal done
        if index != 0 or done:
            return
        done = True
        panel.consume(wl_server.id, EMAIL, GIB)  # расход после чтения пачки
        if operation == "purchase":
            await _buy(session, user, panel, 25)
        else:
            await _pay(session, user, panel, days=30, amount=175)

    panel.after_read = concurrent_operation
    report = await _cycle(session, panel)
    assert done and report.complete and report.errors == 0
    assert report.retried_busy >= 1 and report.skipped_busy == 0
    account = await _account(session, user)
    expected = (7, 25) if operation == "purchase" else (10, 0)
    assert (account.free_bytes // GIB, account.paid_bytes // GIB) == expected
    assert account.usage_checkpoint_bytes == 3 * GIB  # устаревшее чтение (2 ГБ) не применено
    assert account.conflict is None
    rebases = await session.scalar(
        select(func.count(WhitelistLedger.id)).where(WhitelistLedger.kind == "usage_rebase")
    )
    assert rebases == 0
    assert await whitelist.list_open_events(session, user.id) == []


async def test_account_that_stays_busy_is_reported_as_skipped(
    session, wl_server, panel, monkeypatch
):
    ids = await _populate(session, wl_server, panel, 5, used=GIB)
    original = whitelist._reconcile_one
    busy_user = (await session.get(WhitelistAccount, ids[2])).user_id

    async def always_busy(session, user_id, *args, **kwargs):
        if user_id == busy_user:
            return whitelist.ReconcileOutcome.BUSY
        return await original(session, user_id, *args, **kwargs)

    monkeypatch.setattr(whitelist, "_reconcile_one", always_busy)
    status = whitelist.ReconcileStatus()
    report = await _cycle(session, panel, status=status)
    assert report.complete and report.skipped_busy == 1 and report.reconciled == 4
    assert report.errors == 0 and report.accounts == 5  # без двойного учёта
    assert panel.read_emails.count(_email(2)) == 2  # один повтор, не бесконечный
    # Обход завершён, но один учёт не сверен: свежесть всех данных не подтверждена.
    assert status.last_complete_at is not None and status.last_success_at is None
    text = "\n".join(texts.reconcile_status_lines(status))
    assert "все учёты сверены" not in text and "изменились во время обхода 1" in text


# --- Наблюдаемость ----------------------------------------------------------------


async def test_status_tracks_last_success_and_staleness(session, wl_server, panel, caplog):
    await _populate(session, wl_server, panel, 30, used=GIB)
    status = whitelist.ReconcileStatus()
    now = datetime.now(UTC)
    assert status.success_age(now) is None and status.worst_case_staleness(now) is None
    with caplog.at_level("INFO", logger="app.services.whitelist"):
        report = await _cycle(session, panel, status=status)
    assert status.last_report is report and status.traversals_completed == 1
    assert status.last_success_at == report.finished_at
    assert status.last_success_started_at == report.started_at <= report.finished_at
    later = report.finished_at + timedelta(minutes=10)
    assert status.success_age(later) == timedelta(minutes=10)
    assert status.worst_case_staleness(later) >= status.success_age(later)
    assert report.active_seconds >= 0
    assert any("сверка расхода завершена" in r.message and "сверено 30" in r.message
               for r in caplog.records)


async def test_admin_summary_exposes_reconcile_status(session, wl_server, service_on):
    summary = await whitelist.admin_summary(session)
    assert summary.reconcile is whitelist.RECONCILE_STATUS


def _text_report(now, **counts):
    report = whitelist.ReconcileReport(
        server_id=1, started_at=now - timedelta(minutes=30),
        finished_at=now - timedelta(minutes=29), batches=1,
    )
    for name, value in counts.items():
        setattr(report, name, value)
    return report


def test_reconcile_text_describes_age_and_abort():
    now = datetime.now(UTC)
    status = whitelist.ReconcileStatus()
    assert "ещё не завершён" in texts.reconcile_status_lines(status, now)[0]
    report = _text_report(now, reconciled=90)
    status.last_report = report
    status.last_complete_at = status.last_success_at = report.finished_at
    status.last_complete_started_at = status.last_success_started_at = report.started_at
    status.current = whitelist.ReconcileReport(
        server_id=1, started_at=now, aborted="panel_unavailable", remaining=40
    )
    lines = "\n".join(texts.reconcile_status_lines(status, now))
    assert "29 мин назад, все учёты сверены" in lines and "не старше 30 мин" in lines
    assert "сверено 90" in lines and "ошибок 0" in lines
    assert "прерван (panel_unavailable), впереди учётов: 40" in lines


def test_reconcile_text_does_not_promise_freshness_for_unconfirmed_accounts():
    now = datetime.now(UTC)
    status = whitelist.ReconcileStatus()
    report = _text_report(now, reconciled=90, errors=2, skipped_busy=3, skipped_no_client=4)
    status.last_report = report
    status.last_complete_at = report.finished_at
    status.last_complete_started_at = report.started_at
    lines = texts.reconcile_status_lines(status, now)
    head = lines[0]
    assert "не сверено учётов: 9" in head
    assert "ошибок 2" in head and "изменились во время обхода 3" in head
    assert "нет клиента на панели 4" in head
    assert "все учёты сверены" not in head and "данные учёта не старше" not in "\n".join(lines)
    assert "их данные могут быть старше" in head.lower() and "сверенные не старше 30 мин" in head
    assert "полностью подтверждённого обхода с запуска бота ещё не было" in lines[1]


def test_reconcile_text_keeps_old_confirmed_traversal_next_to_newer_gaps():
    now = datetime.now(UTC)
    status = whitelist.ReconcileStatus()
    status.last_success_at = now - timedelta(minutes=60)
    status.last_success_started_at = now - timedelta(minutes=65)
    report = _text_report(now, reconciled=98, errors=2)
    status.last_report = report
    status.last_complete_at = report.finished_at
    status.last_complete_started_at = report.started_at
    lines = "\n".join(texts.reconcile_status_lines(status, now))
    assert "последний обход завершён 29 мин назад, но не сверено учётов: 2" in lines
    assert "последний полностью подтверждённый обход завершён 60 мин назад" in lines
    assert "данные учёта не старше 65 мин" in lines


def test_next_delay_is_a_pause_not_a_deadline():
    delay = whitelist.next_reconcile_delay
    assert delay(900, 100, complete=True) == 800
    # Обход, занявший дольше периода, не запускается сразу же заново.
    assert delay(900, 5000, complete=True) == whitelist.RECONCILE_MIN_IDLE_SECONDS
    assert delay(900, 5, complete=False) == whitelist.RECONCILE_RETRY_SECONDS
    assert delay(30, 5, complete=False) == 30 and delay(30, 100, complete=True) == 30


# --- Подключение в main -----------------------------------------------------------


async def test_poller_uses_settings_global_status_and_adaptive_delay(monkeypatch):
    seen: dict = {}
    delays: list[float] = []

    class Maker:
        def __call__(self):
            return self

        async def __aenter__(self):
            return "session"

        async def __aexit__(self, *exc):
            return False

    async def fake_cycle(session, updater, **kwargs):
        seen.update(kwargs, session=session)
        return SimpleNamespace(complete=False)

    async def fake_sleep(seconds):
        delays.append(seconds)
        raise asyncio.CancelledError

    monkeypatch.setattr(app_main, "get_sessionmaker", lambda: Maker())
    monkeypatch.setattr(app_main, "build_updater", lambda **_: object())
    monkeypatch.setattr(whitelist, "reconcile_cycle", fake_cycle)
    monkeypatch.setattr(app_main.asyncio, "sleep", fake_sleep)
    settings = SimpleNamespace(
        whitelist_reconcile_minutes=15, whitelist_reconcile_batch_size=40,
        whitelist_reconcile_batch_pause_seconds=2.5, xui_request_timeout=5,
    )
    with pytest.raises(asyncio.CancelledError):
        await app_main._whitelist_reconcile_poller(settings)
    assert seen["batch_size"] == 40 and seen["pause_seconds"] == 2.5
    assert seen["status"] is whitelist.RECONCILE_STATUS
    assert delays == [whitelist.RECONCILE_RETRY_SECONDS]  # прерванный обход повторяется скоро


# --- Неудачный повтор BUSY: завершение обхода ≠ подтверждённая свежесть -------------


def _busy_on_first_read(monkeypatch, user_ids: set[int]) -> dict[int, int]:
    """Учёты, изменившиеся между чтением и сверкой: BUSY только при первом чтении."""
    original = whitelist._reconcile_one
    seen: dict[int, int] = {}

    async def flaky(session, user_id, *args, **kwargs):
        if user_id in user_ids:
            seen[user_id] = seen.get(user_id, 0) + 1
            if seen[user_id] == 1:
                return whitelist.ReconcileOutcome.BUSY
        return await original(session, user_id, *args, **kwargs)

    monkeypatch.setattr(whitelist, "_reconcile_one", flaky)
    return seen


async def _user_ids(session, account_ids) -> set[int]:
    return {(await session.get(WhitelistAccount, i)).user_id for i in account_ids}


async def test_failed_busy_retry_is_not_successful_cycle(session, wl_server, panel, monkeypatch):
    ids = await _populate(session, wl_server, panel, 2, used=GIB)
    _busy_on_first_read(monkeypatch, await _user_ids(session, ids))
    panel.unavailable_from_batch = 1  # первое чтение прошло, повторное — нет
    status = whitelist.ReconcileStatus()
    report = await _cycle(session, panel, status=status)

    assert report.complete and report.aborted is None
    assert (report.errors, report.skipped_busy, report.reconciled) == (2, 0, 0)
    assert report.accounts == 2 and report.unconfirmed == 2 and not report.confirmed
    assert report.cursor == ids[-1] and status.current is None  # курсор дошёл до конца
    assert status.last_complete_at is not None and status.last_success_at is None
    assert status.last_success_started_at is None and status.worst_case_staleness(
        datetime.now(UTC)) is None
    assert not any(await _reconciled(session, ids))  # старая статистика учётов не тронута
    text = "\n".join(texts.reconcile_status_lines(status))
    assert "ошибок 2" in text and "не сверено учётов: 2" in text
    assert "все учёты сверены" not in text and "данные учёта не старше" not in text


async def test_retry_helper_reports_unreadable_batch_as_errors(session, wl_server, panel):
    """Прямой вызов повтора: полностью нечитаемая пачка — ошибки, а не пропуск."""
    ids = await _populate(session, wl_server, panel, 2, used=GIB)
    panel.unavailable_from_batch = 0
    report = whitelist.ReconcileReport(
        server_id=wl_server.id, started_at=datetime.now(UTC), busy_ids=ids
    )

    async def sleep(_):
        pass

    await whitelist._retry_busy(
        session, panel, wl_server, report, batch_size=100, pause_seconds=0, sleep=sleep
    )
    status = whitelist.ReconcileStatus()
    await whitelist._finish_reconcile(session, status, report)
    assert (report.errors, report.skipped_busy) == (2, 0)
    assert status.last_success_at is None and status.last_complete_at is not None


async def test_partly_failed_busy_retry_counts_each_account_once(
    session, wl_server, panel, monkeypatch
):
    ids = await _populate(session, wl_server, panel, 5, used=GIB)
    busy = await _user_ids(session, [ids[1], ids[3]])
    _busy_on_first_read(monkeypatch, busy)

    async def break_one_on_retry(index, emails):
        if index == 0:
            panel.errors = {_email(1)}  # только повторное чтение не вернёт клиента

    panel.after_read = break_one_on_retry
    status = whitelist.ReconcileStatus()
    report = await _cycle(session, panel, status=status)

    assert report.complete
    assert (report.reconciled, report.errors, report.skipped_busy) == (4, 1, 0)
    assert report.retried_busy == 1 and report.accounts == 5  # без двойного подсчёта
    assert report.cursor == ids[-1]
    assert [i for i, ok in enumerate(await _reconciled(session, ids)) if not ok] == [1]
    assert status.last_complete_at is not None and status.last_success_at is None
    assert "ошибок 1" in texts.reconcile_status_lines(status)[0]


async def test_busy_again_without_http_error_still_withholds_freshness(
    session, wl_server, panel, monkeypatch
):
    ids = await _populate(session, wl_server, panel, 3, used=GIB)
    busy_user = (await session.get(WhitelistAccount, ids[0])).user_id
    original = whitelist._reconcile_one

    async def always_busy(session, user_id, *args, **kwargs):
        if user_id == busy_user:
            return whitelist.ReconcileOutcome.BUSY
        return await original(session, user_id, *args, **kwargs)

    monkeypatch.setattr(whitelist, "_reconcile_one", always_busy)
    status = whitelist.ReconcileStatus()
    report = await _cycle(session, panel, status=status)
    assert (report.errors, report.skipped_busy, report.reconciled) == (0, 1, 2)
    assert report.accounts == 3 and report.unconfirmed == 1
    assert status.last_success_at is None
    head = texts.reconcile_status_lines(status)[0]
    assert "изменились во время обхода 1" in head and "все учёты сверены" not in head


async def test_next_clean_traversal_recovers_and_old_confirmation_survives_gap(
    session, wl_server, panel, monkeypatch
):
    ids = await _populate(session, wl_server, panel, 3, used=GIB)
    status = whitelist.ReconcileStatus()
    first = await _cycle(session, panel, status=status)
    assert first.confirmed and status.last_success_at == first.finished_at
    confirmed_at, confirmed_started = status.last_success_at, status.last_success_started_at

    # Следующий обход: повтор BUSY не читается — подтверждение прежнее, завершение новое.
    panel.batches.clear()
    panel.unavailable_from_batch = 1
    _busy_on_first_read(monkeypatch, await _user_ids(session, ids[:2]))
    second = await _cycle(session, panel, status=status)
    assert second is not first and second.errors == 2 and not second.confirmed
    assert status.last_success_at == confirmed_at
    assert status.last_success_started_at == confirmed_started
    assert status.last_complete_at == second.finished_at and status.last_report is second
    lines = texts.reconcile_status_lines(status)
    assert "но не сверено учётов: 2" in lines[0]
    assert "последний полностью подтверждённый обход" in lines[1]

    # Панель восстановилась, учёты больше не заняты: подтверждение обновляется.
    panel.batches.clear()
    panel.unavailable_from_batch = None
    monkeypatch.undo()
    third = await _cycle(session, panel, status=status)
    assert third.confirmed and (third.errors, third.skipped_busy) == (0, 0)
    assert status.last_success_at == third.finished_at >= confirmed_at
    assert status.last_success_started_at == third.started_at
    assert "все учёты сверены" in texts.reconcile_status_lines(status)[0]
