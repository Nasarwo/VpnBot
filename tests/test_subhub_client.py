from __future__ import annotations

import json

import httpx
import pytest

from app.services.subhub_client import (
    SubHubClient,
    SubHubError,
    build_happ_import_url,
)


async def test_resolve_returns_unified_subscription():
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["X-Admin-Token"] == "admin-secret"
        assert request.url.path == "/admin/subscriptions/resolve"
        return httpx.Response(200, json={
            "email": "client-id",
            "subscription_url": "https://sub.example/connection/stable-token",
            "raw_subscription_url": "https://sub.example/connection/raw/stable-token",
            "happ_url": "https://sub.example/happ/add/stable-token",
        })

    async with SubHubClient(
        "https://internal.example", "admin-secret",
        transport=httpx.MockTransport(handler),
    ) as client:
        result = await client.resolve(email="client-id")

    assert result.email == "client-id"
    assert result.subscription_url.endswith("/connection/stable-token")


async def test_resolve_after_sync_waits_for_new_panel_client():
    resolves = 0
    syncs = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal resolves, syncs
        if request.url.path == "/admin/sync":
            syncs += 1
            return httpx.Response(202)
        resolves += 1
        if resolves == 1:
            return httpx.Response(404)
        return httpx.Response(200, json={
            "email": "client-id",
            "subscription_url": "https://sub.example/connection/token",
            "raw_subscription_url": "https://sub.example/connection/raw/token",
            "happ_url": "https://sub.example/happ/add/token",
        })

    async with SubHubClient(
        "https://internal.example", "admin-secret",
        transport=httpx.MockTransport(handler),
    ) as client:
        result = await client.resolve_after_sync("client-id", attempts=2, poll_delay=0)

    assert result.email == "client-id"
    assert resolves == 2
    assert syncs == 1


async def test_resolve_candidates_uses_mapping_identity_before_sync():
    requested: list[str] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/admin/subscriptions/resolve"):
            identity = json.loads(request.content)["email"]
            requested.append(identity)
            if identity == "mapping@example.com":
                return httpx.Response(200, json={
                    "email": identity,
                    "subscription_url": "https://sub.example/connection/token",
                    "raw_subscription_url": "https://sub.example/connection/raw/token",
                    "happ_url": "https://sub.example/happ/add/token",
                })
            return httpx.Response(404)
        raise AssertionError("sync must not run when a mapping identity resolves")

    async with SubHubClient(
        "https://sub.example", "admin", transport=httpx.MockTransport(handler)
    ) as client:
        result = await client.resolve_candidates_after_sync(
            ["stale@example.com", " Mapping@Example.com ", "mapping@example.com"],
            poll_delay=0,
        )

    assert result.email == "mapping@example.com"
    assert requested == ["stale@example.com", "mapping@example.com"]


async def test_authentication_failure_has_safe_error_message():
    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(401)

    async with SubHubClient(
        "https://internal.example", "do-not-leak-this",
        transport=httpx.MockTransport(handler),
    ) as client:
        with pytest.raises(SubHubError) as error:
            await client.resolve(email="client-id")

    assert "do-not-leak-this" not in str(error.value)


def test_build_happ_import_url_is_stable_and_opaque():
    subscription = "https://enderworld.org/sub/client-public-id"
    first = build_happ_import_url(
        "https://sub.example", "admin-secret", subscription
    )
    second = build_happ_import_url(
        "https://sub.example/", "admin-secret", subscription
    )
    assert first == second
    assert first.startswith("https://sub.example/happ/import/")
    assert subscription not in first
