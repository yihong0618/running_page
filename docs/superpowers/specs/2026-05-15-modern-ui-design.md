# Modern Workout Dashboard UI — Design Spec

**Date:** 2026-05-15
**Branch:** `modern-ui`
**Scope:** Full frontend rewrite. Python data sync scripts untouched.

---

## Overview

A modern, single-page personal workout dashboard focused on **running and cycling data**. The centerpiece is a GitHub-contribution-style heatmap showing activity distances, with rich statistics, trend charts, and an activity list. Supports dark/light theme and dynamic sport-type filtering.

---

## Tech Stack

| Layer | Choice |
|-------|--------|
| Framework | React 18 + TypeScript |
| Build | Vite |
| Styling | Tailwind CSS v4 |
| Charts | Recharts |
| Routing | React Router v6 (single Dashboard page) |
| Data | `src/static/activities.json` (existing format, filtered to `Run` + `Ride`) |

---

## Page Structure

Single-page Dashboard (`/`), scrolling top-to-bottom:

```
┌─────────────────────────────────────────┐
│  Header                                 │
│  Logo | Sport Filter Tabs | Year | Theme│
├─────────────────────────────────────────┤
│  Hero Stats (6 cards, responsive grid)  │
├─────────────────────────────────────────┤
│  Contribution Heatmap                   │
├─────────────────────────────────────────┤
│  Trend Charts (2 charts side by side)   │
├─────────────────────────────────────────┤
│  Activity List (card/table toggle)      │
└─────────────────────────────────────────┘
```

---

## Components

### Header
- **Left:** Project name/logo (text only, minimal)
- **Center:** Sport filter tabs — `全部 / 跑步 / 骑行` — controls all components globally
- **Right:** Year selector dropdown + dark/light theme toggle button

### Hero Stats
6 metric cards in a responsive grid (3-col desktop / 2-col tablet / 1-col mobile):

1. 总距离 (km)
2. 总次数
3. 总时间 (hours)
4. 最长单次距离
5. 最佳配速 (running) / 最快均速 (cycling)
6. 当前连续打卡天数 (streak)

Numbers use monospace font (`font-mono`) for visual impact.

### Contribution Heatmap

GitHub contribution graph style:
- **X-axis:** weeks of the year; **Y-axis:** Mon–Sun
- **Color by sport:**
  - 跑步: orange scale `#431407` → `#f97316`
  - 骑行: blue scale `#1e3a5f` → `#3b82f6`
  - 全部: purple scale `#3b0764` → `#a855f7`
- **Intensity:** distance-based (longer = darker cell)
- **Tooltip on hover:** date + distance + activity name(s)
- **Year switcher:** renders heatmap for selected year
- **Empty day:** subtle base color (not invisible)

### Trend Charts (side by side, stack on tablet/mobile)

1. **月度距离柱状图** — stacked bar chart, running + cycling per month
2. **配速/均速趋势** — scatter plot of per-activity pace, with moving-average trend line

### Activity List

- Default: **card view** — each card shows date, distance, time, pace, sport icon, optional route polyline thumbnail
- Toggle: **table view** — compact, click column headers to sort
- Filters: date range, sport type (synced with global filter)
- Sort: by date (default desc), distance, pace

---

## Visual Design

### Color System

| Token | Dark | Light |
|-------|------|-------|
| Background | `#0d1117` | `#f6f8fa` |
| Card | `#161b22` | `#ffffff` |
| Border | `#30363d` | `#d0d7de` |
| Text primary | `#e6edf3` | `#1f2328` |
| Text muted | `#8b949e` | `#656d76` |

Sport accent colors defined as CSS variables, switched via filter state.

### Typography & Shape
- Numbers: `font-mono`, large size for hero stats
- Cards: `rounded-xl`, subtle shadow, flat modern aesthetic
- Consistent 4px spacing grid via Tailwind

### Interactions & Animation
- Filter tab switch: all components update synchronously, 300ms fade transition
- Heatmap hover: floating tooltip
- Year switch: heatmap re-renders smoothly
- Activity card hover: slight lift with box-shadow
- Card/table toggle: fade transition on content area

### Responsive Breakpoints
| Breakpoint | Layout |
|-----------|--------|
| > 1280px | Trend charts side by side, stats 3-col |
| 768–1280px | Trend charts stacked, stats 2-col |
| < 768px | Full single column, heatmap horizontally scrollable |

---

## Data Layer

- **Source:** `src/static/activities.json` — untouched existing format
- **Filtering:** frontend-only, filter to `type === 'Run' || type === 'Ride'`
- **No backend changes:** Python sync scripts remain as-is
- **Year filtering:** derive from activity `start_date` field

---

## Out of Scope

- Map route visualization (deprioritized for v1, can add later)
- Other sport types (swimming, hiking, etc.)
- Social/sharing features
- Backend API changes
