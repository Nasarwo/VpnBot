from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class XuiError(Exception):
    """Базовая ошибка взаимодействия с панелью 3x-ui."""


class XuiAuthError(XuiError):
    """Ошибка авторизации в панели."""


class XuiClient:
    """Изолированный клиент для работы с API панели 3x-ui.

    Поддерживает vmess/vless/trojan. Хранит cookie-сессию на время жизни клиента.
    Пароли не логируются. Для временных сетевых ошибок выполняется retry.
    """

    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        timeout: float = 15.0,
        max_retries: int = 3,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._username = username
        self._password = password
        self._timeout = timeout
        self._max_retries = max_retries
        self._client = client
        self._owns_client = client is None
        self._logged_in = False

    async def __aenter__(self) -> XuiClient:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()

    @property
    def _http(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self._base_url, timeout=self._timeout
            )
        return self._client

    async def close(self) -> None:
        if self._client is not None and self._owns_client:
            await self._client.aclose()
            self._client = None

    async def _request(
        self, method: str, path: str, **kwargs: Any
    ) -> httpx.Response:
        last_exc: Exception | None = None
        for attempt in range(1, self._max_retries + 1):
            try:
                response = await self._http.request(method, path, **kwargs)
                return response
            except (httpx.TransportError, httpx.TimeoutException) as exc:
                last_exc = exc
                logger.warning(
                    "Сетевая ошибка к панели %s (попытка %s/%s): %s",
                    self._base_url,
                    attempt,
                    self._max_retries,
                    exc.__class__.__name__,
                )
                if attempt < self._max_retries:
                    await asyncio.sleep(0.5 * attempt)
        raise XuiError(
            f"Сетевая ошибка при запросе к панели {self._base_url}"
        ) from last_exc

    @staticmethod
    def _parse_json(response: httpx.Response) -> dict[str, Any]:
        try:
            return response.json()
        except json.JSONDecodeError as exc:
            raise XuiError("Некорректный JSON-ответ панели") from exc

    async def login(self) -> None:
        response = await self._request(
            "POST",
            "/login",
            data={"username": self._username, "password": self._password},
        )
        if response.status_code != 200:
            raise XuiAuthError(
                f"Ошибка авторизации в панели {self._base_url}: HTTP {response.status_code}"
            )
        data = self._parse_json(response)
        if not data.get("success", False):
            raise XuiAuthError(
                f"Панель {self._base_url} отклонила авторизацию"
            )
        self._logged_in = True

    async def _ensure_login(self) -> None:
        if not self._logged_in:
            await self.login()

    async def list_inbounds(self) -> list[dict[str, Any]]:
        """Возвращает список inbound'ов панели с их БД-id, портами и протоколами."""
        await self._ensure_login()
        response = await self._request("GET", "/panel/api/inbounds/list")
        data = self._parse_json(response)
        if not data.get("success", False):
            raise XuiError(f"Не удалось получить список inbound: {data.get('msg')}")
        obj = data.get("obj", [])
        return obj if isinstance(obj, list) else []

    async def get_inbound(self, inbound_id: int) -> dict[str, Any]:
        await self._ensure_login()
        response = await self._request(
            "GET", f"/panel/api/inbounds/get/{inbound_id}"
        )
        data = self._parse_json(response)
        if not data.get("success", False):
            raise XuiError(
                f"Не удалось получить inbound {inbound_id}: {data.get('msg')}"
            )
        return data.get("obj", {})

    def _extract_clients(self, inbound: dict[str, Any]) -> list[dict[str, Any]]:
        settings_raw = inbound.get("settings")
        if isinstance(settings_raw, str):
            try:
                settings = json.loads(settings_raw)
            except json.JSONDecodeError as exc:
                raise XuiError("Некорректный settings inbound") from exc
        elif isinstance(settings_raw, dict):
            settings = settings_raw
        else:
            settings = {}
        clients = settings.get("clients", [])
        return clients if isinstance(clients, list) else []

    async def get_client(
        self, inbound_id: int, *, client_uuid: str | None = None, email: str | None = None
    ) -> dict[str, Any] | None:
        inbound = await self.get_inbound(inbound_id)
        for client in self._extract_clients(inbound):
            if client_uuid is not None and client.get("id") == client_uuid:
                return client
            if email is not None and client.get("email") == email:
                return client
        return None

    async def update_client_expiry(
        self,
        inbound_id: int,
        client_uuid: str,
        email: str,
        expiry_ms: int,
        identifier: str | None = None,
    ) -> None:
        """Обновляет expiryTime клиента. Работает для всех протоколов.

        identifier — значение в пути updateClient/{id}: UUID для vless/vmess,
        email для trojan/shadowsocks/hysteria2. По умолчанию используется client_uuid.
        """
        await self._ensure_login()
        client = await self.get_client(
            inbound_id, client_uuid=client_uuid, email=email
        )
        if client is None:
            raise XuiError(
                f"Клиент {email} не найден в inbound {inbound_id}"
            )

        client["expiryTime"] = expiry_ms
        client["enable"] = True
        payload = {
            "id": inbound_id,
            "settings": json.dumps({"clients": [client]}),
        }
        path_id = identifier or client_uuid
        response = await self._request(
            "POST",
            f"/panel/api/inbounds/updateClient/{path_id}",
            json=payload,
        )
        data = self._parse_json(response)
        if not data.get("success", False):
            raise XuiError(
                f"Панель не подтвердила обновление клиента {email}: {data.get('msg')}"
            )

    async def add_client(
        self, inbound_id: int, client_obj: dict[str, object]
    ) -> None:
        """Создаёт нового клиента в inbound через addClient."""
        await self._ensure_login()
        payload = {
            "id": inbound_id,
            "settings": json.dumps({"clients": [client_obj]}),
        }
        response = await self._request(
            "POST", "/panel/api/inbounds/addClient", json=payload
        )
        data = self._parse_json(response)
        if not data.get("success", False):
            raise XuiError(
                f"Панель не подтвердила создание клиента "
                f"{client_obj.get('email')}: {data.get('msg')}"
            )

    async def get_client_ips(self, email: str) -> list[str]:
        """Возвращает список IP-адресов клиента из журнала 3x-ui (iplimit log).

        Требует включённого логирования IP в панели. Если записей нет — вернёт [].
        """
        await self._ensure_login()
        response = await self._request(
            "POST", f"/panel/api/inbounds/clientIps/{email}"
        )
        data = self._parse_json(response)
        if not data.get("success", False):
            return []
        return self._parse_ips(data.get("obj"))

    @staticmethod
    def _parse_ips(obj: object) -> list[str]:
        if obj is None:
            return []
        if isinstance(obj, list):
            return [str(ip).strip() for ip in obj if str(ip).strip()]
        if isinstance(obj, str):
            text = obj.strip()
            if not text or text.lower().startswith("no ip record"):
                return []
            # Пытаемся распарсить JSON-массив, иначе делим по разделителям.
            try:
                parsed = json.loads(text)
                if isinstance(parsed, list):
                    return [str(ip).strip() for ip in parsed if str(ip).strip()]
            except json.JSONDecodeError:
                pass
            parts = text.replace(",", "\n").split("\n")
            return [p.strip() for p in parts if p.strip()]
        return []
