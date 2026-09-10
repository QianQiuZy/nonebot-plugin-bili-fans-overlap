# nonebot-plugin-bili-fans-overlap

NoneBot2 插件：查询 B 站粉丝团之间的 UID 重合率。

## 使用

```text
/粉丝团查重 小礼猫 酷萨 音悦生
```

一次最多查询 5 个粉丝团。名称必须与插件内 `rooms.json` 中的 `medal` 完全一致，至少输入 2 个名称。

结果按方向分别计算：`A&B` 表示 B 与 A 的交集占 A 的比例，即交集 UID 数除以 A 的 UID 数，并保留两位小数。同一对粉丝团会输出两个方向：

```text
粉丝团重合查询
小礼猫&酷萨：33.33%
酷萨&小礼猫：35.33%
```

## 配置

在 NoneBot 宿主的 `.env` 中可配置：

```dotenv
BILI_FANS_OVERLAP_API_BASE=https://fans.harei.cn
BILI_FANS_OVERLAP_HTTP_TIMEOUT=10
```

插件会请求 bilifanscache 的 `/fans?room_id=<room_id>` 接口获取缓存的粉丝 UID。
