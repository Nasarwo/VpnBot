"""Совместимость inbound услуги «Обход белых списков» с форматом ссылок SubHub.

Сервер услуги готов, только если SubHub сможет построить для его inbound
рабочую ссылку. Правила повторяют `SingleLinkVpn/subhub/app/link_builder.py`
(`build_link`) и `mihomo_profiles._proxy` и проверяются тестом против этих
исходников. Это проверка данных панели, а не того, что панель уже добавлена в
конфигурацию рабочего SubHub (`config.yaml`, `reality_overrides`).

Ключи и данные чужих клиентов не попадают в сообщения: приватный ключ REALITY
используется только для вывода публичного (как в SubHub), у клиентов панели
читается только значение flow.
"""

from __future__ import annotations

import base64
import binascii
import json
from collections import Counter
from dataclasses import dataclass
from typing import Any

from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey

# Транспорты VLESS REALITY, для которых SubHub передаёт в ссылке все параметры.
_REALITY_NETWORKS = ("tcp", "raw", "xhttp")
_HYSTERIA = ("hysteria", "hysteria2", "hy2")
# Значения flow, которые 3x-ui предлагает для VLESS (Xray: только TCP/RAW).
_KNOWN_FLOWS = ("xtls-rprx-vision", "xtls-rprx-vision-udp443")


@dataclass(frozen=True, slots=True)
class InboundCompat:
    """Вердикт по одному inbound: ``problems`` блокируют готовность, ``notes`` — нет."""

    inbound_id: int
    kind: str
    problems: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()

    @property
    def compatible(self) -> bool:
        return not self.problems


def _json(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
        except ValueError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def _strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if item not in (None, "")]


def _public_key_available(reality: dict[str, Any]) -> bool:
    client_side = _json(reality.get("settings"))
    for source in (client_side, reality):
        for key in ("publicKey", "public_key", "password"):
            if source.get(key):
                return True
    private = reality.get("privateKey") or reality.get("private_key")
    if not isinstance(private, str) or not private.strip():
        return False
    value = private.strip()
    try:
        raw = base64.urlsafe_b64decode((value + "=" * (-len(value) % 4)).encode("ascii"))
    except (UnicodeEncodeError, ValueError, binascii.Error):
        return False
    if len(raw) != 32:
        return False
    # Как SubHub derive_public_key: ключ должен выводиться, сам он не сохраняется.
    try:
        X25519PrivateKey.from_private_bytes(raw).public_key()
    except ValueError:
        return False
    return True


def _foreign_flows(settings: dict[str, Any]) -> Counter[str]:
    clients = settings.get("clients")
    flows: Counter[str] = Counter()
    for client in clients if isinstance(clients, list) else []:
        if isinstance(client, dict):
            flows[str(client.get("flow") or "")] += 1
    return flows


def _check_vless_reality(
    stream: dict[str, Any],
    settings: dict[str, Any],
    network: str,
    flow: str | None,
) -> tuple[list[str], list[str]]:
    problems: list[str] = []
    notes: list[str] = []
    reality = _json(stream.get("realitySettings"))
    if network not in _REALITY_NETWORKS:
        problems.append(
            f"транспорт {network}: SubHub передаёт в ссылке параметры только для "
            "tcp/raw и xhttp"
        )
    if network in ("tcp", "raw"):
        header = _json(_json(stream.get(f"{network}Settings")).get("header"))
        header_type = str(header.get("type") or "none").lower()
        if header_type != "none":
            problems.append(
                f"{network} header {header_type}: SubHub не передаёт headerType в ссылке"
            )
    if not _public_key_available(reality):
        problems.append(
            "REALITY: публичный ключ недоступен (нет publicKey и корректного privateKey)"
        )
    if not _strings(reality.get("serverNames")):
        problems.append("REALITY: пустой serverNames (SNI)")
    if not _strings(reality.get("shortIds")):
        problems.append("REALITY: нет непустого значения в shortIds")
    decryption = str(settings.get("decryption") or "none").lower()
    if decryption != "none":
        problems.append(
            "VLESS decryption ≠ none (VLESS Encryption): SubHub передаёт encryption=none"
        )
    if flow:
        if flow not in _KNOWN_FLOWS:
            problems.append(f"flow={flow} не поддерживается для VLESS REALITY")
        elif network not in ("tcp", "raw"):
            problems.append(
                f"flow={flow} неприменим к транспорту {network}: SubHub не передаст его в ссылке"
            )
        else:
            notes.append(f"Клиенты услуги и ссылка SubHub получат flow={flow}.")
    elif network in ("tcp", "raw"):
        flows = _foreign_flows(settings)
        used = sorted(value for value in flows if value)
        if used:
            notes.append(
                "У существующих клиентов inbound на панели задан flow "
                + ", ".join(f"{value} ({flows[value]})" for value in used)
                + ". Клиенты услуги создаются без flow: бот не переносит его с чужих "
                "клиентов. Если flow нужен, задайте его явно для целевого inbound "
                "(/delinbound и /addinbound <server> <inbound> vless <flow>) и "
                "синхронизируйте сервер."
            )
        else:
            notes.append("Клиенты услуги создаются без flow.")
    return problems, notes


def check_inbound(raw: dict[str, Any], *, flow: str | None = None) -> InboundCompat:
    """Проверяет inbound из ``/panel/api/inbounds/list`` и flow целевой строки бота."""
    raw_id = raw.get("id")
    inbound_id = raw_id if isinstance(raw_id, int) else -1
    protocol = str(raw.get("protocol") or "").lower() or "?"
    settings = _json(raw.get("settings"))
    stream = _json(raw.get("streamSettings"))
    # Значения по умолчанию — как в SubHub normalize_inbound.
    network = str(stream.get("network") or raw.get("network") or "tcp").lower()
    security = str(stream.get("security") or "none").lower()

    if protocol == "vless":
        kind = f"vless/{security}/{network}"
        if security != "reality":
            return InboundCompat(
                inbound_id, kind,
                problems=(
                    f"VLESS без REALITY (security={security}): SubHub строит ссылки "
                    "VLESS только с REALITY",
                ),
            )
        problems, notes = _check_vless_reality(stream, settings, network, flow)
        return InboundCompat(inbound_id, kind, tuple(problems), tuple(notes))

    if protocol in _HYSTERIA:
        kind = protocol
        problems = []
        notes = ["Hysteria2 проверен только по исходникам SubHub, не трафиком."]
        if security != "tls":
            problems.append(f"{protocol} с security={security}: нужен TLS")
        tls = _json(stream.get("tlsSettings"))
        if not (tls.get("serverName") or tls.get("server_name")):
            notes.append("В tlsSettings нет serverName: SubHub подставит public_host сервера.")
        if flow:
            problems.append(f"flow={flow} неприменим к {protocol}")
        return InboundCompat(inbound_id, kind, tuple(problems), tuple(notes))

    return InboundCompat(
        inbound_id, protocol,
        problems=(
            f"протокол {protocol}: SubHub строит ссылки только для VLESS REALITY "
            "и Hysteria2",
        ),
    )


def describe(compat: InboundCompat) -> str:
    """Краткая строка для администратора: id, вид и итог."""
    if compat.compatible:
        return f"{compat.inbound_id} ({compat.kind}, совместим)"
    return (
        f"{compat.inbound_id} ({compat.kind}, несовместим: "
        + "; ".join(compat.problems) + ")"
    )
