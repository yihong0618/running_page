#!/usr/bin/env python3
"""treadmill2garmin —— 蓝牙跑步机 (FTMS) → FIT 文件 → Garmin Connect 中国区

工作方式
    1. 常驻后台, 用 bleak 连接跑步机, 订阅 FTMS 的 Treadmill Data(2ACD) 和 Machine Status(2ADA)
    2. 检测到开跑就开始记录 (每个采样实时写入 journal, 崩溃/断电不丢数据)
    3. 停止 / 空转超时 / 计数器清零 / 长时间无数据 → 结束会话, 生成 FIT 放进 outbox
    4. 后台上传线程把 outbox 里的 FIT 传到 Garmin CN (失败指数退避重试, 重启后继续传)

注意: Garmin Connect 只接受 "文件上传", 没有实时推送接口。这里的 "实时" 指实时采集 +
      实时落盘, 每次跑步结束后立刻生成并上传 FIT。

子命令
    run       常驻服务 (systemd 用这个)
    scan      扫描附近 BLE 设备, 找到跑步机的名字/地址
    replay    把 nRF Connect 导出的 CSV 回放成 FIT (不连蓝牙、不上传, 用来验证)
    upload    把 outbox 里待传的 FIT 上传一次后退出
    fitinfo   解析并打印一个 FIT 文件的摘要
    selftest  内置自检 (编码→解码往返)

依赖: pip install bleak garth   (Python >= 3.9)
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import json
import logging
import os
import random
import re
import signal
import socket
import struct
import sys
import time
from dataclasses import dataclass
from datetime import date as date_cls
from datetime import datetime, time as time_cls, tzinfo
from pathlib import Path
from typing import Callable, List, Optional, Tuple

log = logging.getLogger("t2g")


# ════════════════════════════ 配置 ════════════════════════════
def _env(name: str, default, cast=str):
    v = os.environ.get(name)
    return default if v is None or v == "" else cast(v)


def _truthy(v: str) -> bool:
    return str(v).strip().lower() in ("1", "true", "yes", "on")


@dataclass
class Cfg:
    device_name: str = "Umay-"        # 按广播名前缀匹配
    device_address: str = ""          # 指定后优先按地址匹配 (Linux 为 MAC)
    data_dir: Path = Path("./data")   # outbox/ uploaded/ journal/ 都在这里
    garmin_domain: str = "garmin.cn"
    tz: str = ""                      # 空 = 系统时区
    min_seconds: int = 30             # 短于此的会话丢弃 (防误触)
    min_meters: int = 20              # 短于此的会话丢弃
    idle_end_s: int = 60              # 速度为 0 (且未按停止) 持续这么久 → 结束
    pause_end_s: int = 90             # 按了停止后这么久没恢复也没收到 Reset → 结束
    gap_end_s: int = 60               # 这么久没收到数据 → 结束
    stale_s: int = 20                 # 已连接但这么久没数据 → 主动重连 (0 = 关闭)
    scan_timeout: float = 15.0
    hr_min_coverage: float = 0.5      # 有效心率占比低于此则不写心率 (抓手传感器常常大半是 0)
    no_upload: bool = False

    @classmethod
    def from_env(cls) -> "Cfg":
        return cls(
            device_name=_env("T2G_DEVICE_NAME", cls.device_name),
            device_address=_env("T2G_DEVICE_ADDRESS", ""),
            data_dir=Path(_env("T2G_DATA_DIR", "./data")),
            garmin_domain=_env("T2G_GARMIN_DOMAIN", cls.garmin_domain),
            tz=_env("T2G_TZ", ""),
            min_seconds=_env("T2G_MIN_SECONDS", cls.min_seconds, int),
            min_meters=_env("T2G_MIN_METERS", cls.min_meters, int),
            idle_end_s=_env("T2G_IDLE_END_S", cls.idle_end_s, int),
            pause_end_s=_env("T2G_PAUSE_END_S", cls.pause_end_s, int),
            gap_end_s=_env("T2G_GAP_END_S", cls.gap_end_s, int),
            stale_s=_env("T2G_STALE_S", cls.stale_s, int),
            scan_timeout=_env("T2G_SCAN_TIMEOUT", cls.scan_timeout, float),
            hr_min_coverage=_env("T2G_HR_MIN_COVERAGE", cls.hr_min_coverage, float),
            no_upload=_env("T2G_NO_UPLOAD", False, _truthy),
        )

    @property
    def outbox(self) -> Path:
        return self.data_dir / "outbox"

    @property
    def uploaded(self) -> Path:
        return self.data_dir / "uploaded"

    @property
    def journal(self) -> Path:
        return self.data_dir / "journal"

    def ensure_dirs(self) -> None:
        for d in (self.data_dir, self.outbox, self.uploaded, self.journal):
            d.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(self.data_dir, 0o700)
        except OSError:
            pass


def get_tz(name: str) -> tzinfo:
    if name:
        try:
            from zoneinfo import ZoneInfo
            return ZoneInfo(name)
        except Exception as e:  # tzdata 缺失等
            log.warning("timezone %r unavailable (%s), falling back to system tz", name, e)
    return datetime.now().astimezone().tzinfo  # type: ignore[return-value]


def load_secret() -> str:
    """Garmin 登录凭据 (get_garmin_secret.py 生成的字符串)。只从环境变量/文件读, 不进命令行。"""
    s = os.environ.get("GARMIN_SECRET_STRING_CN", "").strip()
    path = os.environ.get("T2G_SECRET_FILE", "").strip()
    if not s and path:
        s = Path(path).read_text(encoding="utf-8").strip()
    if not s:
        raise SystemExit("缺少 GARMIN_SECRET_STRING_CN (或 T2G_SECRET_FILE), 见 .env.example")
    return s


# ════════════════════════ FTMS 协议解析 ════════════════════════
def _uuid16(n: int) -> str:
    return f"{n:08x}-0000-1000-8000-00805f9b34fb"


FTMS_SERVICE = _uuid16(0x1826)
TREADMILL_DATA = _uuid16(0x2ACD)
MACHINE_STATUS = _uuid16(0x2ADA)


@dataclass
class Frame:
    """一帧 Treadmill Data。字段为 None 表示这帧里没有 / 无效。计数器是跑步机的绝对值。"""
    speed_kmh: Optional[float] = None
    distance_m: Optional[int] = None
    incline_pct: Optional[float] = None
    kcal: Optional[int] = None
    hr: Optional[int] = None
    elapsed_s: Optional[int] = None


class _Cur:
    def __init__(self, b: bytes, o: int):
        self.b, self.o = b, o

    def take(self, n: int) -> bytes:
        if self.o + n > len(self.b):
            raise ValueError("truncated treadmill data")
        v = self.b[self.o:self.o + n]
        self.o += n
        return v


def parse_treadmill_data(b: bytes) -> Frame:
    """按 FTMS 规范的 flags 动态解析 (不写死布局)。多余的尾部字节 (厂商扩展) 直接忽略。"""
    b = bytes(b)
    if len(b) < 2:
        raise ValueError("too short")
    flags = struct.unpack_from("<H", b, 0)[0]
    c, f = _Cur(b, 2), Frame()
    if not flags & 0x0001:                                    # bit0=0 → 带瞬时速度 (规范里是反的)
        f.speed_kmh = struct.unpack("<H", c.take(2))[0] / 100.0
    if flags & 0x0002:
        c.take(2)                                             # 平均速度
    if flags & 0x0004:
        f.distance_m = int.from_bytes(c.take(3), "little")    # 累计距离 (m)
    if flags & 0x0008:
        f.incline_pct = struct.unpack("<h", c.take(2))[0] / 10.0
        c.take(2)                                             # ramp angle
    if flags & 0x0010:
        c.take(4)                                             # 爬升 +/-
    if flags & 0x0020:
        c.take(1)                                             # 瞬时配速
    if flags & 0x0040:
        c.take(1)                                             # 平均配速
    if flags & 0x0080:
        kcal = struct.unpack("<H", c.take(2))[0]
        c.take(3)                                             # kcal/h + kcal/min
        f.kcal = None if kcal == 0xFFFF else kcal
    if flags & 0x0100:
        hr = c.take(1)[0]
        f.hr = hr if 0 < hr < 255 else None                   # 0 = 无信号
    if flags & 0x0200:
        c.take(1)                                             # MET
    if flags & 0x0400:
        f.elapsed_s = struct.unpack("<H", c.take(2))[0]
    return f


@dataclass
class Status:
    kind: str                     # reset / stop / pause / start / target_speed / target_incline / other
    value: Optional[float] = None


def parse_machine_status(b: bytes) -> Status:
    b = bytes(b)
    if not b:
        raise ValueError("empty status")
    op = b[0]
    if op == 0x01:
        return Status("reset")
    if op == 0x02:
        return Status("pause" if len(b) > 1 and b[1] == 0x02 else "stop")
    if op == 0x03:
        return Status("stop")                                  # 安全钥匙拔出
    if op == 0x04:
        return Status("start")
    if op == 0x05 and len(b) >= 3:
        return Status("target_speed", struct.unpack_from("<H", b, 1)[0] / 100.0)
    if op == 0x06 and len(b) >= 3:
        return Status("target_incline", struct.unpack_from("<h", b, 1)[0] / 10.0)
    return Status("other", op)


# ═══════════════════════ 会话数据 / 记录器 ═══════════════════════
@dataclass
class Sample:
    ts: float                     # unix 秒 (UTC)
    speed_mps: float
    dist_m: float                 # 相对本次会话起点
    incline: Optional[float]
    hr: Optional[int]
    kcal: Optional[int]           # 相对本次会话起点
    elapsed_s: Optional[int]      # 相对本次会话起点

    def to_json(self) -> str:
        return json.dumps([round(self.ts, 3), self.speed_mps, self.dist_m, self.incline,
                           self.hr, self.kcal, self.elapsed_s])

    @staticmethod
    def from_json(line: str) -> "Sample":
        a = json.loads(line)
        return Sample(*a)


PAUSE_GAP_S = 10


@dataclass
class Session:
    samples: List[Sample]

    @property
    def start_ts(self) -> float:
        return self.samples[0].ts

    @property
    def end_ts(self) -> float:
        return self.samples[-1].ts

    @property
    def distance_m(self) -> float:
        return max(s.dist_m for s in self.samples)

    @property
    def pauses(self) -> List[Tuple[float, float]]:
        """相邻采样间隔 > PAUSE_GAP_S 视为暂停 (暂停期间不记录采样)。从采样推导, 所以崩溃恢复后也在。"""
        return [(a.ts, b.ts) for a, b in zip(self.samples, self.samples[1:]) if b.ts - a.ts > PAUSE_GAP_S]

    @property
    def timer_s(self) -> float:
        e = self.samples[-1].elapsed_s
        if e:
            return float(e)                              # 跑步机自己的计时 (暂停时不走)
        paused = sum(b - a for a, b in self.pauses)
        return max(1.0, self.end_ts - self.start_ts - paused)

    @property
    def calories(self) -> Optional[int]:
        ks = [s.kcal for s in self.samples if s.kcal is not None]
        return max(ks) if ks else None

    @property
    def max_speed_mps(self) -> float:
        return max(s.speed_mps for s in self.samples)

    @property
    def avg_speed_mps(self) -> float:
        return self.distance_m / self.timer_s if self.timer_s else 0.0

    def hr_values(self, min_coverage: float) -> List[int]:
        vals = [s.hr for s in self.samples if s.hr]
        if not self.samples or len(vals) / len(self.samples) < min_coverage:
            return []
        return vals


class Journal:
    """进行中的会话逐条落盘 (jsonl)。进程崩溃/断电后可从这里恢复。"""

    def __init__(self, directory: Optional[Path]):
        self.dir = directory
        self.path: Optional[Path] = None
        self._fh = None
        self._last_sync = 0.0

    def open(self, sid: int) -> None:
        if self.dir is None:
            return
        self.path = self.dir / f"{sid}.jsonl"
        self._fh = open(self.path, "a", encoding="utf-8")

    def append(self, s: Sample) -> None:
        if self._fh is None:
            return
        self._fh.write(s.to_json() + "\n")
        self._fh.flush()
        now = time.monotonic()
        if now - self._last_sync > 15:                 # 每 15 秒 fsync 一次, 兼顾 SD 卡寿命
            os.fsync(self._fh.fileno())
            self._last_sync = now

    def close(self, delete: bool) -> None:
        if self._fh is not None:
            self._fh.close()
            self._fh = None
        if delete and self.path is not None:
            self.path.unlink(missing_ok=True)
        self.path = None

    @staticmethod
    def orphans(directory: Path) -> List[Tuple[Path, List[Sample]]]:
        out = []
        for p in sorted(directory.glob("*.jsonl")):
            samples: List[Sample] = []
            for line in p.read_text(encoding="utf-8").splitlines():
                try:
                    samples.append(Sample.from_json(line))
                except Exception:
                    break                               # 最后一行可能写了一半
            out.append((p, samples))
        return out


class SessionTracker:
    """把 (时间戳, 帧/状态) 变成一次次跑步会话。时间戳由调用方传入, 所以实时和回放共用同一份逻辑。

    跑步机计数器 (距离/时间/卡路里) 是 "自上次 Reset 起累计", 并不是每次开跑清零,
    所以起跑时记录基线, 之后一律用相对值。
    """

    def __init__(self, cfg: Cfg, sink: Callable[[Session], None], journal_dir: Optional[Path]):
        self.cfg, self.sink = cfg, sink
        self.journal = Journal(journal_dir)
        self.active = False
        self.samples: List[Sample] = []
        self._base: Optional[Frame] = None
        self._prev: Optional[Frame] = None
        self._last_rx = 0.0
        self._last_moving = 0.0
        self._stopping_since: Optional[float] = None
        self._paused_at: Optional[float] = None

    # ── 输入 ──
    def on_frame(self, ts: float, f: Frame) -> None:
        self._last_rx = ts
        if self.active and self._counters_reset(f):
            self._finish(self._paused_at or self._last_moving or ts, "counters reset")
        moving = (f.speed_kmh or 0.0) > 0.0
        if not self.active:
            if moving:
                self._start(ts, f)
            self._prev = f
            return
        if self._stopping_since is not None:           # 收到 stop 后的第一帧 = 暂停时刻的最终数值
            self._append(ts, f)
            self._paused_at, self._stopping_since = ts, None
            log.info("paused by user at %.0f m", self.samples[-1].dist_m)
        elif self._paused_at is not None:
            if moving:                                  # 暂停后重新起跑 (计数器接着累计, 没有 Reset)
                log.info("resumed after %.0fs pause", ts - self._paused_at)
                self._paused_at = None
                self._last_moving = ts
                self._append(ts, f)
        else:
            self._append(ts, f)
            if moving:
                self._last_moving = ts
            elif ts - self._last_moving >= self.cfg.idle_end_s:
                self._prev = f
                self._finish(self._last_moving, "idle timeout")
                return
        self._prev = f

    def on_status(self, ts: float, st: Status) -> None:
        # 这台跑步机: Stop(0x02) 实为暂停, 计数器不清零; 约 17 秒后若没重新开始会发 Reset(0x01)。
        # 所以只有 Reset / 计数器清零 / 超时才算一次跑步结束。
        if not self.active:
            return
        if st.kind == "reset":
            self._finish(self.samples[-1].ts, "machine reset")
        elif st.kind == "stop" and self._paused_at is None and self._stopping_since is None:
            self._stopping_since = ts

    def tick(self, ts: float) -> None:
        if not self.active:
            return
        if self._stopping_since is not None and ts - self._stopping_since > 3:
            self._paused_at, self._stopping_since = self._stopping_since, None
        if self._paused_at is not None:
            if ts - self._paused_at >= self.cfg.pause_end_s:
                self._finish(self._paused_at, "pause timeout")
            elif ts - self._last_rx >= self.cfg.gap_end_s:
                self._finish(self._paused_at, "data gap")
        elif ts - self._last_rx >= self.cfg.gap_end_s:
            self._finish(self._last_rx, "data gap")
        elif ts - self._last_moving >= self.cfg.idle_end_s:
            self._finish(self._last_moving, "idle timeout")

    def shutdown(self, ts: float) -> None:
        if self.active:
            self._finish(self._last_rx or ts, "shutdown")

    # ── 内部 ──
    def _counters_reset(self, f: Frame) -> bool:
        p = self._prev
        if p is None:
            return False
        if f.distance_m is not None and p.distance_m is not None and f.distance_m < p.distance_m - 5:
            return True
        if f.elapsed_s is not None and p.elapsed_s is not None and f.elapsed_s < p.elapsed_s - 5:
            return True
        return False

    @staticmethod
    def _rel(cur, base):
        return None if cur is None else max(0, cur - (base or 0))

    def _start(self, ts: float, f: Frame) -> None:
        base = self._prev if self._prev is not None else f
        if (f.distance_m is not None and base.distance_m is not None and f.distance_m < base.distance_m) or \
           (f.elapsed_s is not None and base.elapsed_s is not None and f.elapsed_s < base.elapsed_s):
            base = f                                    # 计数器在两帧之间被清零过
        self._base, self.active = base, True
        self.samples, self._stopping_since, self._paused_at = [], None, None
        self._last_moving = ts
        self.journal.open(int(ts))
        log.info("session started (speed %.1f km/h)", f.speed_kmh or 0)
        self._append(ts, f)

    def _append(self, ts: float, f: Frame) -> None:
        if self.samples and int(ts) <= int(self.samples[-1].ts):
            return                                      # 每秒最多一个点
        b = self._base or f
        dist = self._rel(f.distance_m, b.distance_m) or 0
        if self.samples:
            dist = max(dist, self.samples[-1].dist_m)   # 距离只增不减
        s = Sample(ts=ts, speed_mps=(f.speed_kmh or 0.0) / 3.6, dist_m=float(dist),
                   incline=f.incline_pct, hr=f.hr,
                   kcal=self._rel(f.kcal, b.kcal), elapsed_s=self._rel(f.elapsed_s, b.elapsed_s))
        self.samples.append(s)
        self.journal.append(s)

    def _finish(self, end_ts: float, reason: str) -> None:
        if not self.active:
            return
        samples = [s for s in self.samples if s.ts <= end_ts] or self.samples
        self.active, self.samples, self._base = False, [], None
        self._stopping_since = self._paused_at = None
        session = Session(samples)
        log.info("session ended (%s): %.0f m, %.0f s", reason, session.distance_m, session.timer_s)
        if session.timer_s < self.cfg.min_seconds or session.distance_m < self.cfg.min_meters:
            log.info("session too short, discarded")
            self.journal.close(delete=True)
            return
        jpath = self.journal.path                       # 必须在 close() 清空 path 之前取
        self.journal.close(delete=False)
        try:
            self.sink(session)
        except Exception:
            log.exception("sink failed; journal kept for recovery")
            return
        if jpath is not None:
            jpath.unlink(missing_ok=True)


# ═════════════════════════ FIT 编码 / 解码 ═════════════════════════
FIT_EPOCH = 631065600           # 1989-12-31T00:00:00Z 的 unix 时间
_CRC_TABLE = [0x0000, 0xCC01, 0xD801, 0x1400, 0xF001, 0x3C00, 0x2800, 0xE401,
              0xA001, 0x6C00, 0x7800, 0xB401, 0x5000, 0x9C01, 0x8801, 0x4400]


def fit_crc(data: bytes, crc: int = 0) -> int:
    for byte in data:
        tmp = _CRC_TABLE[crc & 0xF]
        crc = (crc >> 4) & 0x0FFF
        crc = crc ^ tmp ^ _CRC_TABLE[byte & 0xF]
        tmp = _CRC_TABLE[crc & 0xF]
        crc = (crc >> 4) & 0x0FFF
        crc = crc ^ tmp ^ _CRC_TABLE[(byte >> 4) & 0xF]
    return crc


def fit_ts(unix: float) -> int:
    return int(round(unix)) - FIT_EPOCH


# name: (base_type_id, struct_fmt, size, invalid_value, max_value, min_value)
_BASE = {
    "enum":    (0x00, "B", 1, 0xFF,       0xFF,       0),
    "uint8":   (0x02, "B", 1, 0xFF,       0xFF,       0),
    "sint16":  (0x83, "h", 2, 0x7FFF,     0x7FFF,     -0x8000),
    "uint16":  (0x84, "H", 2, 0xFFFF,     0xFFFF,     0),
    "uint32":  (0x86, "I", 4, 0xFFFFFFFF, 0xFFFFFFFF, 0),
    "uint32z": (0x8C, "I", 4, 0,          0xFFFFFFFF, 0),
}
_BASE_BY_ID = {v[0]: v for v in _BASE.values()}


class FitWriter:
    def __init__(self) -> None:
        self.data = bytearray()
        self._defs: dict = {}

    def define(self, local: int, global_num: int, fields: List[Tuple[int, str]]) -> None:
        self._defs[local] = fields
        self.data += struct.pack("<BBBHB", 0x40 | local, 0, 0, global_num, len(fields))
        for num, tname in fields:
            self.data += struct.pack("<BBB", num, _BASE[tname][2], _BASE[tname][0])

    def write(self, local: int, values: dict) -> None:
        self.data.append(local)
        for num, tname in self._defs[local]:
            _tid, fmt, _size, invalid, vmax, vmin = _BASE[tname]
            v = values.get(num)
            v = invalid if v is None else int(round(v))
            if v < vmin or v > vmax:
                v = invalid
            self.data += struct.pack("<" + fmt, v)

    def to_bytes(self) -> bytes:
        body = bytes(self.data)
        header = struct.pack("<BBHI4s", 14, 0x20, 2140, len(body), b".FIT")
        header += struct.pack("<H", fit_crc(header))
        full = header + body
        return full + struct.pack("<H", fit_crc(full))


def utc_offset_s(ts: float, tz: tzinfo) -> int:
    off = datetime.fromtimestamp(ts, tz).utcoffset()
    return int(off.total_seconds()) if off else 0


def device_serial() -> int:
    h = hashlib.sha1(socket.gethostname().encode()).digest()
    return int.from_bytes(h[:4], "big") or 1


def build_fit(s: Session, tz: tzinfo, hr_min_coverage: float = 0.5) -> bytes:
    """Activity 文件: file_id → event(start) → record×N → event(stop) → lap → session → activity。
    sport=running, sub_sport=treadmill, manufacturer=development(255)。"""
    w = FitWriter()
    t0, t1 = fit_ts(s.start_ts), fit_ts(s.end_ts)
    hr_vals = s.hr_values(hr_min_coverage)
    use_hr = bool(hr_vals)
    elapsed_ms = max(1.0, s.end_ts - s.start_ts) * 1000
    timer_ms = s.timer_s * 1000
    dist_cm = s.distance_m * 100

    w.define(0, 0, [(0, "enum"), (1, "uint16"), (2, "uint16"), (3, "uint32z"), (4, "uint32")])
    w.write(0, {0: 4, 1: 255, 2: 0, 3: device_serial(), 4: t0})                 # type=activity

    w.define(1, 21, [(253, "uint32"), (0, "enum"), (1, "enum"), (4, "uint8")])  # event
    w.write(1, {253: t0, 0: 0, 1: 0, 4: 0})                                     # timer start

    w.define(2, 20, [(253, "uint32"), (5, "uint32"), (6, "uint16"), (73, "uint32"),
                     (9, "sint16"), (3, "uint8")])                              # record
    prev: Optional[Sample] = None
    for p in s.samples:
        if prev is not None and p.ts - prev.ts > PAUSE_GAP_S:       # 暂停: 计时器 stop → start
            w.write(1, {253: fit_ts(prev.ts), 0: 0, 1: 4, 4: 0})
            w.write(1, {253: fit_ts(p.ts), 0: 0, 1: 0, 4: 0})
        prev = p
        w.write(2, {253: fit_ts(p.ts), 5: p.dist_m * 100, 6: p.speed_mps * 1000,
                    73: p.speed_mps * 1000,
                    9: None if p.incline is None else p.incline * 100,
                    3: p.hr if use_hr else None})

    w.write(1, {253: t1, 0: 0, 1: 4, 4: 0})                                     # timer stop_all

    avg_v, max_v = s.avg_speed_mps * 1000, s.max_speed_mps * 1000
    avg_hr = round(sum(hr_vals) / len(hr_vals)) if use_hr else None
    max_hr = max(hr_vals) if use_hr else None

    w.define(3, 19, [(253, "uint32"), (0, "enum"), (1, "enum"), (2, "uint32"), (7, "uint32"),
                     (8, "uint32"), (9, "uint32"), (11, "uint16"), (13, "uint16"),
                     (14, "uint16"), (15, "uint8"), (16, "uint8")])             # lap
    w.write(3, {253: t1, 0: 9, 1: 1, 2: t0, 7: elapsed_ms, 8: timer_ms, 9: dist_cm,
                11: s.calories, 13: avg_v, 14: max_v, 15: avg_hr, 16: max_hr})

    w.define(4, 18, [(253, "uint32"), (254, "uint16"), (0, "enum"), (1, "enum"), (2, "uint32"),
                     (5, "enum"), (6, "enum"), (7, "uint32"), (8, "uint32"), (9, "uint32"),
                     (11, "uint16"), (14, "uint16"), (15, "uint16"), (16, "uint8"),
                     (17, "uint8"), (25, "uint16"), (26, "uint16")])            # session
    w.write(4, {253: t1, 254: 0, 0: 8, 1: 1, 2: t0, 5: 1, 6: 1, 7: elapsed_ms, 8: timer_ms,
                9: dist_cm, 11: s.calories, 14: avg_v, 15: max_v, 16: avg_hr, 17: max_hr,
                25: 0, 26: 1})                                                  # sport=running, sub=treadmill

    w.define(5, 34, [(253, "uint32"), (0, "uint32"), (1, "uint16"), (2, "enum"),
                     (3, "enum"), (4, "enum"), (5, "uint32")])                  # activity
    w.write(5, {253: t1, 0: timer_ms, 1: 1, 2: 0, 3: 26, 4: 1,
                5: t1 + utc_offset_s(s.end_ts, tz)})
    return w.to_bytes()


def decode_fit(b: bytes) -> List[Tuple[int, dict]]:
    """极简解码器 (仅支持本脚本写出的 FIT: 普通头 + 小端 + 无开发者字段), 用于自检和 fitinfo。"""
    hs = b[0]
    if b[8:12] != b".FIT":
        raise ValueError("not a FIT file")
    if hs >= 14 and fit_crc(b[:12]) != struct.unpack_from("<H", b, 12)[0]:
        raise ValueError("header CRC mismatch")
    dsize = struct.unpack_from("<I", b, 4)[0]
    if fit_crc(b[:hs + dsize]) != struct.unpack_from("<H", b, hs + dsize)[0]:
        raise ValueError("file CRC mismatch")
    defs, msgs, o = {}, [], hs
    while o < hs + dsize:
        h = b[o]
        o += 1
        local = h & 0x0F
        if h & 0x40:
            o += 1                                       # reserved
            if b[o] != 0:
                raise ValueError("big-endian not supported")
            o += 1
            gnum = struct.unpack_from("<H", b, o)[0]
            o += 2
            n = b[o]
            o += 1
            fields = []
            for _ in range(n):
                fields.append(tuple(b[o:o + 3]))
                o += 3
            defs[local] = (gnum, fields)
        else:
            gnum, fields = defs[local]
            vals = {}
            for num, size, tid in fields:
                _t, fmt, _sz, invalid, _mx, _mn = _BASE_BY_ID[tid]
                v = struct.unpack_from("<" + fmt, b, o)[0]
                o += size
                vals[num] = None if v == invalid else v
            msgs.append((gnum, vals))
    return msgs


def describe_fit(path: Path) -> str:
    msgs = decode_fit(path.read_bytes())
    recs = [m for g, m in msgs if g == 20]
    sess = next((m for g, m in msgs if g == 18), {})
    dist = (sess.get(9) or 0) / 100
    timer = (sess.get(8) or 0) / 1000
    pace = f"{int(timer / dist * 1000 // 60)}:{int(timer / dist * 1000 % 60):02d}/km" if dist else "-"
    start = datetime.fromtimestamp((sess.get(2) or 0) + FIT_EPOCH).astimezone()
    return (f"{path.name}: {len(msgs)} messages, {len(recs)} records\n"
            f"  start {start:%Y-%m-%d %H:%M:%S %Z}  distance {dist:.0f} m  timer {timer:.0f} s  "
            f"avg pace {pace}  kcal {sess.get(11)}  sport={sess.get(5)} sub={sess.get(6)}\n"
            f"  avg HR {sess.get(16)}  max HR {sess.get(17)}  max speed {(sess.get(15) or 0) / 1000 * 3.6:.1f} km/h")


# ═══════════════════════════ 落盘 + 上传 ═══════════════════════════
def write_fit_file(cfg: Cfg, session: Session, out_dir: Path, tz: tzinfo) -> Path:
    data = build_fit(session, tz, cfg.hr_min_coverage)
    decode_fit(data)                                    # 写盘前自检, 坏文件绝不进 outbox
    stamp = datetime.fromtimestamp(session.start_ts, tz).strftime("%Y%m%d_%H%M%S")
    out_dir.mkdir(parents=True, exist_ok=True)
    final = out_dir / f"{stamp}_treadmill.fit"
    tmp = final.with_suffix(".tmp")
    tmp.write_bytes(data)
    os.replace(tmp, final)                              # 原子写入
    log.info("FIT written: %s (%d bytes)", final, len(data))
    return final


def upload_file(cfg: Cfg, path: Path) -> str:
    """同步上传一个 FIT。返回 'uploaded' 或 'duplicate'。凭据每次从 secret 重建, 避免内存里长期持有过期 token。"""
    import garth  # 延迟导入, replay/selftest 不需要

    client = garth.Client(domain=cfg.garmin_domain)
    client.loads(load_secret())
    try:
        with open(path, "rb") as fh:
            client.upload(fh)
    except Exception as e:
        status = getattr(getattr(getattr(e, "error", None), "response", None), "status_code", None)
        if status == 409 or "duplicate" in str(e).lower():
            return "duplicate"                          # Garmin 已有同一活动, 视为成功
        raise
    return "uploaded"


class Uploader:
    def __init__(self, cfg: Cfg):
        self.cfg = cfg
        self._wake = asyncio.Event()
        self._retry: dict = {}                          # 文件名 -> (失败次数, 下次重试时间)

    def kick(self) -> None:
        self._wake.set()

    async def run(self, stop: asyncio.Event) -> None:
        while not stop.is_set():
            try:
                await asyncio.wait_for(self._wake.wait(), timeout=60)
            except asyncio.TimeoutError:
                pass
            self._wake.clear()
            if not stop.is_set():
                await self.flush()

    async def flush(self) -> None:
        for p in sorted(self.cfg.outbox.glob("*.fit")):
            attempt, not_before = self._retry.get(p.name, (0, 0.0))
            if time.time() < not_before:
                continue
            try:
                result = await asyncio.to_thread(upload_file, self.cfg, p)
            except Exception as e:
                attempt += 1
                delay = min(3600, 30 * 2 ** min(attempt, 7)) * (0.8 + 0.4 * random.random())
                self._retry[p.name] = (attempt, time.time() + delay)
                log.warning("upload %s failed (%s: %s); retry #%d in %.0fs. "
                            "If this is an auth error, regenerate the secret with get_garmin_secret.py",
                            p.name, type(e).__name__, e, attempt, delay)
                continue
            self._retry.pop(p.name, None)
            os.replace(p, self.cfg.uploaded / p.name)
            log.info("upload %s: %s", p.name, result)


# ═════════════════════════════ BLE ═════════════════════════════
async def ble_loop(cfg: Cfg, tracker: SessionTracker, stop: asyncio.Event) -> None:
    try:
        from bleak import BleakClient, BleakScanner
    except ImportError:
        raise SystemExit("缺少依赖: pip install bleak")
    loop = asyncio.get_running_loop()
    backoff = 2.0

    def match(dev, adv) -> bool:
        if cfg.device_address:
            return dev.address.upper() == cfg.device_address.upper()
        return (adv.local_name or dev.name or "").startswith(cfg.device_name)

    while not stop.is_set():
        try:
            dev = await BleakScanner.find_device_by_filter(match, timeout=cfg.scan_timeout)
            if dev is None:
                log.info("treadmill not found, rescanning")
            else:
                log.info("connecting to %s (%s)", dev.name or "?", dev.address)
                disconnected = asyncio.Event()
                last_rx = time.monotonic()

                def on_disc(_c) -> None:
                    loop.call_soon_threadsafe(disconnected.set)

                def on_data(_c, data: bytearray) -> None:
                    nonlocal last_rx
                    last_rx = time.monotonic()
                    try:
                        tracker.on_frame(time.time(), parse_treadmill_data(data))
                    except Exception as e:
                        log.debug("bad treadmill frame %s: %s", bytes(data).hex(), e)

                def on_status(_c, data: bytearray) -> None:
                    try:
                        tracker.on_status(time.time(), parse_machine_status(data))
                    except Exception as e:
                        log.debug("bad status %s: %s", bytes(data).hex(), e)

                async with BleakClient(dev, disconnected_callback=on_disc, timeout=20.0) as client:
                    await client.start_notify(TREADMILL_DATA, on_data)
                    try:
                        await client.start_notify(MACHINE_STATUS, on_status)
                    except Exception as e:
                        log.warning("machine status unavailable (%s); relying on idle timeout", e)
                    log.info("connected, streaming")
                    backoff = 2.0
                    while not stop.is_set() and not disconnected.is_set():
                        if cfg.stale_s and time.monotonic() - last_rx > cfg.stale_s:
                            log.warning("no data for %ds, reconnecting", cfg.stale_s)
                            break
                        await asyncio.sleep(1)
                log.info("disconnected")
        except asyncio.CancelledError:
            raise
        except Exception as e:
            log.warning("BLE error: %s: %s", type(e).__name__, e)
        if stop.is_set():
            break
        try:
            await asyncio.wait_for(stop.wait(), timeout=backoff * (0.8 + 0.4 * random.random()))
        except asyncio.TimeoutError:
            pass
        backoff = min(backoff * 2, 60.0)


async def ticker(tracker: SessionTracker, stop: asyncio.Event) -> None:
    while not stop.is_set():
        tracker.tick(time.time())
        try:
            await asyncio.wait_for(stop.wait(), timeout=1.0)
        except asyncio.TimeoutError:
            pass


async def cmd_scan(cfg: Cfg, seconds: float) -> None:
    from bleak import BleakScanner
    found = await BleakScanner.discover(timeout=seconds, return_adv=True)
    print("* = 广播了 FTMS(0x1826) 服务")
    for addr, (dev, adv) in sorted(found.items(), key=lambda kv: -kv[1][1].rssi):
        ftms = FTMS_SERVICE in [u.lower() for u in adv.service_uuids]
        print(f"{'*' if ftms else ' '} {addr}  {adv.rssi:>4} dBm  {adv.local_name or dev.name or '-'}")


# ═════════════════════════════ 命令 ═════════════════════════════
async def cmd_run(cfg: Cfg) -> None:
    cfg.ensure_dirs()
    if not cfg.no_upload:
        load_secret()                                    # 启动时就失败, 别等到第一次上传
    tz = get_tz(cfg.tz)
    uploader = Uploader(cfg)
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop.set)
        except NotImplementedError:                      # Windows
            signal.signal(sig, lambda *_: loop.call_soon_threadsafe(stop.set))

    def sink(session: Session) -> None:
        write_fit_file(cfg, session, cfg.outbox, tz)
        if not cfg.no_upload:
            uploader.kick()

    tracker = SessionTracker(cfg, sink, cfg.journal)
    for path, samples in Journal.orphans(cfg.journal):   # 上次异常退出遗留的会话
        if samples:
            log.warning("recovering unfinished session from %s (%d samples)", path.name, len(samples))
            session = Session(samples)
            if session.timer_s >= cfg.min_seconds and session.distance_m >= cfg.min_meters:
                sink(session)
        path.unlink(missing_ok=True)
    if not cfg.no_upload:
        uploader.kick()                                  # 启动时先把积压的传一遍

    log.info("started: device prefix=%r address=%r data_dir=%s upload=%s",
             cfg.device_name, cfg.device_address, cfg.data_dir, not cfg.no_upload)
    tasks = [asyncio.create_task(ble_loop(cfg, tracker, stop)),
             asyncio.create_task(ticker(tracker, stop))]
    if not cfg.no_upload:
        tasks.append(asyncio.create_task(uploader.run(stop)))
    await stop.wait()
    log.info("shutting down")
    uploader.kick()                                      # 唤醒可能正在 60s 等待里的上传协程, 否则关机会卡住
    await asyncio.gather(*tasks, return_exceptions=True)
    tracker.shutdown(time.time())
    if not cfg.no_upload:
        try:
            await asyncio.wait_for(uploader.flush(), timeout=30)
        except Exception as e:
            log.warning("final upload skipped: %s", e)


def cmd_replay(cfg: Cfg, csv_path: Path, day: date_cls, out_dir: Path) -> int:
    """回放 nRF Connect 导出的 CSV。CSV 只有 HH:MM:SS 没有日期, 用 --date 补; 时间按 --tz 解释。"""
    tz = get_tz(cfg.tz or "Asia/Shanghai")
    pat = re.compile(r"Updated Value of Characteristic (2ACD|2ADA) to ([0-9A-Fa-f ]+)\.")
    outputs: List[Path] = []
    cfg.gap_end_s = cfg.pause_end_s = 600                # CSV 里的值是抽样的, 放宽断档判定

    def sink(session: Session) -> None:
        outputs.append(write_fit_file(cfg, session, out_dir, tz))

    tracker = SessionTracker(cfg, sink, None)
    last = 0.0
    with open(csv_path, newline="", encoding="utf-8-sig") as fh:
        for row in csv.reader(fh):
            if len(row) < 4:
                continue
            m = pat.search(row[3])
            if not m:
                continue
            hh, mm, ss = row[0].split(":")
            sec, _, ms = ss.partition(".")
            ts = datetime.combine(day, time_cls(int(hh), int(mm), int(sec), int(ms or 0) * 1000), tz).timestamp()
            last = ts
            data = bytes.fromhex(m.group(2).replace(" ", ""))
            tracker.tick(ts)
            try:
                if m.group(1) == "2ACD":
                    tracker.on_frame(ts, parse_treadmill_data(data))
                else:
                    tracker.on_status(ts, parse_machine_status(data))
            except ValueError as e:
                log.warning("skip bad value %s: %s", data.hex(), e)
    tracker.shutdown(last)
    for p in outputs:
        print(describe_fit(p))
    return len(outputs)


def cmd_upload(cfg: Cfg) -> None:
    cfg.ensure_dirs()
    asyncio.run(Uploader(cfg).flush())


def cmd_selftest() -> None:
    cfg = Cfg(min_seconds=1, min_meters=1)
    tz = get_tz("Asia/Shanghai")
    got: List[Session] = []
    tr = SessionTracker(cfg, got.append, None)
    t = 1_800_000_000.0
    # 起跑前计数器就带着上次的残值 (真机观察到的行为: 360 m / 125 s / 18 kcal)
    for i in range(3):
        tr.on_frame(t + i, Frame(0.0, 360, 0.0, 18, None, 125))
    tr.on_status(t + 3, Status("start"))
    for i in range(30):                                   # 第 1 段: 30 s @ 10.8 km/h
        tr.on_frame(t + 4 + i, Frame(10.8, 360 + i * 3, 2.0, 18 + i // 6, 140 if i > 5 else None, 125 + i))
    tr.on_status(t + 34, Status("stop"))                   # 按停止 = 暂停, 不应结束会话
    tr.on_frame(t + 35, Frame(0.0, 450, 2.0, 23, None, 155))
    for i in range(15):                                   # 暂停 15 s, 速度 0
        tr.on_frame(t + 36 + i, Frame(0.0, 450, 2.0, 23, None, 155))
    assert not got and tr.active, "pause must not end the session"
    for i in range(30):                                   # 第 2 段: 30 s 接着跑, 计数器继续累计
        tr.on_frame(t + 51 + i, Frame(10.8, 450 + i * 3, 2.0, 23 + i // 6, None, 156 + i))
    tr.on_status(t + 81, Status("stop"))
    tr.on_frame(t + 82, Frame(0.0, 540, 2.0, 28, None, 185))
    assert not got, "stop alone must not end the session"
    tr.on_status(t + 99, Status("reset"))                  # 17 s 后跑步机 Reset → 结束
    assert len(got) == 1, got
    s = got[0]
    assert abs(s.distance_m - 180) <= 3 and s.samples[0].dist_m == 0, (s.distance_m, s.samples[0])
    assert abs(s.timer_s - 60) <= 2 and len(s.pauses) == 1, (s.timer_s, s.pauses)
    data = build_fit(s, tz)
    msgs = decode_fit(data)
    kinds = [g for g, _ in msgs]
    assert kinds.count(20) == len(s.samples) and kinds[0] == 0 and kinds[-1] == 34, kinds
    assert kinds.count(21) == 4, "start + pause stop/start + final stop"
    sess = next(m for g, m in msgs if g == 18)
    assert sess[5] == 1 and sess[6] == 1 and abs(sess[9] / 100 - s.distance_m) < 1
    bad = bytearray(data)                                  # 破坏一个字节 → CRC 必须报错
    bad[40] ^= 0xFF
    try:
        decode_fit(bytes(bad))
        raise AssertionError("corruption not detected")
    except ValueError:
        pass
    print("selftest OK:", len(data), "bytes,", len(s.samples), "records, 1 pause")


# ═════════════════════════════ 入口 ═════════════════════════════
def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("-v", "--verbose", action="store_true")
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("run", help="常驻服务")
    sp = sub.add_parser("scan", help="扫描 BLE 设备")
    sp.add_argument("--seconds", type=float, default=10)
    rp = sub.add_parser("replay", help="nRF Connect CSV → FIT")
    rp.add_argument("csv", type=Path)
    rp.add_argument("--date", default=date_cls.today().isoformat(), help="CSV 的日期 YYYY-MM-DD")
    rp.add_argument("--out", type=Path, default=Path("./replay_out"))
    sub.add_parser("upload", help="上传 outbox 里待传的 FIT")
    fp = sub.add_parser("fitinfo", help="打印 FIT 摘要")
    fp.add_argument("file", type=Path)
    sub.add_parser("selftest", help="内置自检")
    args = ap.parse_args(argv)

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s", stream=sys.stdout)
    cfg = Cfg.from_env()
    cmd = args.cmd or "run"
    if cmd == "run":
        asyncio.run(cmd_run(cfg))
    elif cmd == "scan":
        asyncio.run(cmd_scan(cfg, args.seconds))
    elif cmd == "replay":
        n = cmd_replay(cfg, args.csv, date_cls.fromisoformat(args.date), args.out)
        print(f"{n} FIT file(s) in {args.out}")
    elif cmd == "upload":
        cmd_upload(cfg)
    elif cmd == "fitinfo":
        print(describe_fit(args.file))
    elif cmd == "selftest":
        cmd_selftest()
    return 0


if __name__ == "__main__":
    sys.exit(main())
