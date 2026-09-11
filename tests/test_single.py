from nonebot_plugin_bili_fans_overlap.core import (
    LEVEL_BUCKETS,
    FanGroup,
    FanId,
    FanSnapshot,
    RoomId,
    UserId,
    build_medal_index,
)
from nonebot_plugin_bili_fans_overlap.single import (
    calculate_single_details,
    format_single_details,
    parse_single_medal_name,
)


def test_parse_single_medal_name_requires_one_complete_name() -> None:
    groups = (
        FanGroup(RoomId(1), UserId(1), "主播1", "小礼猫"),
        FanGroup(RoomId(2), UserId(2), "主播2", "酷萨"),
    )
    medal_index = build_medal_index(groups)

    assert parse_single_medal_name("小礼猫", medal_index) == groups[0]
    assert parse_single_medal_name("小礼猫 酷萨", medal_index) is None
    assert parse_single_medal_name("未知", medal_index) is None


def test_format_single_details_uses_total_and_guard_denominators() -> None:
    group = FanGroup(RoomId(1), UserId(1), "主播1", "小礼猫")
    snapshot = FanSnapshot(
        medal_levels={
            FanId(1): 1,
            FanId(2): 10,
            FanId(3): 11,
            FanId(4): 21,
            FanId(5): 61,
            FanId(6): 10,
        },
        guard_levels={FanId(1): 3, FanId(2): 2, FanId(3): 1},
    )

    stats = calculate_single_details(snapshot)

    assert stats.base_total == 6
    assert stats.level_counts[:3] == (3, 1, 1)
    assert len(stats.level_counts) == len(LEVEL_BUCKETS) == 6
    assert stats.guard_counts == (1, 1, 1)
    assert format_single_details(group, stats) == (
        "粉丝团详细\n"
        "小礼猫总数：6\n"
        "1~10级：3 50.00%\n"
        "11~20级：1 16.67%\n"
        "21~30级：1 16.67%\n"
        "上舰总数：3 50.00%\n"
        "舰长总数：1 33.33%\n"
        "提督总数：1 33.33%\n"
        "总督总数：1 33.33%"
    )


def test_format_single_details_hides_zero_rows() -> None:
    group = FanGroup(RoomId(1), UserId(1), "主播1", "小礼猫")
    snapshot = FanSnapshot(medal_levels={FanId(1): 1}, guard_levels={})

    output = format_single_details(group, calculate_single_details(snapshot))

    assert output == "粉丝团详细\n小礼猫总数：1\n1~10级：1 100.00%"
