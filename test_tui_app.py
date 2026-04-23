import json
import unittest

from textual.widgets import Button

from run_page.tui.app import (
    FilterBar,
    NavSidebar,
    RunDetailPanel,
    RunningTUI,
    StatsView,
    _monthly_distances,
)
from run_page.tui.data import Activity, YearStats


def _activity(run_id: int, date_local: str) -> dict:
    return {
        "run_id": run_id,
        "name": f"Run {run_id}",
        "distance": 5000.0,
        "moving_time": "00:25:00",
        "type": "Run",
        "subtype": None,
        "start_date": f"{date_local} 00:00:00",
        "start_date_local": f"{date_local} 08:00:00",
        "location_country": None,
        "summary_polyline": None,
        "average_heartrate": None,
        "elevation_gain": None,
        "average_speed": 3.33,
        "streak": 1,
    }


def _many_activities(count: int = 108) -> list[dict]:
    return [
        _activity(i, f"2026-{(i % 4) + 1:02d}-{(i % 27) + 1:02d}")
        for i in range(1, count + 1)
    ]


class RunningTUITest(unittest.IsolatedAsyncioTestCase):
    def test_monthly_distances_aggregates_by_month(self) -> None:
        year_stats = YearStats(
            year="2026",
            daily_distances={
                "2026-01-01": 5.0,
                "2026-01-15": 3.5,
                "2026-02-02": 7.0,
            },
        )

        totals = _monthly_distances(year_stats)

        self.assertEqual(len(totals), 12)
        self.assertAlmostEqual(totals[0], 8.5)
        self.assertAlmostEqual(totals[1], 7.0)
        self.assertTrue(all(value == 0 for value in totals[2:]))

    async def test_default_year_filter_uses_latest_year(self) -> None:
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as tmp:
            data_path = f"{tmp}/activities.json"
            with open(data_path, "w") as fh:
                json.dump(
                    [
                        _activity(1, "2024-01-01"),
                        _activity(2, "2026-01-02"),
                    ],
                    fh,
                )

            app = RunningTUI(data_path)

            async with app.run_test() as pilot:
                await pilot.pause()

                filter_bar = app.query_one(FilterBar)
                detail = app.query_one(RunDetailPanel)
                year_button = app.query_one("#fl-year", Button)
                type_button = app.query_one("#fl-type", Button)

                self.assertEqual(filter_bar.selected_year, "2026")
                self.assertEqual(year_button.label.plain, "2026")
                self.assertEqual(type_button.label.plain, "All")
                self.assertEqual(
                    [activity.year for activity in app._displayed_activities],
                    ["2026"],
                )
                self.assertIsNotNone(app.filtered_data)
                self.assertEqual(app.filtered_data.total_count, 1)
                self.assertAlmostEqual(app.filtered_data.total_distance, 5.0)
                self.assertIsNotNone(detail.activity)
                self.assertEqual(detail.activity.date_local, "2026-01-02")
                self.assertEqual(app.sub_title, "2026 · 1/2 activities")
                self.assertEqual(app._current_view, "list")
                self.assertFalse(app.query_one("#view-stats").display)
                self.assertTrue(app.query_one("#view-list").display)
                self.assertEqual(len(app.query("#fl-search")), 0)

                nav = app.query_one(NavSidebar)
                labels = [button.label.plain for button in nav.query(Button)]
                self.assertEqual(labels, ["1  List", "2  Stats"])

    async def test_cursor_move_updates_detail_without_click(self) -> None:
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as tmp:
            data_path = f"{tmp}/activities.json"
            with open(data_path, "w") as fh:
                json.dump(
                    [
                        _activity(1, "2026-01-01"),
                        _activity(2, "2026-01-02"),
                    ],
                    fh,
                )

            app = RunningTUI(data_path)

            async with app.run_test() as pilot:
                await pilot.press("1")
                await pilot.pause()

                detail = app.query_one(RunDetailPanel)
                self.assertIsNotNone(detail.activity)
                self.assertEqual(detail.activity.date_local, "2026-01-01")

                await pilot.press("down")
                await pilot.pause()

                self.assertIsNotNone(detail.activity)
                self.assertEqual(detail.activity.date_local, "2026-01-02")

    def test_run_detail_rows_keep_city_only(self) -> None:
        activity = Activity(
            run_id=1,
            name="City Run",
            distance=5000.0,
            moving_time="00:25:00",
            type="Run",
            subtype=None,
            start_date="2026-01-01 00:00:00",
            start_date_local="2026-01-01 08:00:00",
            location_country="高能街, 凌水街道, 栾金村, 甘井子区, 沙河口区, 大连市, 辽宁省, 116026, 中国",
            summary_polyline="abc",
            average_heartrate=160,
            elevation_gain=None,
            average_speed=3.33,
            streak=1,
        )

        rows = dict(RunDetailPanel()._rows(activity))

        self.assertEqual(rows["Location"], "大连市")
        self.assertNotIn("Type", rows)
        self.assertNotIn("Route", rows)

    def test_run_detail_extra_rows_include_cumulative_context(self) -> None:
        activities = [
            Activity(
                run_id=1,
                name="Run 1",
                distance=5000.0,
                moving_time="00:25:00",
                type="Run",
                subtype=None,
                start_date="2026-01-01 00:00:00",
                start_date_local="2026-01-01 08:00:00",
                location_country=None,
                summary_polyline=None,
                average_heartrate=None,
                elevation_gain=None,
                average_speed=3.33,
                streak=1,
            ),
            Activity(
                run_id=2,
                name="Run 2",
                distance=3000.0,
                moving_time="00:15:00",
                type="Run",
                subtype=None,
                start_date="2026-01-02 00:00:00",
                start_date_local="2026-01-02 08:00:00",
                location_country=None,
                summary_polyline=None,
                average_heartrate=None,
                elevation_gain=None,
                average_speed=3.33,
                streak=2,
            ),
        ]
        panel = RunDetailPanel()
        from run_page.tui.data import aggregate_activities

        panel.data = aggregate_activities(activities)

        rows = dict(panel._extra_rows(activities[1]))

        self.assertEqual(rows["Week"], "01")
        self.assertEqual(rows["YTD"], "8.0 km")
        self.assertEqual(rows["MTD"], "8.0 km")
        self.assertEqual(rows["Year #"], "2 / 2")
        self.assertEqual(rows["Month #"], "2 / 2")

    async def test_stats_period_uses_overall_data_range(self) -> None:
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as tmp:
            data_path = f"{tmp}/activities.json"
            with open(data_path, "w") as fh:
                json.dump(
                    [
                        _activity(1, "2025-01-01"),
                        _activity(2, "2026-01-02"),
                    ],
                    fh,
                )

            app = RunningTUI(data_path)

            async with app.run_test() as pilot:
                await pilot.press("y")
                await pilot.pause()

                self.assertEqual(app.query_one(FilterBar).selected_year, "2025")
                self.assertEqual(app.query_one(StatsView).period_label, "2025-2026")

    async def test_stats_period_uses_selected_year_and_next_year(self) -> None:
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as tmp:
            data_path = f"{tmp}/activities.json"
            with open(data_path, "w") as fh:
                json.dump(
                    [
                        _activity(1, "2021-01-01"),
                        _activity(2, "2022-01-02"),
                        _activity(3, "2026-01-03"),
                    ],
                    fh,
                )

            app = RunningTUI(data_path)

            async with app.run_test() as pilot:
                await pilot.press("y", "y")
                await pilot.pause()

                self.assertEqual(app.query_one(FilterBar).selected_year, "2021")
                self.assertEqual(app.query_one(StatsView).period_label, "2021-2022")

    async def test_stats_view_fits_single_screen_for_single_year(self) -> None:
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as tmp:
            data_path = f"{tmp}/activities.json"
            with open(data_path, "w") as fh:
                json.dump(_many_activities(), fh)

            app = RunningTUI(data_path)

            async with app.run_test(size=(160, 55)) as pilot:
                await pilot.press("2")
                await pilot.pause()

                stats_view = app.query_one(StatsView)

                self.assertEqual(stats_view.max_scroll_y, 0)

    async def test_stats_view_scrolls_on_small_screen(self) -> None:
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as tmp:
            data_path = f"{tmp}/activities.json"
            with open(data_path, "w") as fh:
                json.dump(_many_activities(), fh)

            app = RunningTUI(data_path)

            async with app.run_test(size=(120, 24)) as pilot:
                await pilot.press("2")
                await pilot.pause()

                stats_view = app.query_one(StatsView)

                self.assertGreater(stats_view.max_scroll_y, 0)

    async def test_left_right_keys_switch_selected_year(self) -> None:
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as tmp:
            data_path = f"{tmp}/activities.json"
            with open(data_path, "w") as fh:
                json.dump(
                    [
                        _activity(1, "2024-01-01"),
                        _activity(2, "2025-01-01"),
                        _activity(3, "2026-01-01"),
                    ],
                    fh,
                )

            app = RunningTUI(data_path)

            async with app.run_test() as pilot:
                await pilot.pause()

                filter_bar = app.query_one(FilterBar)
                self.assertEqual(filter_bar.selected_year, "2026")

                await pilot.press("left")
                await pilot.pause()
                self.assertEqual(filter_bar.selected_year, "2025")

                await pilot.press("right")
                await pilot.pause()
                self.assertEqual(filter_bar.selected_year, "2026")
