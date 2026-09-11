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
LevelBucket: TypeAlias = tuple[int, int]
GuardTier: TypeAlias = tuple[str, int]

LEVEL_BUCKETS: Final[tuple[LevelBucket, ...]] = (
    (1, 10),
    (11, 20),
    (21, 30),
    (31, 40),
    (41, 50),
    (51, 60),
)
GUARD_TIERS: Final[tuple[GuardTier, ...]] = (
    ("舰长", 3),
    ("提督", 2),
    ("总督", 1),
)
DETAIL_SEPARATOR: Final = "——————————"
DETAIL_EXPLANATION_SEPARATOR: Final = "————说明————"

INVALID_INPUT_MESSAGE: Final = "请输入完整粉丝团名称进行查重"
DETAILED_INVALID_INPUT_MESSAGE: Final = "详细查重仅支持两个完整粉丝团名称"
DETAILED_GROUP_COUNT: Final = 2
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


@dataclass(frozen=True, slots=True)
class FanSnapshot:
    """Fan-medal levels and non-zero guard levels for one room."""

    medal_levels: Mapping[FanId, int]
    guard_levels: Mapping[FanId, int]


@dataclass(frozen=True, slots=True)
class DetailedDirectionStats:
    """Detailed overlap statistics using one medal as the denominator."""

    base_total: int
    intersection_count: int
    level_counts: tuple[int, ...]
    guard_counts: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class DetailedOverlapStats:
    """Bidirectional detailed overlap statistics for two snapshots."""

    first: DetailedDirectionStats
    second: DetailedDirectionStats
    shared_guard_count: int


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


def parse_two_medal_names(
    raw_text: str,
    medal_index: Mapping[str, tuple[FanGroup, ...]],
) -> tuple[FanGroup, FanGroup] | None:
    """Parse exactly two unique, complete medal names from command text."""
    groups = parse_medal_names(raw_text, medal_index)
    if groups is None or len(groups) != DETAILED_GROUP_COUNT:
        return None
    return groups[0], groups[1]


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


def _calculate_detailed_direction(
    base: FanSnapshot,
    other: FanSnapshot,
) -> DetailedDirectionStats:
    """Calculate overlap buckets with ``base`` as the percentage denominator."""
    common_ids = frozenset(base.medal_levels) & frozenset(other.medal_levels)
    level_counts = tuple(
        sum(
            lower <= base.medal_levels[fan_id] <= upper
            for fan_id in common_ids
        )
        for lower, upper in LEVEL_BUCKETS
    )
    guard_counts = tuple(
        sum(base.guard_levels.get(fan_id) == guard_level for fan_id in common_ids)
        for _, guard_level in GUARD_TIERS
    )
    return DetailedDirectionStats(
        base_total=len(base.medal_levels),
        intersection_count=len(common_ids),
        level_counts=level_counts,
        guard_counts=guard_counts,
    )


def calculate_detailed_overlap(
    first: FanSnapshot,
    second: FanSnapshot,
) -> DetailedOverlapStats:
    """Calculate directional level/guard buckets and shared non-zero guards."""
    first_ids = frozenset(first.medal_levels)
    second_ids = frozenset(second.medal_levels)
    common_ids = first_ids & second_ids
    shared_guard_count = sum(
        first.guard_levels.get(fan_id, 0) == second.guard_levels.get(fan_id, 0) != 0
        for fan_id in common_ids
    )
    return DetailedOverlapStats(
        first=_calculate_detailed_direction(first, second),
        second=_calculate_detailed_direction(second, first),
        shared_guard_count=shared_guard_count,
    )


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


def _format_count_percentage(count: int, total: int) -> str:
    percentage = 0.0 if total == 0 else count / total * 100
    return f"{count} {percentage:.2f}%"


def format_detailed_overlap_results(
    first: FanGroup,
    second: FanGroup,
    stats: DetailedOverlapStats,
) -> str:
    """Render detailed bidirectional overlap statistics for two fan groups."""
    lines = [
        "粉丝团查重详细",
        f"{first.medal}总数：{stats.first.base_total}",
        f"{second.medal}总数：{stats.second.base_total}",
        (
            f"{first.medal}&{second.medal}："
            f"{_format_count_percentage(stats.first.intersection_count, stats.first.base_total)}"
        ),
        (
            f"{second.medal}&{first.medal}："
            f"{_format_count_percentage(stats.second.intersection_count, stats.second.base_total)}"
        ),
    ]
    lines.append(DETAIL_SEPARATOR)
    lines.extend(
        (
            f"{first.medal}&{second.medal} {lower}~{upper}级："
            f"{_format_count_percentage(count, stats.first.base_total)}"
        )
        for (lower, upper), count in zip(LEVEL_BUCKETS, stats.first.level_counts, strict=True)
        if count > 0
    )
    lines.append(DETAIL_SEPARATOR)
    lines.extend(
        (
            f"{second.medal}&{first.medal} {lower}~{upper}级："
            f"{_format_count_percentage(count, stats.second.base_total)}"
        )
        for (lower, upper), count in zip(LEVEL_BUCKETS, stats.second.level_counts, strict=True)
        if count > 0
    )
    lines.append(DETAIL_SEPARATOR)
    lines.extend(
        (
            f"{first.medal}&{second.medal} {label}："
            f"{_format_count_percentage(count, stats.first.base_total)}"
        )
        for (label, _), count in zip(GUARD_TIERS, stats.first.guard_counts, strict=True)
        if count > 0
    )
    lines.extend(
        (
            f"{second.medal}&{first.medal} {label}："
            f"{_format_count_percentage(count, stats.second.base_total)}"
        )
        for (label, _), count in zip(GUARD_TIERS, stats.second.guard_counts, strict=True)
        if count > 0
    )
    shared_guard_line = (
        f"{first.medal}&{second.medal}共同上舰："
        f"{_format_count_percentage(stats.shared_guard_count, stats.first.base_total)}"
    )
    lines.append(shared_guard_line)
    lines.append(DETAIL_EXPLANATION_SEPARATOR)
    level_explanation = (
        f"{first.medal}&{second.medal} 1~10级："
        f"{first.medal}中拥有{second.medal}牌子且{first.medal}为1~10级"
    )
    guard_explanation = (
        f"{first.medal}&{second.medal} 舰长："
        f"{first.medal}中拥有{second.medal}牌子且为{first.medal}舰长"
    )
    lines.extend(
        (
            f"{first.medal}&{second.medal}：{first.medal}中拥有{second.medal}牌子占{first.medal}的比重",
            level_explanation,
            guard_explanation,
            "共同上舰：两者均有上舰（不论等级）",
        )
    )
    return "\n".join(lines)
