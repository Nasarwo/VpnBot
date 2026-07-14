from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
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
    happ_url: str


def build_happ_import_url(
    subhub_url: str, admin_token: str, subscription_url: str
) -> str:
    """Build a signed HTTPS trampoline for importing a legacy subscription."""
    parsed_subscription = urlparse(subscription_url)
    if (
        parsed_subscription.scheme != "https"
        or not parsed_subscription.netloc
        or parsed_subscription.username
        or parsed_subscription.password
    ):
        raise ValueError("a valid HTTPS subscription URL is required")
    parsed_subhub = urlparse(subhub_url)
    if parsed_subhub.scheme not in {"http", "https"} or not parsed_subhub.netloc:
        raise ValueError("a valid SubHub URL is required")
    if not admin_token.strip():
        raise ValueError("SubHub admin token is required")
    payload = base64.urlsafe_b64encode(subscription_url.encode()).decode().rstrip("=")
    signature = hmac.new(
        admin_token.encode(), payload.encode(), hashlib.sha256
    ).hexdigest()
    return f"{subhub_url.rstrip('/')}/happ/import/{payload}/{signature}"


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
                happ_url=str(data["happ_url"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise SubHubError("SubHub returned an invalid response") from exc
        for value in (
            resolved.subscription_url,
            resolved.raw_subscription_url,
            resolved.happ_url,
        ):
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
        return await self.resolve_candidates_after_sync(
            [email], attempts=attempts, poll_delay=poll_delay
        )

    async def resolve_candidates_after_sync(
        self,
        identities: list[str],
        *,
        attempts: int = 4,
        poll_delay: float = 1.0,
    ) -> ResolvedSubscription:
        """Resolve the first panel identity known to SubHub.

        Older bot records can have a stale primary email while their per-server
        mappings contain the actual 3x-ui email. Try all safe candidates but
        trigger only one global synchronization.
        """
        candidates = list(
            dict.fromkeys(value.strip().casefold() for value in identities if value.strip())
        )
        if not candidates:
            raise ValueError("at least one identity is required")

        async def try_candidates() -> ResolvedSubscription:
            last_error: SubHubError | None = None
            for candidate in candidates:
                try:
                    return await self.resolve(email=candidate)
                except (SubHubNotFound, SubHubNotReady) as exc:
                    last_error = exc
            raise SubHubNotReady("none of the identities is ready") from last_error

        last_error: SubHubError | None = None
        try:
            return await try_candidates()
        except SubHubNotReady as exc:
            last_error = exc
        await self.trigger_sync()
        for attempt in range(max(1, attempts - 1)):
            if poll_delay > 0:
                await asyncio.sleep(poll_delay * (attempt + 1))
            try:
                return await try_candidates()
            except SubHubNotReady as exc:
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
