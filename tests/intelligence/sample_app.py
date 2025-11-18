"""Sample Textual application for testing AST analyzer.

This is a simple TUI app that demonstrates the patterns the AST analyzer
is designed to detect and extract.
"""

from textual.app import App
from textual.screen import Screen, ModalScreen
from textual.widgets import Button, Static, Input, DataTable
from textual.binding import Binding
from textual.containers import Container


class MainMenuScreen(Screen):
    """Main menu screen - entry point of the application."""

    BINDINGS = [
        Binding("q", "quit", "Quit Application"),
        Binding("s", "show_settings", "Settings", show=True),
        Binding("h", "show_help", "Help", show=True),
        Binding("d", "show_data", "View Data", show=True),
    ]

    def compose(self):
        """Create child widgets."""
        yield Static("Welcome to Sample TUI App", id="title", classes="title")
        yield Container(
            Button("View Data", id="btn-data", variant="primary"),
            Button("Settings", id="btn-settings"),
            Button("Help", id="btn-help"),
            Button("Quit", id="btn-quit", variant="error"),
            id="button-container",
        )

    def action_quit(self):
        """Quit the application."""
        self.app.exit()

    def action_show_settings(self):
        """Navigate to settings screen."""
        self.app.push_screen("SettingsScreen")

    def action_show_help(self):
        """Navigate to help screen."""
        self.app.push_screen("HelpScreen")

    def action_show_data(self):
        """Navigate to data screen."""
        self.app.push_screen("DataScreen")


class SettingsScreen(Screen):
    """Settings configuration screen."""

    BINDINGS = [
        Binding("escape", "back", "Back to Menu"),
        Binding("s", "save", "Save Settings"),
    ]

    def compose(self):
        """Create child widgets."""
        yield Static("Settings", id="header")
        yield Input(placeholder="Username", id="input-username")
        yield Input(placeholder="Email", id="input-email", password=True)
        yield Button("Save", id="btn-save", variant="success")
        yield Button("Cancel", id="btn-cancel")

    def action_back(self):
        """Return to previous screen."""
        self.app.pop_screen()

    def action_save(self):
        """Save settings and return."""
        # Save logic would go here
        self.app.pop_screen()


class DataScreen(Screen):
    """Data display screen with table."""

    BINDINGS = [
        Binding("escape", "back", "Back"),
        Binding("r", "refresh", "Refresh Data"),
    ]

    def compose(self):
        """Create child widgets."""
        yield Static("Data View", id="header")
        yield DataTable(id="data-table")
        yield Button("Refresh", id="btn-refresh")
        yield Button("Back", id="btn-back")

    def action_back(self):
        """Return to main menu."""
        self.app.pop_screen()

    def action_refresh(self):
        """Refresh the data table."""
        # Refresh logic would go here
        pass


class HelpScreen(ModalScreen):
    """Help modal screen."""

    BINDINGS = [
        Binding("escape", "close", "Close"),
    ]

    def compose(self):
        """Create child widgets."""
        yield Container(
            Static("Help Information", id="help-title"),
            Static("Press 'q' to quit", id="help-quit"),
            Static("Press 's' for settings", id="help-settings"),
            Static("Press 'h' for this help", id="help-help"),
            Button("Close", id="btn-close"),
            id="help-dialog",
        )

    def action_close(self):
        """Close the help modal."""
        self.app.pop_screen()


class SampleApp(App):
    """Sample Textual application."""

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=False),
    ]

    def on_mount(self):
        """Install screens."""
        self.install_screen(MainMenuScreen(), name="MainMenuScreen")
        self.install_screen(SettingsScreen(), name="SettingsScreen")
        self.install_screen(DataScreen(), name="DataScreen")
        self.install_screen(HelpScreen(), name="HelpScreen")

        # Start with main menu
        self.push_screen("MainMenuScreen")


if __name__ == "__main__":
    app = SampleApp()
    app.run()
