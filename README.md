# Running Page · viazure

个人跑步主页：**[run.viazure.cc](https://run.viazure.cc)**

本仓库 fork 自 [yihong0618/running_page](https://github.com/yihong0618/running_page)。数据同步（Garmin / Keep / Strava / Nike 等）、部署（GitHub Pages / Vercel）、GitHub Actions 配置等通用用法，请直接看 [上游 README](https://github.com/yihong0618/running_page#readme)，这里只记录本 fork 的改动。

## 本 fork 的主要改动

### 1. `dashboard_pro` 主题

自包含的新主题（`src/themes/dashboard_pro`），不影响上游原有主题：

- 仪表盘式首页：个人资料卡、统计卡片、贡献热力图（动态色阶）、双日历视图、个人最佳、趋势图、活动日志与活动列表
- 地图：路线地图与轨迹页，路线自动适配视野、轨迹回放动画、3D 追随视角；无 GPS 的活动可复用上一条路线展示
- 汇总页、中国地图、页眉页脚与中英文本地化
- 主题偏好与上游 dashboard 默认值隔离；前端 chunk 加载失败时自动恢复

### 2. 每次活动的分段分析弹层

首页活动卡片上有分段数据的活动会出现入口，打开后显示：

- 摘要：距离、时间、配速、心率、步频、步幅、功率、爬升、训练效果等（副标题里带出有氧训练效果）
- 每公里配速条 + 分段表（按公里 / 按圈切换）
- 配速、心率、步频、步幅、功率、爬升（海拔剖面 + 爬升/下降 + 最高海拔）、跑步动态（触地时间、垂直振幅、垂直步幅比）等趋势图
- 心率区间（优先使用设备配置的区间，否则按最大心率估算）、配速区间（优先 FIT 速度区间，边界显示为 `5'00"` 而不是秒/公里数字；否则按阈值配速估算并标「估算」；按时长而不是采样点数）
- 仅在 FIT 含户外/天气温度时显示气温；手表传感器温度不展示（不标成「温度」也不标成「表温」）

数据源与可用字段：

| 来源                                         | 可显示                                                                         |
| -------------------------------------------- | ------------------------------------------------------------------------------ |
| FIT（Garmin 等，`FIT_OUT/`）                 | 全部字段：分段、圈、步频、步幅、功率、跑步动态、设备心率区间、训练效果、负荷等 |
| GPX / TCX（如 Keep，`GPX_OUT/`、`TCX_OUT/`） | 每公里配速、心率、爬升、估算心率/配速区间；文件里有步频/功率时也会显示         |

同一活动同时有多种文件时优先级为 FIT > TCX > GPX；缺失的字段在弹层中直接隐藏。GPX/TCX 没有暂停事件，超过 30 秒且几乎没有移动的间隔按暂停处理。

### 3. 其他

- Garmin 中国区同步：导入 FIT 中的 GPS，修正开始时间解析等
- 隐私模式：关灯地图 + 匿名活动标题，可在 `config.yml` 开关；详见下方「隐私」

## 生成分段数据

```bash
pip install garmin-fit-sdk            # 仅解析 FIT 需要；GPX/TCX 用标准库
python run_page/gen_splits.py         # 扫描 FIT_OUT、TCX_OUT、GPX_OUT，增量生成
python run_page/gen_splits.py --force # 全部重建
python run_page/gen_splits.py --fit-only
python run_page/gen_splits.py --file path/to/activity.fit  # 单个文件输出到终端
```

输出为 `public/splits/{run_id}.json` 和 `public/splits/index.json`。`run_id` 与 `src/static/activities.json` 对应：FIT 按开始时间（毫秒）；Keep 等以活动 id 命名的 GPX/TCX 按文件名，否则按开始时间。GitHub Actions 同步数据后会自动运行该脚本。

测试：`python -m pytest test_gen_splits.py`

## 隐私

### 隐私模式

公开站默认开启（`config.yml` 里 `privacy_mode: true`），避免把真实路线位置和活动名暴露给访客：

- **关灯地图**：关闭底图瓦片，只保留轨迹线（隐私开启时也不提供 3D）
- **匿名标题**（`privacy_anonymous_titles: true`）：活动名换成时段标题，如「清晨跑步」「傍晚跑步」「夜间跑步」；半马 / 全马、骑行等按距离与类型显示

永久关闭：`privacy_mode: false`（始终显示真实底图与原活动名）。只关灯、保留原标题可设 `privacy_anonymous_titles: false`。

### 分段数据

- 分段文件只含聚合后的统计和降采样曲线，**不含 GPS 坐标**，也没有逐秒原始数据
- 在本地或自己的 Actions 中生成，不上传到任何第三方

## License

沿用上游 [MIT License](LICENSE)。
