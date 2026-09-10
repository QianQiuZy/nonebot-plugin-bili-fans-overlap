import pytest
from nonebot_plugin_bili_fans_overlap.core import (
    INVALID_INPUT_MESSAGE,
    FanGroup,
    FanId,
    RoomId,
    UserId,
    build_medal_index,
    calculate_overlap_percentage,
    format_overlap_results,
    parse_medal_names,
)


def test_parse_medal_names_accepts_two_to_five_complete_names() -> None:
    groups = tuple(
        FanGroup(RoomId(index), UserId(index), f"主播{index}", name)
        for index, name in enumerate(("小礼猫", "酷萨", "音悦生", "第四", "第五"), 1)
    )
    rooms = build_medal_index(groups)

    result = parse_medal_names("小礼猫 酷萨 音悦生", rooms)
    assert result is not None
    assert tuple(group.room_id for group in result) == (1, 2, 3)

    result = parse_medal_names("小礼猫 酷萨 音悦生 第四 第五", rooms)
    assert result is not None
    assert tuple(group.room_id for group in result) == (1, 2, 3, 4, 5)


def test_parse_medal_names_rejects_incomplete_or_invalid_input() -> None:
    rooms = build_medal_index(
        (
            FanGroup(RoomId(1), UserId(1), "主播1", "小礼猫"),
            FanGroup(RoomId(2), UserId(2), "主播2", "酷萨"),
        )
    )

    assert parse_medal_names("", rooms) is None
    assert parse_medal_names("小礼猫", rooms) is None
    assert parse_medal_names("小礼 酷萨", rooms) is None
    assert parse_medal_names("小礼猫 酷萨 未知", rooms) is None
    assert parse_medal_names("小礼猫 酷萨 小礼猫", rooms) is None
    assert INVALID_INPUT_MESSAGE == "请输入完整粉丝团名称进行查重"


def test_parse_medal_names_rejects_more_than_five_names() -> None:
    rooms = build_medal_index(
        tuple(
            FanGroup(RoomId(index), UserId(index), f"主播{index}", str(index))
            for index in range(1, 7)
        )
    )

    assert parse_medal_names("1 2 3 4 5 6", rooms) is None


def test_calculate_overlap_percentage_measures_other_group_share() -> None:
    left = {FanId(101), FanId(102), FanId(103)}
    right = {FanId(102), FanId(103), FanId(104), FanId(105)}

    assert calculate_overlap_percentage(left, right) == pytest.approx(200 / 3)
    assert calculate_overlap_percentage(right, left) == 50.0
    assert calculate_overlap_percentage(set(), set()) == 0.0


def test_format_overlap_results_renders_both_directions_and_two_decimals() -> None:
    result = format_overlap_results(
        (
            ("小礼猫", "酷萨", 33.333),
            ("酷萨", "小礼猫", 35.333),
        ),
    )

    assert result == "粉丝团重合查询\n小礼猫&酷萨：33.33%\n酷萨&小礼猫：35.33%"
