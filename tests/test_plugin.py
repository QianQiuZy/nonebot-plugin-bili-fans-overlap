import anyio
import nonebot_plugin_bili_fans_overlap as plugin
from nonebot.adapters.onebot.v11 import GroupMessageEvent, MessageSegment


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


class _RecordingBot:
    self_id: str

    def __init__(self) -> None:
        self.self_id = "456"
        self.calls: list[tuple[str, dict[str, object]]] = []

    async def call_api(self, api: str, **data: object) -> object:
        self.calls.append((api, data))
        if api == "send_private_msg":
            return {"message_id": 9001}
        return {}


def test_detailed_forward_sends_to_bot_self_before_group_forward() -> None:
    async def run() -> None:
        bot = _RecordingBot()
        event = GroupMessageEvent.model_construct(group_id=123)

        await plugin.send_detailed_forward(bot, event, "统计内容")

        assert bot.calls[0] == (
            "send_private_msg",
            {"user_id": 456, "message": "统计内容"},
        )
        assert bot.calls[1][0] == "send_forward_msg"
        assert bot.calls[1][1]["group_id"] == 123
        assert bot.calls[1][1]["messages"] == [MessageSegment.node(9001)]

    anyio.run(run)
