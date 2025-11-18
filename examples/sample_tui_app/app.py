#!/usr/bin/env python3
"""
Sample Textual TUI Application
Demonstrates a multi-screen app with navigation, keybindings, and various widgets.
"""

from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.widgets import (
    Header,
    Footer,
    Button,
    Static,
    Label,
    DataTable,
    Switch,
)
from textual.containers import Container, Horizontal, Vertical
from textual.binding import Binding


class MainMenuScreen(Screen):
    """Main menu screen with navigation to other screens."""

    BINDINGS = [
        Binding("s", "goto_settings", "Settings", show=True),
        Binding("d", "goto_dashboard", "Dashboard", show=True),
        Binding("q", "quit", "Quit", show=True),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield Container(
            Static("🎮 Sample TUI Application", id="title"),
            Static("Navigate using buttons or keyboard shortcuts", id="subtitle"),
            Horizontal(
                Button("⚙️  Settings", id="btn-settings", variant="primary"),
                Button("📊 Dashboard", id="btn-dashboard", variant="success"),
                Button("🚪 Quit", id="btn-quit", variant="error"),
                id="button-container",
            ),
            id="main-menu",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id
        if button_id == "btn-settings":
            self.app.push_screen("settings")
        elif button_id == "btn-dashboard":
            self.app.push_screen("dashboard")
        elif button_id == "btn-quit":
            self.app.exit()

    def action_goto_settings(self) -> None:
        """Navigate to settings screen."""
        self.app.push_screen("settings")

    def action_goto_dashboard(self) -> None:
        """Navigate to dashboard screen."""
        self.app.push_screen("dashboard")

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()


class SettingsScreen(Screen):
    """Settings screen with configuration options."""

    BINDINGS = [
        Binding("escape", "go_back", "Back", show=True),
        Binding("q", "quit", "Quit", show=True),
    ]

    def __init__(self):
        super().__init__()
        self.dark_mode = True
        self.notifications = True
        self.auto_save = False

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield Container(
            Static("⚙️ Settings", id="settings-title"),
            Vertical(
                Horizontal(
                    Label("Dark Mode:", id="label-dark-mode"),
                    Switch(value=self.dark_mode, id="switch-dark-mode"),
                ),
                Horizontal(
                    Label("Notifications:", id="label-notifications"),
                    Switch(value=self.notifications, id="switch-notifications"),
                ),
                Horizontal(
                    Label("Auto Save:", id="label-auto-save"),
                    Switch(value=self.auto_save, id="switch-auto-save"),
                ),
                id="settings-controls",
            ),
            Button("← Back to Menu", id="btn-back", variant="primary"),
            id="settings-container",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "btn-back":
            self.app.pop_screen()

    def on_switch_changed(self, event: Switch.Changed) -> None:
        """Handle switch toggle events."""
        switch_id = event.switch.id
        if switch_id == "switch-dark-mode":
            self.dark_mode = event.value
        elif switch_id == "switch-notifications":
            self.notifications = event.value
        elif switch_id == "switch-auto-save":
            self.auto_save = event.value

    def action_go_back(self) -> None:
        """Return to previous screen."""
        self.app.pop_screen()

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()


class DashboardScreen(Screen):
    """Dashboard screen showing data table and statistics."""

    BINDINGS = [
        Binding("escape", "go_back", "Back", show=True),
        Binding("r", "refresh_data", "Refresh", show=True),
        Binding("q", "quit", "Quit", show=True),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield Container(
            Static("📊 Dashboard", id="dashboard-title"),
            Horizontal(
                Static("Total Items: 42", id="stat-items"),
                Static("Active Users: 15", id="stat-users"),
                Static("Uptime: 99.9%", id="stat-uptime"),
                id="stats-container",
            ),
            DataTable(id="data-table"),
            Button("← Back to Menu", id="btn-back", variant="primary"),
            id="dashboard-container",
        )

    def on_mount(self) -> None:
        """Initialize the dashboard when mounted."""
        table = self.query_one("#data-table", DataTable)
        table.add_columns("ID", "Name", "Status", "Value")
        table.add_rows(
            [
                ("001", "Alpha", "Active", "42"),
                ("002", "Beta", "Inactive", "38"),
                ("003", "Gamma", "Active", "55"),
                ("004", "Delta", "Active", "29"),
                ("005", "Epsilon", "Pending", "44"),
            ]
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "btn-back":
            self.app.pop_screen()

    def action_go_back(self) -> None:
        """Return to previous screen."""
        self.app.pop_screen()

    def action_refresh_data(self) -> None:
        """Refresh dashboard data (placeholder)."""
        # In a real app, this would reload data from a source
        self.notify("Data refreshed!")

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()


class SampleTUIApp(App):
    """A sample Textual TUI application for testing."""

    CSS = """
    Screen {
        align: center middle;
    }

    #main-menu, #settings-container, #dashboard-container {
        width: 80;
        height: auto;
        border: solid $primary;
        padding: 2;
    }

    #title {
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    #subtitle, #settings-title, #dashboard-title {
        text-align: center;
        margin-bottom: 2;
    }

    #button-container {
        align: center middle;
        height: auto;
        margin-top: 2;
    }

    Button {
        margin: 0 1;
    }

    #settings-controls {
        margin: 2 0;
    }

    #settings-controls Horizontal {
        height: 3;
        align: center middle;
    }

    #settings-controls Label {
        width: 20;
    }

    #stats-container {
        height: 3;
        margin: 1 0;
    }

    #stats-container Static {
        border: solid $secondary;
        padding: 0 2;
        margin: 0 1;
    }

    DataTable {
        height: 10;
        margin: 1 0;
    }
    """

    SCREENS = {
        "main": MainMenuScreen,
        "settings": SettingsScreen,
        "dashboard": DashboardScreen,
    }

    def on_mount(self) -> None:
        """Initialize the application."""
        self.push_screen("main")


if __name__ == "__main__":
    app = SampleTUIApp()
    app.run()
