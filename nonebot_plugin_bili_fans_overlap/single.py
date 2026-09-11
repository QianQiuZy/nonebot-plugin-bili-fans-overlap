"""Single fan-medal detail calculations and rendering."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from .core import GUARD_TIERS, LEVEL_BUCKETS, FanGroup, FanSnapshot

if TYPE_CHECKING:
    from collections.abc import Mapping

SINGLE_DETAILED_INVALID_INPUT_MESSAGE: Final = "详细查询仅支持一个完整粉丝团名称"


@dataclass(frozen=True, slots=True)
class SingleDetailsStats:
    """Level and guard statistics for one fan-medal snapshot."""

    base_total: int
    level_counts: tuple[int, ...]
    guard_counts: tuple[int, ...]


def parse_single_medal_name(
    raw_text: str,
    medal_index: Mapping[str, tuple[FanGroup, ...]],
) -> FanGroup | None:
    """Parse exactly one complete, unambiguous medal name."""
    names = tuple(raw_text.split())
    if len(names) != 1:
        return None
    matches = medal_index.get(names[0])
    if matches is None or len(matches) != 1:
        return None
    return matches[0]


def calculate_single_details(snapshot: FanSnapshot) -> SingleDetailsStats:
    """Calculate level buckets and non-zero guard tiers for one snapshot."""
    level_counts = tuple(
        sum(lower <= level <= upper for level in snapshot.medal_levels.values())
        for lower, upper in LEVEL_BUCKETS
    )
    guard_counts = tuple(
        sum(snapshot.guard_levels.get(fan_id) == guard_level for fan_id in snapshot.medal_levels)
        for _, guard_level in GUARD_TIERS
    )
    return SingleDetailsStats(
        base_total=len(snapshot.medal_levels),
        level_counts=level_counts,
        guard_counts=guard_counts,
    )


def _format_count_percentage(count: int, total: int) -> str:
    percentage = 0.0 if total == 0 else count / total * 100
    return f"{count} {percentage:.2f}%"


def format_single_details(group: FanGroup, stats: SingleDetailsStats) -> str:
    """Render one fan-medal's levels and guard statistics."""
    lines = [
        "粉丝团详细",
        f"{group.medal}总数：{stats.base_total}",
    ]
    lines.extend(
        f"{lower}~{upper}级：{_format_count_percentage(count, stats.base_total)}"
        for (lower, upper), count in zip(LEVEL_BUCKETS, stats.level_counts, strict=True)
        if count > 0
    )
    guard_total = sum(stats.guard_counts)
    if guard_total > 0:
        lines.append(f"上舰总数：{_format_count_percentage(guard_total, stats.base_total)}")
        lines.extend(
            f"{label}总数：{_format_count_percentage(count, guard_total)}"
            for (label, _), count in zip(GUARD_TIERS, stats.guard_counts, strict=True)
            if count > 0
        )
    return "\n".join(lines)
