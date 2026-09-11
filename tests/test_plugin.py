import nonebot_plugin_bili_fans_overlap as plugin


def test_plugin_metadata_and_command_registration() -> None:
    assert plugin.__plugin_meta__.name == "B站粉丝团查重"
    assert plugin.__plugin_meta__.usage == (
        "/粉丝团查重 小礼猫 酷萨 音悦生\n"
        "/粉丝团查重详细 小礼猫 酷萨"
    )
    assert plugin.fans_overlap.type == "message"
    assert plugin.fans_overlap.priority == 5
    assert plugin.fans_overlap.block
    assert plugin.fans_overlap_detailed.type == "message"
    assert plugin.fans_overlap_detailed.priority == 5
    assert plugin.fans_overlap_detailed.block
