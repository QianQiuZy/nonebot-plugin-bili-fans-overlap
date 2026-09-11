from typing import final

import httpx2
import pytest
from nonebot_plugin_bili_fans_overlap.api import (
    FansCacheError,
    fetch_fan_ids,
    fetch_fan_snapshots,
)
from nonebot_plugin_bili_fans_overlap.core import FanGroup, RoomId, UserId


@final
class _ClientContext:
    client: httpx2.AsyncClient

    def __init__(self, client: httpx2.AsyncClient) -> None:
        self.client = client

    async def __aenter__(self) -> httpx2.AsyncClient:
        return self.client

    async def __aexit__(self, *args: object) -> None:
        await self.client.aclose()


def _group(room_id: int) -> FanGroup:
    return FanGroup(RoomId(room_id), UserId(room_id), f"主播{room_id}", f"勋章{room_id}")


@pytest.mark.asyncio
async def test_fetch_fan_ids_reads_uid_keys_from_medal_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requested_rooms: list[str] = []

    async def handler(request: httpx2.Request) -> httpx2.Response:
        requested_rooms.append(request.url.params["room_id"])
        return httpx2.Response(
            200,
            json={
                "code": 0,
                "msg": "success",
                "uid": 99,
                "room_id": int(request.url.params["room_id"]),
                "medal": {"101": 1, "102": 2},
            },
        )

    def create_client(api_base: str, _timeout_seconds: float) -> _ClientContext:
        return _ClientContext(
            httpx2.AsyncClient(base_url=api_base, transport=httpx2.MockTransport(handler)),
        )

    monkeypatch.setattr("nonebot_plugin_bili_fans_overlap.api._create_client", create_client)
    result = await fetch_fan_ids((_group(1), _group(2)), "http://cache", 1.0)

    assert requested_rooms == ["1", "2"]
    assert result == (frozenset({101, 102}), frozenset({101, 102}))


@pytest.mark.asyncio
async def test_fetch_fan_ids_raises_for_nonzero_cache_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def handler(_request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(
            200,
            json={"code": -1, "msg": "failed", "uid": 99, "room_id": 1, "medal": {}},
        )

    def create_client(api_base: str, _timeout_seconds: float) -> _ClientContext:
        return _ClientContext(
            httpx2.AsyncClient(base_url=api_base, transport=httpx2.MockTransport(handler)),
        )

    monkeypatch.setattr("nonebot_plugin_bili_fans_overlap.api._create_client", create_client)

    with pytest.raises(FansCacheError, match="cache returned code -1"):
        _ = await fetch_fan_ids((_group(1),), "http://cache", 1.0)


@pytest.mark.asyncio
async def test_fetch_fan_snapshots_reads_nonzero_guard_levels(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def handler(_request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(
            200,
            json={
                "code": 0,
                "msg": "success",
                "uid": 99,
                "room_id": 1,
                "medal": {"101": 1, "102": 2},
                "guard_level": {"101": 3, "102": 0},
            },
        )

    def create_client(api_base: str, _timeout_seconds: float) -> _ClientContext:
        return _ClientContext(
            httpx2.AsyncClient(base_url=api_base, transport=httpx2.MockTransport(handler)),
        )

    monkeypatch.setattr("nonebot_plugin_bili_fans_overlap.api._create_client", create_client)

    result = await fetch_fan_snapshots((_group(1),), "http://cache", 1.0)

    assert result[0].medal_levels == {101: 1, 102: 2}
    assert result[0].guard_levels == {101: 3}


@pytest.mark.asyncio
async def test_fetch_fan_snapshots_rejects_uninitialized_guard_cache(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def handler(_request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(
            200,
            json={
                "code": 0,
                "msg": "success",
                "uid": 99,
                "room_id": 1,
                "medal": {"101": 1},
                "guard_level": None,
            },
        )

    def create_client(api_base: str, _timeout_seconds: float) -> _ClientContext:
        return _ClientContext(
            httpx2.AsyncClient(base_url=api_base, transport=httpx2.MockTransport(handler)),
        )

    monkeypatch.setattr("nonebot_plugin_bili_fans_overlap.api._create_client", create_client)

    with pytest.raises(FansCacheError, match="guard cache is not initialized"):
        _ = await fetch_fan_snapshots((_group(1),), "http://cache", 1.0)
