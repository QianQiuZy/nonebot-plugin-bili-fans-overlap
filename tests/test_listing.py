from nonebot_plugin_bili_fans_overlap.core import FanGroup, RoomId, UserId
from nonebot_plugin_bili_fans_overlap.listing import format_room_list


def test_format_room_list_renders_name_and_medal_in_input_order() -> None:
    groups = (
        FanGroup(RoomId(1), UserId(1), "花礼Harei", "小礼猫"),
        FanGroup(RoomId(2), UserId(2), "阿萨AzA", "酷萨"),
    )

    assert format_room_list(groups) == "当前可查：\n花礼Harei 小礼猫\n阿萨AzA 酷萨"
