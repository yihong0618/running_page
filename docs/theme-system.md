# 主题系统 (3.0)

Running Page 3.0 引入了可插拔的主题架构。你可以切换内置主题或创建自己的主题，无需修改源代码。

## 工作原理

主题位于 `src/themes/<name>/` 目录下，每个主题导出一个 React 组件。应用入口 (`src/App.tsx`) 维护一个**主题注册表**，将主题名称映射到懒加载的组件：

```typescript
// src/App.tsx
const themes: Record<string, React.LazyExoticComponent<React.ComponentType>> = {
  dashboard: lazy(() => import('./themes/dashboard')),
  classic: lazy(() => import('./themes/classic')),
  // 在此添加自定义主题
}
```

构建时，`config.yml` 中的 `theme_preset` 决定加载哪个主题。所有主题共享核心层 (`src/core/`)——类型、i18n 翻译、活动数据钩子和语言工具。

## 内置主题

### Dashboard

Dashboard 主题是为跑者设计的现代化单页布局，提供丰富的小部件：

- **统计卡片** — 年度/月度/周度进度条，含连续运动追踪
- **热力图** — GitHub 风格的活动网格，每日详情，支持导出 PNG
- **活动日志** — 分页表格，支持距离筛选（10km+、20km+、40km+），运动类型图标
- **路线地图** — 基于 Mapbox 的路线可视化，点击活动高亮轨迹
- **轨迹墙** — 全页轨迹网格，智能聚类（按起终点），支持导出 PNG
- **中国地图** — 省份级活动热力图，点击筛选
- **个人最佳** — 自动检测 PR（5K、10K、半马、全马）
- **日历小部件** — 月度日历，气泡显示距离
- **深色/浅色模式** — 跟随系统或手动切换

主要特性：
- 所有数据在一个页面展示（无需路由跳转）
- 点击任意活动即可在地图和日志中查看
- 热力图和轨迹墙支持导出为 PNG 图片
- 响应式两栏网格布局

### Classic

Classic 主题保留了原始的多页面布局，每个视图有独立路由。使用 `react-router-dom` 导航和 `react-map-gl` 地图。如果你更喜欢原始风格，或从 v2.x 升级，推荐选择此主题。

> **注意：** 如果你从 v2.x 升级，可在 `config.yml` 中设置 `theme_preset: classic`。

## 创建自定义主题

1. 在 `src/themes/<your-theme>/` 下创建新目录，例如 `src/themes/minimal/`
2. 创建 `index.tsx` 导出默认 React 组件
3. 使用共享核心层获取数据和 i18n：

```tsx
// src/themes/minimal/index.tsx
import { getActivityData } from '@/hooks/useActivities'
import { useTheme } from '@/hooks/useTheme'
import { useLocale } from '@/hooks/useLocale'
import type { Activity } from '@/types'

export default function Minimal() {
  const activities = getActivityData() as Activity[]
  const { t } = useLocale()
  // ... 你的自定义布局
}
```

4. 在 `src/App.tsx` 中注册你的主题：

```typescript
const themes = {
  dashboard: lazy(() => import('./themes/dashboard')),
  classic: lazy(() => import('./themes/classic')),
  minimal: lazy(() => import('./themes/minimal')), // 添加这行
}
```

5. 在 `config.yml` 中设置 `theme_preset: minimal`

## 共享核心层 API

所有主题可用的钩子和工具：

| 模块 | 导出 |
|--------|---------|
| `@/hooks/useActivities` | `getActivityData()`、`useFilteredActivities()`、`getAvailableYears()`、`formatDistance()`、`formatPace()`、`formatDuration()`、`parseMovingTime()`、`extractProvince()` |
| `@/hooks/useLocale` | `useLocale()` → `{ t, locale }` 用于 i18n |
| `@/hooks/useTheme` | `useTheme()` → `{ dark, toggle }` 用于深/浅色模式 |
| `@/types` | `Activity`、`SportFilter` 类型 |
| `@/config` | `MAPBOX_TOKEN`、`AVATAR`、`GOALS`、`DEFAULT_LOCALE`、`THEME_PRESET` |

Dashboard 主题的组件 (`src/components/`) 也可复用 —— 如需要可在自定义主题中导入。
