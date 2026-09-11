"""Rendering for the configured fan-medal room list."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from .core import FanGroup


def format_room_list(groups: Sequence[FanGroup]) -> str:
    """Render each configured broadcaster name and fan-medal name."""
    lines = ["当前可查："]
    lines.extend(f"{group.name} {group.medal}" for group in groups)
    return "\n".join(lines)
