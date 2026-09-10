# nonebot-plugin-bili-fans-overlap

NoneBot2 插件：查询 B 站粉丝团之间的 UID 重合率。

## 使用

```text
/粉丝团查重 小礼猫 酷萨 音悦生
```

一次最多查询 5 个粉丝团。名称必须与插件内 `rooms.json` 中的 `medal` 完全一致，至少输入 2 个名称。

重合率按两个粉丝 UID 集合的交集除以并集计算，并保留两位小数。

## 配置

在 NoneBot 宿主的 `.env` 中可配置：

```dotenv
BILI_FANS_OVERLAP_API_BASE=https://fans.harei.cn
BILI_FANS_OVERLAP_HTTP_TIMEOUT=10
```

插件会请求 bilifanscache 的 `/fans?room_id=<room_id>` 接口获取缓存的粉丝 UID。
