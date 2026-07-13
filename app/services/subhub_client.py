from __future__ import annotations

import asyncio
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx


class SubHubError(Exception):
    """Base error for the internal SubHub integration."""


class SubHubNotFound(SubHubError):
    """The panels have not exposed this identity to SubHub yet."""


class SubHubNotReady(SubHubError):
    """The identity exists, but currently has no active nodes."""


@dataclass(frozen=True, slots=True)
class ResolvedSubscription:
    email: str
    subscription_url: str
    raw_subscription_url: str


class SubHubClient:
    """Small authenticated client for the SubHub admin API.

    Subscription URLs and tokens are intentionally never logged here.
    """

    def __init__(
        self,
        base_url: str,
        admin_token: str,
        *,
        timeout: float = 15.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        if not base_url.strip() or not admin_token.strip():
            raise ValueError("SubHub URL and admin token are required")
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/") + "/",
            headers={"X-Admin-Token": admin_token},
            timeout=timeout,
            transport=transport,
        )

    async def __aenter__(self) -> SubHubClient:
        return self

    async def __aexit__(self, *_args: object) -> None:
        await self.close()

    async def close(self) -> None:
        await self._client.aclose()

    async def resolve(
        self, *, email: str | None = None, token: str | None = None
    ) -> ResolvedSubscription:
        payload = {"email": email} if email is not None else {"token": token}
        try:
            response = await self._client.post("admin/subscriptions/resolve", json=payload)
        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            raise SubHubError("SubHub is temporarily unavailable") from exc
        if response.status_code == 404:
            raise SubHubNotFound("subscription was not found")
        if response.status_code == 409:
            raise SubHubNotReady("subscription is not ready")
        if response.status_code in {401, 403}:
            raise SubHubError("SubHub authentication failed")
        if response.status_code != 200:
            raise SubHubError(f"SubHub resolve failed with HTTP {response.status_code}")
        try:
            data = response.json()
            email_value = data["email"]
            if not isinstance(email_value, str) or not email_value.strip():
                raise ValueError("missing email")
            resolved = ResolvedSubscription(
                email=email_value.strip().casefold(),
                subscription_url=str(data["subscription_url"]),
                raw_subscription_url=str(data["raw_subscription_url"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise SubHubError("SubHub returned an invalid response") from exc
        for value in (resolved.subscription_url, resolved.raw_subscription_url):
            parsed = urlparse(value)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                raise SubHubError("SubHub returned an invalid subscription URL")
        return resolved

    async def trigger_sync(self) -> None:
        try:
            response = await self._client.post("admin/sync")
        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            raise SubHubError("SubHub is temporarily unavailable") from exc
        if response.status_code in {202, 409}:
            return
        if response.status_code in {401, 403}:
            raise SubHubError("SubHub authentication failed")
        raise SubHubError(f"SubHub sync failed with HTTP {response.status_code}")

    async def resolve_after_sync(
        self,
        email: str,
        *,
        attempts: int = 4,
        poll_delay: float = 1.0,
    ) -> ResolvedSubscription:
        last_error: SubHubError | None = None
        try:
            return await self.resolve(email=email)
        except (SubHubNotFound, SubHubNotReady) as exc:
            last_error = exc
        await self.trigger_sync()
        for attempt in range(max(1, attempts - 1)):
            if poll_delay > 0:
                await asyncio.sleep(poll_delay * (attempt + 1))
            try:
                return await self.resolve(email=email)
            except (SubHubNotFound, SubHubNotReady) as exc:
                last_error = exc
        raise SubHubNotReady("subscription is still being prepared") from last_error


async def trigger_configured_sync(
    base_url: str,
    admin_token: str,
    *,
    timeout: float = 15.0,
) -> bool:
    """Best-effort notification after a successful panel mutation."""
    if not base_url.strip() or not admin_token.strip():
        return False
    try:
        async with SubHubClient(base_url, admin_token, timeout=timeout) as client:
            await client.trigger_sync()
    except (SubHubError, ValueError):
        return False
    return True
