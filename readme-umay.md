## 1. nRF connect APP 导出的 CSV 里能读出跑步机哪些信息

**设备身份**
- 广播名 `Umay-A7H-0E2905`，标准 FTMS（蓝牙健身设备协议，服务 0x1826）跑步机，广播间隔约 50 ms。
- 厂商 "YM"，固件 V83.61.02，硬件/软件 V1.0.1，序列号 25192F025054。
- 还有厂商私有服务 FFF0/FFF3（订阅了但整段日志没出数据）和一个私有 128 位特征，用不上。

**每秒一帧的数据（2ACD，空闲时也是 1 Hz）**

| 有 | 说明 |
|---|---|
| 速度 | 0.01 km/h 精度，加减速以 0.1 km/h 为步长 |
| 累计距离 | 米，10 m 一跳 |
| 坡度 | 0.1%，你这两次最高 20%（第一次）和 4%（第二次） |
| 累计卡路里 | 跑步机自己估的 |
| 已用时间 | 秒 |
| 心率 | 大半是 0，偶发 60–79，跑 12–15 km/h 不可能是真心率，多半是抓手传感器噪声 |

没有：步频、步数、功率、爬升（恒为 0）、每小时/每分钟热量（恒为 0）、GPS。

**状态事件（2ADA）**：开始、停止、Reset、目标速度变化、目标坡度变化。

**这台机器的几个关键行为**，都是按真实数据看出来的：
1. 计数器是"自上次 Reset 起累计"，不是每次开跑清零。第一次开跑前就带着 360 m / 125 s / 18 kcal 的残值，所以必须记基线、用相对值。
2. 按"停止"其实是暂停，计数器不清零。第二次跑中间停了 17 秒又接着跑，总共还是一次。真正的结束标志是停止约 17 秒后跑步机发的 Reset。
3. 两次跑步的汇总：

| | 开始 | 距离 | 用时 | 配速 | 最高速度 | 热量 |
|---|---|---|---|---|---|---|
| 第 1 次 | 18:25 | 220 m | 72 s | 5:27 | 15.0 km/h | 12 kcal |
| 第 2 次 | 18:32 | 190 m | 95 s（含暂停） | 8:20 | 8.5 km/h | 9 kcal |

这和你 running_page 上那两条记录（0.2 km、1m、5:27、8:20）完全吻合。也就是说这两次已经通过别的途径进了 Garmin CN，见下面"注意"。

**CSV 的局限**：它只给约 20% 的通知记了数值（Treadmill Data 861 次里只有 176 次有值）；时间没有日期；型号字符串读了 4 次但没记值。

## 2. 自启 + 常驻 + 生成 FIT + 推送 Garmin CN

可以做，但有一点要先说清：**Garmin Connect 只接受文件上传，没有实时推送接口**。所以"实时"只能是实时采集、实时落盘，每次跑完立即生成 FIT 并上传。

交付了 4 个文件：`treadmill2garmin.py`（主脚本，自带 FIT 编码器，只依赖 `bleak` 和 `garth`）、`treadmill2garmin.service`、`treadmill2garmin.env.example`、`requirements.txt`。

**部署（需要有蓝牙的 Linux 服务器，树莓派即可；WSL 没有蓝牙）：**
```bash
sudo apt install -y python3-venv bluez
sudo useradd -r -s /usr/sbin/nologin -G bluetooth treadmill
sudo mkdir -p /opt/treadmill2garmin && sudo cp treadmill2garmin.py requirements.txt /opt/treadmill2garmin/
cd /opt/treadmill2garmin && sudo python3 -m venv .venv && sudo .venv/bin/pip install -r requirements.txt
sudo cp treadmill2garmin.env.example /etc/treadmill2garmin.env
sudo chmod 600 /etc/treadmill2garmin.env && sudo nano /etc/treadmill2garmin.env   # 填 GARMIN_SECRET_STRING_CN
sudo cp treadmill2garmin.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now treadmill2garmin
journalctl -u treadmill2garmin -f
```
secret 就是你之前用 `get_garmin_secret.py ... --is-cn` 生成的那串。

**上线前先验证（强烈建议）**，用你这份 CSV 在任何机器上都能跑，不需要蓝牙：
```bash
python treadmill2garmin.py replay 你的.csv --date 2026-10-03 --out ./out
python treadmill2garmin.py fitinfo ./out/xxx.fit
```

**用到的最佳实践**
- 会话状态机的时间戳由外部传入，实时和回放走同一份代码。
- 每秒采样先写 journal 再处理，崩溃或断电后重启能恢复未完成的会话。
- FIT 先原子写盘，并用内置解码器校验 CRC 通过后才放进 outbox。
- 上传在独立线程，失败按指数退避重试，重启后继续传。Garmin 返回 409（重复）视为成功。
- 蓝牙断线用指数退避加抖动重连。跑步机连空闲时都 1 Hz 发数据，所以 20 秒没数据就判定为"僵尸连接"并强制重连。
- 密钥只走 `EnvironmentFile`（权限 0600），不进命令行。
- systemd 用非 root 用户运行，带加固选项，收到 SIGTERM 会先结束当前会话再退出。

## 注意

- **没法替你验证的部分**：沙箱里没有蓝牙硬件，也不能联网。蓝牙层我用假 bleak 测了重连和会话逻辑，真实的 `bleak` 连接和 `garth` 上传调用没实测。FIT 字段编号是我按 FIT 规范手写的，只做了自带解码器往返、CRC 和上面的数值对账，没有过 Garmin 官方 SDK。**第一次真跑完后，先在 Garmin Connect 网页手动导入一份 FIT 确认没问题，再打开自动上传**（调试时设 `T2G_NO_UPLOAD=1` 只生成不上传）。
- **重复上传风险**：这两次现在已经在 Garmin CN 里了，说明有别的途径（手表或 App）在上传。如果同时开脚本，同一次跑步可能出现两条。选一个来源，另一个关掉。
- **蓝牙单连接**：FTMS 设备一般同一时间只允许一个主机连接，我无法从日志确认这台是否如此。服务常驻连着的话，手机 nRF、App 或手表就连不上，要用时先 `systemctl stop treadmill2garmin`。
- 服务器要放在跑步机附近（BLE 约 10 米内）；卡路里是跑步机按它自己的算法估的，没有你的体重；心率默认只在有效采样占比 ≥50% 时才写入。
- 数据进 Garmin CN 后，你现有的 running_page 每天的 Actions 同步会自动把它们拉到网站上，不用改任何东西。

  
