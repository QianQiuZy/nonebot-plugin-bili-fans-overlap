"""NoneBot entry point for B站 fan-medal overlap queries."""

# pyright: reportUnknownMemberType=false

from itertools import combinations
from pathlib import Path
from typing import Annotated, Final

from nonebot import get_plugin_config, on_command
from nonebot.adapters.onebot.v11 import Message
from nonebot.matcher import Matcher
from nonebot.params import CommandArg
from nonebot.plugin import PluginMetadata

from .api import FansCacheError, fetch_fan_ids, fetch_fan_snapshots
from .config import Config
from .core import (
    DETAILED_INVALID_INPUT_MESSAGE,
    INVALID_INPUT_MESSAGE,
    FanGroup,
    FanIds,
    OverlapPair,
    build_medal_index,
    calculate_detailed_overlap,
    calculate_overlap_percentage,
    format_detailed_overlap_results,
    format_overlap_results,
    load_rooms,
    parse_medal_names,
    parse_two_medal_names,
)

__plugin_meta__ = PluginMetadata(
    name="B站粉丝团查重",
    description="查询多个 B 站粉丝团之间的 UID 重合率。",
    usage="/粉丝团查重 小礼猫 酷萨 音悦生\n/粉丝团查重详细 小礼猫 酷萨",
    type="application",
    config=Config,
)

_ROOMS_FILE: Final = Path(__file__).with_name("rooms.json")
_ROOMS: Final[tuple[FanGroup, ...]] = load_rooms(_ROOMS_FILE)
_MEDAL_INDEX = build_medal_index(_ROOMS)

fans_overlap = on_command(
    "粉丝团查重",
    force_whitespace=True,
    priority=5,
    block=True,
)
fans_overlap_detailed = on_command(
    "粉丝团查重详细",
    force_whitespace=True,
    priority=5,
    block=True,
)


@fans_overlap.handle()
async def _(
    matcher: Matcher,
    args: Annotated[Message, CommandArg()],
) -> None:
    """Handle a pairwise fan-medal overlap query."""
    groups = parse_medal_names(args.extract_plain_text(), _MEDAL_INDEX)
    if groups is None:
        await matcher.finish(INVALID_INPUT_MESSAGE)

    config = get_plugin_config(Config)
    try:
        fan_ids = await fetch_fan_ids(
            groups,
            config.bili_fans_overlap_api_base,
            config.bili_fans_overlap_http_timeout,
        )
    except FansCacheError:
        await matcher.finish("粉丝团缓存查询失败，请稍后再试")

    group_fans: tuple[tuple[FanGroup, FanIds], ...] = tuple(
        zip(groups, fan_ids, strict=True)
    )
    totals = tuple((group.medal, len(ids)) for group, ids in group_fans)
    pairs: list[OverlapPair] = []
    for (left_group, left_ids), (right_group, right_ids) in combinations(group_fans, 2):
        pairs.extend(
            (
                (
                    left_group.medal,
                    right_group.medal,
                    calculate_overlap_percentage(left_ids, right_ids),
                ),
                (
                    right_group.medal,
                    left_group.medal,
                    calculate_overlap_percentage(right_ids, left_ids),
                ),
            )
    )
    await matcher.finish(format_overlap_results(totals, pairs))


@fans_overlap_detailed.handle()
async def _(
    matcher: Matcher,
    args: Annotated[Message, CommandArg()],
) -> None:
    """Handle a detailed two-medal overlap query."""
    groups = parse_two_medal_names(args.extract_plain_text(), _MEDAL_INDEX)
    if groups is None:
        await matcher.finish(DETAILED_INVALID_INPUT_MESSAGE)

    config = get_plugin_config(Config)
    try:
        snapshots = await fetch_fan_snapshots(
            groups,
            config.bili_fans_overlap_api_base,
            config.bili_fans_overlap_http_timeout,
        )
    except FansCacheError:
        await matcher.finish("粉丝团缓存查询失败，请稍后再试")

    stats = calculate_detailed_overlap(snapshots[0], snapshots[1])
    await matcher.finish(format_detailed_overlap_results(groups[0], groups[1], stats))
