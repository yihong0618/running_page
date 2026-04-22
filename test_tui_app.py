import json
import unittest

from textual.widgets import Button

from run_page.tui.app import (
    FilterBar,
    NavSidebar,
    RunDetailPanel,
    RunningTUI,
    _monthly_distances,
)
from run_page.tui.data import YearStats


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
