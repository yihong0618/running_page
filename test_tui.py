import asyncio
from textual.app import App
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.reactive import reactive
from textual.widgets import Static, Header, Footer, DataTable, Button
from rich.console import Group as RichGroup
from rich.table import Table as RichTable
from rich.text import Text as RichText


class StatsView(Widget):
    data = reactive(None)

    def render(self):
        if self.data is None:
            return RichText("  Loading...", style="dim white")
        parts = []
        parts.append(RichText("\n  Overall Statistics\n", style="bold cyan"))
        tbl = RichTable(show_header=False, border_style="green", padding=(0, 2))
        tbl.add_column("", style="bold")
        tbl.add_column("")
        tbl.add_row("Total Distance", "100 km")
        parts.append(tbl)
        return RichGroup(*parts)


class NavSidebar(Widget):
    def compose(self):
        with Vertical():
            yield Button("1  List", id="nav-list")
            yield Button("2  Stat", id="nav-stats")
            yield Button("3  Place", id="nav-places")
            yield Button("4  Grid", id="nav-grid")


class FilterBar(Static):
    def on_mount(self):
        self.styles.dock = "top"
        self.styles.padding = (0, 1)
        self.styles.background = "#161b22"


class TestApp(App):
    CSS = """
    Screen { background: #0d1117; }
    #nav-sidebar { width: 15; height: 100%; }
    #main-area { height: 100%; }
    #view-list { height: 100%; }
    #list-left { width: 45%; min-width: 40; border: solid #30363d; background: #0d1117; }
    #list-right { width: 55%; min-width: 30; }
    #detail-panel { height: auto; border: solid #30363d; background: #0d1117; padding: 0 1; }
    #route-panel { height: 1fr; border: solid #30363d; background: #0d1117; }
    #view-stats { height: 100%; overflow-y: auto; padding: 0 2; }
    #view-places { height: 100%; overflow-y: auto; padding: 0 2; }
    #view-grid { height: 100%; overflow-y: auto; padding: 0 2; }
    """

    def compose(self):
        yield Header()
        with Horizontal():
            yield NavSidebar(id="nav-sidebar")
            with Vertical(id="main-area"):
                yield FilterBar("Filter bar", id="filter-bar")
                with Horizontal(id="view-list"):
                    with Vertical(id="list-left"):
                        yield DataTable(id="run-table")
                    with Vertical(id="list-right"):
                        yield Static("Detail", id="detail-panel")
                        with Vertical(id="route-panel"):
                            yield Static("Route", id="route-map")
                yield StatsView(id="view-stats")
                yield Widget(id="view-places")
                yield Widget(id="view-grid")
        yield Footer()

    def on_mount(self):
        self.title = "Test"
        self.sub_title = "test"
        table = self.query_one("#run-table", DataTable)
        table.add_columns("#", "Date", "Distance")
        for i in range(24):
            table.add_row(str(i), "2026-01-01", "5.00")
        sv = self.query_one("#view-stats")
        sv.data = "something"
        self.query_one("#view-list").display = True
        self.query_one("#view-stats").display = False
        self.query_one("#view-places").display = False
        self.query_one("#view-grid").display = False

        def show():
            self.query_one("#view-list").display = False
            self.query_one("#view-stats").display = True

        asyncio.get_event_loop().call_later(1, show)


if __name__ == "__main__":
    app = TestApp()
    app.run()
