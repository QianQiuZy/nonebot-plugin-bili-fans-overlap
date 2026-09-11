"""Typed client for the bilifanscache room endpoint."""

from __future__ import annotations

import socket
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar, Literal

import httpx
from pydantic import BaseModel, ConfigDict
from typing_extensions import override

from .core import FanGroup, FanId, FanIds, FanSnapshot

if TYPE_CHECKING:
    from collections.abc import Sequence

_LIMITS = httpx.Limits(
    max_connections=20,
    max_keepalive_connections=5,
    keepalive_expiry=30.0,
)
_SOCKET_OPTIONS: list[tuple[int, int, int]] = [
    (socket.IPPROTO_TCP, socket.TCP_NODELAY, 1),
]


class FansResponse(BaseModel):
    """The successful response shape returned by bilifanscache /fans."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    code: int
    msg: str
    uid: int
    room_id: int
    medal: dict[str, int]
    guard_level: dict[str, int] | Literal["none"] | None = None


@dataclass(frozen=True, slots=True)
class FansCacheError(Exception):
    """A user-facing failure while reading one bilifanscache room."""

    room_id: int
    reason: str

    @override
    def __str__(self) -> str:
        return f"room {self.room_id}: {self.reason}"


def _create_client(api_base: str, timeout_seconds: float) -> httpx.AsyncClient:
    """Create a configured HTTP/2 client for the local cache service."""
    timeout = httpx.Timeout(
        connect=5.0,
        read=timeout_seconds,
        write=10.0,
        pool=10.0,
    )
    transport = httpx.AsyncHTTPTransport(
        http2=True,
        retries=3,
        limits=_LIMITS,
        socket_options=_SOCKET_OPTIONS,
    )
    return httpx.AsyncClient(
        base_url=api_base.rstrip("/"),
        follow_redirects=True,
        headers={"Accept": "application/json"},
        timeout=timeout,
        transport=transport,
    )


async def _fetch_room_fan_ids(
    client: httpx.AsyncClient,
    group: FanGroup,
) -> FanIds:
    """Fetch the cached fan UID set for one configured room."""
    payload = await _fetch_room_response(client, group)
    return frozenset(FanId(int(fan_uid)) for fan_uid in payload.medal)


async def _fetch_room_response(
    client: httpx.AsyncClient,
    group: FanGroup,
) -> FansResponse:
    """Fetch and validate one room response from bilifanscache."""
    try:
        response = await client.get("/fans", params={"room_id": group.room_id})
        _ = response.raise_for_status()
        payload = FansResponse.model_validate(response.json())
    except (httpx.HTTPError, ValueError) as error:
        raise FansCacheError(group.room_id, str(error)) from error
    if payload.code != 0:
        raise FansCacheError(group.room_id, f"cache returned code {payload.code}")
    return payload


async def _fetch_room_snapshot(
    client: httpx.AsyncClient,
    group: FanGroup,
) -> FanSnapshot:
    """Fetch fan levels and initialized guard levels for one room."""
    payload = await _fetch_room_response(client, group)
    if payload.guard_level is None:
        raise FansCacheError(group.room_id, "guard cache is not initialized")
    guard_levels = (
        {}
        if payload.guard_level == "none"
        else {
            FanId(int(fan_uid)): guard_level
            for fan_uid, guard_level in payload.guard_level.items()
            if guard_level in (1, 2, 3)
        }
    )
    return FanSnapshot(
        medal_levels={FanId(int(fan_uid)): level for fan_uid, level in payload.medal.items()},
        guard_levels=guard_levels,
    )


async def fetch_fan_ids(
    groups: Sequence[FanGroup],
    api_base: str,
    timeout_seconds: float,
) -> tuple[FanIds, ...]:
    """Fetch cached UID sets for all selected groups with one client."""
    async with _create_client(api_base, timeout_seconds) as client:
        return tuple(
            [await _fetch_room_fan_ids(client, group) for group in groups]
        )


async def fetch_fan_snapshots(
    groups: Sequence[FanGroup],
    api_base: str,
    timeout_seconds: float,
) -> tuple[FanSnapshot, ...]:
    """Fetch fan-medal and initialized guard-level snapshots for selected rooms."""
    async with _create_client(api_base, timeout_seconds) as client:
        return tuple(
            [await _fetch_room_snapshot(client, group) for group in groups]
        )
