import asyncio
from run_page.tui.app import RunningTUI


class TestApp(RunningTUI):
    def on_mount(self):
        super().on_mount()

        async def switch():
            await asyncio.sleep(1)
            self.action_view_stats()
            await asyncio.sleep(1)
            self.exit()

        asyncio.create_task(switch())


if __name__ == "__main__":
    app = TestApp()
    app.run()
