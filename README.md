# Workout Log

A modern, responsive workout tracking dashboard built with React + TypeScript + Tailwind CSS. Visualize your running and cycling activities with interactive heatmaps, route maps, and detailed statistics.

> Based on [running_page](https://github.com/yihong0618/running_page) data pipeline. Live demo: [zhaohongxuan.github.io/workouts](http://zhaohongxuan.github.io/workouts)

## Features

- **Activity Heatmap** — GitHub-style contribution heatmap showing workout frequency across years
- **Route Map** — Mapbox-powered interactive map displaying all GPS tracks with fullscreen support
- **Personal Best** — Track your PRs for 5K, 10K, Half Marathon, and Marathon distances
- **Stats Dashboard** — Yearly, monthly, and weekly goals with progress bars and period comparisons
- **Streak Tracking** — Consecutive days/weeks of activity with visual weekly calendar
- **Activity Log** — Sortable, paginated activity table with distance filters
- **Calendar Widget** — Monthly calendar highlighting workout days
- **i18n** — Full Chinese/English language support with one-click toggle
- **Dark/Light Mode** — Theme toggle with system preference detection
- **Sport Filter** — Filter all views by All / Run / Ride

## Tech Stack

- **React 18** + TypeScript
- **Vite** — Fast dev server and build
- **Tailwind CSS** — Utility-first styling
- **Recharts** — Monthly distance and speed trend charts
- **Mapbox GL** — Interactive route visualization
- **@mapbox/polyline** — Decode GPS polylines

## Getting Started

```bash
# Install dependencies
pnpm install

# Start dev server
pnpm dev

# Build for production
pnpm build
```

## Project Structure

```
src/
├── App.tsx              # Main app layout
├── i18n.ts             # Translation dictionary
├── types.ts            # TypeScript interfaces
├── hooks/
│   ├── useActivities.ts   # Data filtering & formatting
│   ├── useLocale.tsx      # i18n context & hook
│   └── useTheme.ts       # Dark/light mode
├── components/
│   ├── Header.tsx         # Navigation & filters
│   ├── StatsCards.tsx     # Goal cards & streak
│   ├── ProfileCard.tsx    # Personal info summary
│   ├── PersonalBest.tsx   # PR records
│   ├── ContributionHeatmap.tsx  # Activity heatmap
│   ├── ActivityLog.tsx    # Activity table
│   ├── CalendarWidget.tsx # Monthly calendar
│   ├── MonthlyChart.tsx   # Bar chart
│   ├── TrendCharts.tsx    # Speed & distance trends
│   └── RouteMap.tsx       # Mapbox route display
└── static/
    └── activities.json    # Activity data
```

## Data Source

Activity data is synced from Strava/Garmin via the [running_page](https://github.com/yihong0618/running_page) project pipeline and stored as `activities.json`.

## Acknowledgements

- [running_page](https://github.com/yihong0618/running_page) — Data sync pipeline and original project inspiration
- [yihong0618](https://github.com/yihong0618) — Creator of running_page

## License

MIT
