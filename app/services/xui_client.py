from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# Временные ошибки HTTP, при которых допустим retry.
_RETRY_STATUS = {502, 503, 504}

# Безопасные методы не требуют CSRF-токена в 3x-ui.
_SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}

# Заголовок CSRF-токена (3x-ui >= 3.2.x).
_CSRF_HEADER = "X-CSRF-Token"


class XuiError(Exception):
    """Базовая ошибка взаимодействия с панелью 3x-ui."""


class XuiAuthError(XuiError):
    """Ошибка авторизации в панели."""


class XuiClient:
    """Изолированный REST-клиент панели 3x-ui (MHSanaei/3x-ui).

    Принципы:
    - одна cookie-сессия на панель (login один раз, cookie переиспользуется);
    - поддержка CSRF (3x-ui >= 3.2.x): перед login берётся токен с /csrf-token и
      подставляется в заголовок X-CSRF-Token во все небезопасные запросы;
    - при истёкшей сессии (401/403/redirect на login) — повторный login один раз
      и повтор запроса; без бесконечного login-loop;
    - retry только для временных ошибок (network, 502/503/504), не для 4xx;
    - раздельные connect/read таймауты;
    - обновление клиента по принципу read-modify-write (поля не теряются);
    - пароли/cookie/CSRF-токен не логируются.

    Альтернатива входу по паролю — Bearer API-токен панели (api_token): тогда
    login и CSRF не используются (3x-ui снимает CSRF для api_authed запросов).
    """

    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        timeout: float = 15.0,
        connect_timeout: float = 5.0,
        max_retries: int = 3,
        api_token: str | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._username = username
        self._password = password
        self._api_token = api_token
        self._csrf_token: str | None = None
        # None — ещё не проверяли; True/False — поддержка нового /panel/api/clients.
        self._clients_api: bool | None = None
        self._timeout = httpx.Timeout(
            timeout,
            connect=connect_timeout,
            read=timeout,
            write=timeout,
            pool=connect_timeout,
        )
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
            headers = {
                # Браузерный UA: многие панели за Cloudflare/nginx режут
                # стандартный python-httpx User-Agent ответом 403.
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en-US,en;q=0.9",
                "X-Requested-With": "XMLHttpRequest",
            }
            if self._api_token:
                headers["Authorization"] = f"Bearer {self._api_token}"
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=self._timeout,
                follow_redirects=True,
                headers=headers,
            )
        return self._client

    async def close(self) -> None:
        if self._client is not None and self._owns_client:
            await self._client.aclose()
            self._client = None

    # --- Низкоуровневая отправка с retry для временных ошибок ---------------

    async def _send(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        # CSRF-токен обязателен для небезопасных методов в 3x-ui >= 3.2.x.
        if method.upper() not in _SAFE_METHODS and self._csrf_token:
            headers = dict(kwargs.pop("headers", None) or {})
            headers[_CSRF_HEADER] = self._csrf_token
            kwargs["headers"] = headers
        last_exc: Exception | None = None
        for attempt in range(1, self._max_retries + 1):
            try:
                logger.debug(
                    "3x-ui %s %s%s (попытка %s/%s)",
                    method,
                    self._base_url,
                    path,
                    attempt,
                    self._max_retries,
                )
                response = await self._http.request(method, path, **kwargs)
            except (httpx.TransportError, httpx.TimeoutException) as exc:
                last_exc = exc
                logger.warning(
                    "Сетевая ошибка к панели %s%s (попытка %s/%s): %s: %s",
                    self._base_url,
                    path,
                    attempt,
                    self._max_retries,
                    exc.__class__.__name__,
                    exc,
                )
                if attempt < self._max_retries:
                    await asyncio.sleep(0.5 * attempt)
                continue

            logger.debug(
                "3x-ui ответ %s %s -> HTTP %s",
                method,
                path,
                response.status_code,
            )
            if response.status_code in _RETRY_STATUS and attempt < self._max_retries:
                logger.warning(
                    "Временная ошибка панели %s%s: HTTP %s (попытка %s/%s)",
                    self._base_url,
                    path,
                    response.status_code,
                    attempt,
                    self._max_retries,
                )
                await asyncio.sleep(0.5 * attempt)
                continue
            return response

        raise XuiError(
            f"Сетевая ошибка при запросе к панели {self._base_url}{path}"
        ) from last_exc

    def _looks_like_auth_failure(self, response: httpx.Response) -> bool:
        if response.status_code in (401, 403):
            return True
        # follow_redirects=True: истёкшая сессия обычно приводит на страницу login.
        url_path = str(response.url).rstrip("/")
        return url_path.endswith("/login")

    async def _api(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        """Авторизованный запрос: гарантирует login и при истёкшей сессии
        выполняет повторный login один раз и повторяет запрос."""
        await self._ensure_login()
        response = await self._send(method, path, **kwargs)
        if self._looks_like_auth_failure(response):
            logger.info(
                "Сессия панели %s истекла (HTTP %s) — повторный login",
                self._base_url,
                response.status_code,
            )
            self._logged_in = False
            await self.login()
            response = await self._send(method, path, **kwargs)
        return response

    @staticmethod
    def _parse_json(response: httpx.Response) -> dict[str, Any]:
        try:
            return response.json()
        except json.JSONDecodeError as exc:
            raise XuiError("Некорректный JSON-ответ панели") from exc

    # --- Авторизация --------------------------------------------------------

    async def _fetch_csrf_token(self) -> None:
        """Берёт CSRF-токен с /csrf-token (3x-ui >= 3.2.x).

        На старых панелях endpoint отсутствует — это не ошибка, тогда
        работаем без CSRF (токен остаётся None).
        """
        try:
            response = await self._send("GET", "/csrf-token")
        except XuiError:
            return
        if response.status_code != 200:
            logger.debug(
                "CSRF: /csrf-token -> HTTP %s (панель %s без CSRF?)",
                response.status_code,
                self._base_url,
            )
            return
        try:
            data = response.json()
        except json.JSONDecodeError:
            return
        token = data.get("obj")
        if isinstance(token, str) and token:
            self._csrf_token = token
            logger.debug("CSRF-токен получен для панели %s", self._base_url)

    async def login(self) -> None:
        if self._api_token:
            # Bearer-аутентификация: login и CSRF не требуются.
            self._logged_in = True
            return
        # Сначала получаем CSRF-токен и session-cookie, иначе 3x-ui 3.2.x
        # отклонит POST /login с HTTP 403 ещё до проверки пароля.
        self._csrf_token = None
        await self._fetch_csrf_token()
        response = await self._send(
            "POST",
            "/login",
            data={"username": self._username, "password": self._password},
        )
        if response.status_code != 200:
            server_hdr = response.headers.get("server", "")
            snippet = response.text[:200].replace("\n", " ")
            logger.warning(
                "Авторизация в панели %s: HTTP %s (server=%r). Тело: %s",
                self._base_url,
                response.status_code,
                server_hdr,
                snippet,
            )
            raise XuiAuthError(
                f"Ошибка авторизации в панели {self._base_url}: "
                f"HTTP {response.status_code}"
            )
        data = self._parse_json(response)
        if not data.get("success", False):
            logger.warning(
                "Панель %s отклонила авторизацию (user=%s): %s",
                self._base_url,
                self._username,
                data.get("msg"),
            )
            raise XuiAuthError(f"Панель {self._base_url} отклонила авторизацию")
        self._logged_in = True
        logger.info("Авторизация в панели %s успешна", self._base_url)

    async def _ensure_login(self) -> None:
        if not self._logged_in:
            await self.login()

    # --- Inbounds -----------------------------------------------------------

    async def list_inbounds(self) -> list[dict[str, Any]]:
        """Возвращает список inbound'ов панели с их БД-id, портами и протоколами."""
        response = await self._api("GET", "/panel/api/inbounds/list")
        data = self._parse_json(response)
        if not data.get("success", False):
            raise XuiError(f"Не удалось получить список inbound: {data.get('msg')}")
        obj = data.get("obj", [])
        return obj if isinstance(obj, list) else []

    async def get_inbound(self, inbound_id: int) -> dict[str, Any]:
        response = await self._api("GET", f"/panel/api/inbounds/get/{inbound_id}")
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

    # --- Поиск клиента ------------------------------------------------------

    async def find_client(
        self,
        inbound_id: int,
        *,
        client_uuid: str | None = None,
        email: str | None = None,
        sub_id: str | None = None,
    ) -> dict[str, Any] | None:
        """Ищет клиента в inbound по uuid, email или subId (стабильные ID)."""
        inbound = await self.get_inbound(inbound_id)
        for client in self._extract_clients(inbound):
            if client_uuid is not None and client.get("id") == client_uuid:
                return client
            if email is not None and client.get("email") == email:
                return client
            if sub_id is not None and client.get("subId") == sub_id:
                return client
        return None

    async def get_client(
        self,
        inbound_id: int,
        *,
        client_uuid: str | None = None,
        email: str | None = None,
    ) -> dict[str, Any] | None:
        """Совместимый алиас find_client (по uuid/email)."""
        return await self.find_client(
            inbound_id, client_uuid=client_uuid, email=email
        )

    @staticmethod
    def _path_identifier(client: dict[str, Any]) -> str:
        """Идентификатор для updateClient/{id}: id для vless/vmess, иначе email."""
        cid = client.get("id")
        if cid:
            return str(cid)
        return str(client.get("email", ""))

    # --- Обновление клиента (read-modify-write) -----------------------------

    async def update_client(
        self,
        inbound_id: int,
        changes: dict[str, Any],
        *,
        client_uuid: str | None = None,
        email: str | None = None,
        sub_id: str | None = None,
    ) -> dict[str, Any]:
        """Обновляет клиента, сохраняя все его поля и меняя только нужные.

        Возвращает итоговый объект клиента (после слияния).
        """
        client = await self.find_client(
            inbound_id, client_uuid=client_uuid, email=email, sub_id=sub_id
        )
        if client is None:
            raise XuiError(
                f"Клиент не найден в inbound {inbound_id} "
                f"(uuid={client_uuid}, email={email}, sub_id={sub_id})"
            )

        updated = {**client, **changes}
        path_id = self._path_identifier(client)
        payload = {
            "id": inbound_id,
            "settings": json.dumps({"clients": [updated]}),
        }
        logger.info(
            "3x-ui updateClient: inbound=%s email=%s id=%s изменения=%s",
            inbound_id,
            updated.get("email"),
            path_id,
            sorted(changes.keys()),
        )
        response = await self._api(
            "POST", f"/panel/api/inbounds/updateClient/{path_id}", json=payload
        )
        data = self._parse_json(response)
        if not data.get("success", False):
            logger.warning(
                "updateClient отклонён: inbound=%s email=%s msg=%s obj=%s",
                inbound_id,
                updated.get("email"),
                data.get("msg"),
                data.get("obj"),
            )
            raise XuiError(
                f"Панель не подтвердила обновление клиента "
                f"{updated.get('email')}: {data.get('msg')}"
            )
        logger.info(
            "updateClient ок: inbound=%s email=%s", inbound_id, updated.get("email")
        )
        return updated

    async def set_client_expiry(
        self,
        inbound_id: int,
        expiry_ms: int,
        *,
        client_uuid: str | None = None,
        email: str | None = None,
        sub_id: str | None = None,
        verify: bool = False,
    ) -> None:
        """Устанавливает expiryTime (мс) и включает клиента."""
        await self.update_client(
            inbound_id,
            {"expiryTime": expiry_ms, "enable": True},
            client_uuid=client_uuid,
            email=email,
            sub_id=sub_id,
        )
        if verify:
            current = await self.find_client(
                inbound_id, client_uuid=client_uuid, email=email, sub_id=sub_id
            )
            actual = current.get("expiryTime") if current else None
            if actual != expiry_ms:
                logger.warning(
                    "Проверка expiry: ожидалось %s, в панели %s (inbound=%s email=%s)",
                    expiry_ms,
                    actual,
                    inbound_id,
                    email,
                )

    async def set_client_enabled(
        self,
        inbound_id: int,
        enabled: bool,
        *,
        client_uuid: str | None = None,
        email: str | None = None,
        sub_id: str | None = None,
    ) -> None:
        await self.update_client(
            inbound_id,
            {"enable": enabled},
            client_uuid=client_uuid,
            email=email,
            sub_id=sub_id,
        )

    async def set_client_ip_limit(
        self,
        inbound_id: int,
        limit_ip: int,
        *,
        client_uuid: str | None = None,
        email: str | None = None,
        sub_id: str | None = None,
    ) -> None:
        """Лимит уникальных IP (0 = без лимита). Не считать точным лимитом устройств."""
        await self.update_client(
            inbound_id,
            {"limitIp": limit_ip},
            client_uuid=client_uuid,
            email=email,
            sub_id=sub_id,
        )

    async def update_client_expiry(
        self,
        inbound_id: int,
        client_uuid: str,
        email: str,
        expiry_ms: int,
        identifier: str | None = None,  # noqa: ARG002 - совместимость сигнатуры
    ) -> None:
        """Совместимый метод: продление через read-modify-write."""
        await self.set_client_expiry(
            inbound_id, expiry_ms, client_uuid=client_uuid, email=email
        )

    # --- Создание / удаление клиента ---------------------------------------

    async def add_client(
        self, inbound_id: int, client_obj: dict[str, object]
    ) -> None:
        """Создаёт нового клиента в inbound через addClient."""
        payload = {
            "id": inbound_id,
            "settings": json.dumps({"clients": [client_obj]}),
        }
        logger.info(
            "3x-ui addClient: inbound=%s email=%s поля=%s",
            inbound_id,
            client_obj.get("email"),
            sorted(client_obj.keys()),
        )
        response = await self._api(
            "POST", "/panel/api/inbounds/addClient", json=payload
        )
        data = self._parse_json(response)
        if not data.get("success", False):
            logger.warning(
                "addClient отклонён: inbound=%s email=%s msg=%s obj=%s",
                inbound_id,
                client_obj.get("email"),
                data.get("msg"),
                data.get("obj"),
            )
            raise XuiError(
                f"Панель не подтвердила создание клиента "
                f"{client_obj.get('email')}: {data.get('msg')}"
            )
        logger.info(
            "addClient ок: inbound=%s email=%s",
            inbound_id,
            client_obj.get("email"),
        )

    async def del_client(self, inbound_id: int, client_uuid: str) -> None:
        """Удаляет клиента из inbound."""
        logger.info(
            "3x-ui delClient: inbound=%s id=%s", inbound_id, client_uuid
        )
        response = await self._api(
            "POST", f"/panel/api/inbounds/{inbound_id}/delClient/{client_uuid}"
        )
        data = self._parse_json(response)
        if not data.get("success", False):
            raise XuiError(
                f"Панель не подтвердила удаление клиента {client_uuid}: "
                f"{data.get('msg')}"
            )

    # --- Новый client-API (3x-ui >= 3.2.x) ---------------------------------

    async def supports_clients_api(self) -> bool:
        """Определяет, есть ли у панели новый client-API /panel/api/clients.

        В 3x-ui 3.2.x операции с клиентами перенесены из inbound-контроллера
        в отдельный clients-контроллер. Результат кешируется на время сессии.
        """
        if self._clients_api is not None:
            return self._clients_api
        response = await self._api(
            "GET", "/panel/api/clients/get/__caps_probe__"
        )
        # Существующий маршрут вернёт 200 (даже если клиент не найден),
        # на старых панелях маршрута нет — gin отдаёт 404.
        self._clients_api = response.status_code == 200
        logger.info(
            "Панель %s: client-API %s",
            self._base_url,
            "доступен" if self._clients_api else "недоступен (старая версия)",
        )
        return self._clients_api

    async def get_client_record(self, email: str) -> dict[str, Any] | None:
        """Возвращает запись клиента нового API: {"client": {...}, "inboundIds": [...]}.

        None — если клиент не найден.
        """
        response = await self._api(
            "GET", f"/panel/api/clients/get/{email}"
        )
        try:
            data = response.json()
        except json.JSONDecodeError:
            return None
        if not data.get("success", False):
            return None
        obj = data.get("obj")
        return obj if isinstance(obj, dict) else None

    async def create_client_record(
        self, client_obj: dict[str, Any], inbound_ids: list[int]
    ) -> None:
        """Создаёт глобального клиента и привязывает его к inbound'ам (новый API)."""
        payload = {"client": client_obj, "inboundIds": inbound_ids}
        logger.info(
            "3x-ui clients/add: email=%s inbounds=%s поля=%s",
            client_obj.get("email"),
            inbound_ids,
            sorted(client_obj.keys()),
        )
        response = await self._api(
            "POST", "/panel/api/clients/add", json=payload
        )
        data = self._parse_json(response)
        if not data.get("success", False):
            logger.warning(
                "clients/add отклонён: email=%s inbounds=%s msg=%s",
                client_obj.get("email"),
                inbound_ids,
                data.get("msg"),
            )
            raise XuiError(
                f"Панель не подтвердила создание клиента "
                f"{client_obj.get('email')}: {data.get('msg')}"
            )
        logger.info(
            "clients/add ок: email=%s inbounds=%s",
            client_obj.get("email"),
            inbound_ids,
        )

    async def update_client_record(
        self,
        email: str,
        client_obj: dict[str, Any],
        inbound_ids: list[int] | None = None,
    ) -> None:
        """Обновляет глобального клиента по email (новый API)."""
        path = f"/panel/api/clients/update/{email}"
        if inbound_ids is not None:
            ids = ",".join(str(i) for i in inbound_ids)
            path = f"{path}?inboundIds={ids}"
        logger.info(
            "3x-ui clients/update: email=%s inbounds=%s изменения=%s",
            email,
            inbound_ids,
            sorted(client_obj.keys()),
        )
        response = await self._api("POST", path, json=client_obj)
        data = self._parse_json(response)
        if not data.get("success", False):
            logger.warning(
                "clients/update отклонён: email=%s msg=%s",
                email,
                data.get("msg"),
            )
            raise XuiError(
                f"Панель не подтвердила обновление клиента {email}: "
                f"{data.get('msg')}"
            )
        logger.info("clients/update ок: email=%s", email)

    # --- Трафик / IP --------------------------------------------------------

    async def get_client_traffic(self, email: str) -> dict[str, Any] | None:
        """Возвращает статистику трафика клиента по email."""
        response = await self._api(
            "GET", f"/panel/api/inbounds/getClientTraffics/{email}"
        )
        data = self._parse_json(response)
        if not data.get("success", False):
            return None
        obj = data.get("obj")
        return obj if isinstance(obj, dict) else None

    async def get_client_ips(self, email: str) -> list[str]:
        """Возвращает список IP-адресов клиента из журнала 3x-ui (iplimit log).

        Требует включённого логирования IP в панели. Если записей нет — вернёт [].
        """
        if await self.supports_clients_api():
            path = f"/panel/api/clients/ips/{email}"
        else:
            path = f"/panel/api/inbounds/clientIps/{email}"
        response = await self._api("POST", path)
        try:
            data = response.json()
        except json.JSONDecodeError:
            return []
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
