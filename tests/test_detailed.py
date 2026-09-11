from nonebot_plugin_bili_fans_overlap.core import (
    DETAILED_INVALID_INPUT_MESSAGE,
    LEVEL_BUCKETS,
    FanGroup,
    FanId,
    FanSnapshot,
    RoomId,
    UserId,
    build_medal_index,
    calculate_detailed_overlap,
    format_detailed_overlap_results,
    parse_two_medal_names,
)


def test_parse_two_medal_names_rejects_anything_but_two_names() -> None:
    groups = (
        FanGroup(RoomId(1), UserId(1), "主播1", "小礼猫"),
        FanGroup(RoomId(2), UserId(2), "主播2", "酷萨"),
        FanGroup(RoomId(3), UserId(3), "主播3", "音悦生"),
    )
    medal_index = build_medal_index(groups)

    result = parse_two_medal_names("小礼猫 酷萨", medal_index)

    assert result == groups[:2]
    assert parse_two_medal_names("小礼猫", medal_index) is None
    assert parse_two_medal_names("小礼猫 酷萨 音悦生", medal_index) is None
    assert DETAILED_INVALID_INPUT_MESSAGE == "详细查重仅支持两个完整粉丝团名称"


def test_calculate_detailed_overlap_uses_directional_denominators() -> None:
    first = FanSnapshot(
        medal_levels={
            FanId(1): 5,
            FanId(2): 15,
            FanId(3): 25,
            FanId(4): 35,
            FanId(5): 45,
            FanId(6): 55,
        },
        guard_levels={FanId(1): 3, FanId(2): 2, FanId(3): 1, FanId(5): 3},
    )
    second = FanSnapshot(
        medal_levels={FanId(1): 2, FanId(2): 12, FanId(3): 22, FanId(7): 32},
        guard_levels={FanId(1): 3, FanId(2): 1, FanId(3): 1, FanId(7): 2},
    )

    result = calculate_detailed_overlap(first, second)

    assert result.first.intersection_count == 3
    assert result.second.intersection_count == 3
    assert result.first.level_counts[:3] == (1, 1, 1)
    assert result.second.level_counts[:3] == (1, 1, 1)
    assert result.first.guard_counts == (1, 1, 1)
    assert result.second.guard_counts == (1, 0, 2)
    assert result.shared_guard_count == 2
    assert len(result.first.level_counts) == len(LEVEL_BUCKETS) == 6


def test_format_detailed_overlap_results_renders_all_requested_buckets() -> None:
    first = FanGroup(RoomId(1), UserId(1), "主播1", "小礼猫")
    second = FanGroup(RoomId(2), UserId(2), "主播2", "酷萨")
    snapshot = FanSnapshot(medal_levels={FanId(1): 1}, guard_levels={FanId(1): 3})
    result = calculate_detailed_overlap(snapshot, snapshot)

    output = format_detailed_overlap_results(first, second, result)

    assert output == (
        "粉丝团查重详细\n"
        "小礼猫总数：1\n"
        "酷萨总数：1\n"
        "小礼猫&酷萨：1 100.00%\n"
        "酷萨&小礼猫：1 100.00%\n"
        "小礼猫&酷萨 1~10级：1 100.00%\n"
        "酷萨&小礼猫 1~10级：1 100.00%\n"
        "小礼猫&酷萨 舰长：1 100.00%\n"
        "酷萨&小礼猫 舰长：1 100.00%\n"
        "小礼猫&酷萨共同上舰：1 100.00%\n"
        "小礼猫&酷萨：小礼猫中拥有酷萨牌子占小礼猫的比重\n"
        "小礼猫&酷萨 1~10级：小礼猫中拥有酷萨牌子且小礼猫为1~10级\n"
        "小礼猫&酷萨 舰长：小礼猫中拥有酷萨牌子且为小礼猫舰长\n"
        "共同上舰：两者均有上舰（不论等级）"
    )


def test_format_detailed_overlap_results_keeps_required_zero_lines() -> None:
    first = FanGroup(RoomId(1), UserId(1), "主播1", "小礼猫")
    second = FanGroup(RoomId(2), UserId(2), "主播2", "酷萨")
    first_snapshot = FanSnapshot(medal_levels={FanId(1): 1}, guard_levels={})
    second_snapshot = FanSnapshot(medal_levels={FanId(2): 1}, guard_levels={})
    result = calculate_detailed_overlap(first_snapshot, second_snapshot)

    output = format_detailed_overlap_results(first, second, result)

    assert "小礼猫&酷萨：0 0.00%" in output
    assert "酷萨&小礼猫：0 0.00%" in output
    assert "小礼猫&酷萨共同上舰：0 0.00%" in output
    assert [line for line in output.splitlines() if line.endswith("：0 0.00%")] == [
        "小礼猫&酷萨：0 0.00%",
        "酷萨&小礼猫：0 0.00%",
        "小礼猫&酷萨共同上舰：0 0.00%"
    ]
    assert "小礼猫&酷萨：小礼猫中拥有酷萨牌子占小礼猫的比重" in output
    assert "小礼猫&酷萨 1~10级：小礼猫中拥有酷萨牌子且小礼猫为1~10级" in output
    assert "小礼猫&酷萨 舰长：小礼猫中拥有酷萨牌子且为小礼猫舰长" in output
    assert "共同上舰：两者均有上舰（不论等级）" in output
