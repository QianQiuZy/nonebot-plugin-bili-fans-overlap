"""Pure room parsing and UID overlap calculations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar, Final, NewType, TypeAlias

from pydantic import BaseModel, ConfigDict, TypeAdapter

if TYPE_CHECKING:
    from collections.abc import Collection, Iterable, Mapping, Sequence
    from pathlib import Path

RoomId = NewType("RoomId", int)
UserId = NewType("UserId", int)
FanId = NewType("FanId", int)
FanIds: TypeAlias = frozenset[FanId]
GroupTotal: TypeAlias = tuple[str, int]
OverlapPair: TypeAlias = tuple[str, str, float]

INVALID_INPUT_MESSAGE: Final = "请输入完整粉丝团名称进行查重"
MIN_GROUPS: Final = 2
MAX_GROUPS: Final = 5


class RoomRecord(BaseModel):
    """The JSON shape copied from bilifanscache."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    uid: int
    name: str
    medal: str


@dataclass(frozen=True, slots=True)
class FanGroup:
    """A configured room and its exact fan-medal name."""

    room_id: RoomId
    uid: UserId
    name: str
    medal: str


def load_rooms(path: Path) -> tuple[FanGroup, ...]:
    """Load the bundled bilifanscache rooms configuration."""
    records = TypeAdapter(dict[str, RoomRecord]).validate_json(path.read_bytes())
    return tuple(
        FanGroup(
            room_id=RoomId(int(room_id)),
            uid=UserId(record.uid),
            name=record.name,
            medal=record.medal,
        )
        for room_id, record in records.items()
    )


def build_medal_index(groups: Iterable[FanGroup]) -> Mapping[str, tuple[FanGroup, ...]]:
    """Index exact medal names while retaining duplicate-name ambiguities."""
    indexed: dict[str, list[FanGroup]] = {}
    for group in groups:
        indexed.setdefault(group.medal, []).append(group)
    return {medal: tuple(matches) for medal, matches in indexed.items()}


def parse_medal_names(
    raw_text: str,
    medal_index: Mapping[str, tuple[FanGroup, ...]],
) -> tuple[FanGroup, ...] | None:
    """Parse two to five unique, complete medal names from command text."""
    names = tuple(raw_text.split())
    if not MIN_GROUPS <= len(names) <= MAX_GROUPS:
        return None
    if len(set(names)) != len(names):
        return None

    groups: list[FanGroup] = []
    for name in names:
        matches = medal_index.get(name)
        if matches is None or len(matches) != 1:
            return None
        groups.append(matches[0])
    return tuple(groups)


def calculate_overlap_percentage(
    base: Collection[FanId],
    other: Collection[FanId],
) -> float:
    """Return the other group's shared percentage of the base group."""
    base_ids = frozenset(base)
    if not base_ids:
        return 0.0
    other_ids = frozenset(other)
    return len(base_ids & other_ids) / len(base_ids) * 100


def format_overlap_results(
    totals: Sequence[GroupTotal],
    results: Sequence[OverlapPair],
) -> str:
    """Render group totals followed by pairwise overlap percentages."""
    lines = ["粉丝团重合查询"]
    lines.extend(f"{medal}总数：{total}" for medal, total in totals)
    lines.extend(
        f"{left}&{right}：{percentage:.2f}%"
        for left, right, percentage in results
    )
    return "\n".join(lines)
