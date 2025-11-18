# Sample TUI Application

A complete Textual TUI application demonstrating Orchestro's intelligence system.

## Features

- **3 Screens**: MainMenu, Settings, Dashboard
- **Keyboard Navigation**: Full keyboard support with shortcuts
- **Interactive Widgets**: Buttons, switches, data tables
- **Screen Transitions**: Push/pop navigation between screens

## Quick Start

### Install Dependencies

```bash
pip install textual
```

### Run the App

```bash
python examples/sample_tui_app/app.py
```

Or from the project root:

```bash
python -m examples.sample_tui_app.app
```

## Usage

### Navigation

- **Main Menu** → **Settings**: Press `s` or click "Settings" button
- **Main Menu** → **Dashboard**: Press `d` or click "Dashboard" button
- **Return to Previous Screen**: Press `escape` or click "Back" button
- **Quit Application**: Press `q` or click "Quit" button

### Additional Controls

- **Dashboard**: Press `r` to refresh data (shows notification)
- **Settings**: Toggle switches to change options

## Screen Details

### MainMenuScreen

Entry point of the application with navigation buttons.

**Keybindings:**
- `s` - Go to Settings
- `d` - Go to Dashboard
- `q` - Quit application

**Widgets:**
- Header
- Footer
- 3 Buttons (Settings, Dashboard, Quit)

### SettingsScreen

Configuration screen with toggleable options.

**Keybindings:**
- `escape` - Return to main menu
- `q` - Quit application

**Widgets:**
- Header
- Footer
- 3 Switches (Dark Mode, Notifications, Auto Save)
- Back button

### DashboardScreen

Data display screen with statistics and a table.

**Keybindings:**
- `escape` - Return to main menu
- `r` - Refresh data
- `q` - Quit application

**Widgets:**
- Header
- Footer
- Statistics display (3 stat boxes)
- Data table with 5 rows
- Back button

## Code Structure

```
sample_tui_app/
├── app.py          # Main application file
├── __init__.py     # Package initialization
└── README.md       # This file
```

### Key Classes

- **SampleTUIApp**: Main application class
- **MainMenuScreen**: Entry screen with navigation
- **SettingsScreen**: Configuration screen
- **DashboardScreen**: Data display screen

## Testing

This app is designed to demonstrate Orchestro's intelligent test generation:

```bash
# Generate tests automatically
python examples/demo_intelligence.py

# Run generated tests
orchestro examples/generated_tests/smoke_test.yaml
orchestro examples/generated_tests/keybinding_test.yaml
orchestro examples/generated_tests/navigation_test.yaml
```

## Customization

### Adding a New Screen

1. Create a screen class inheriting from `Screen`
2. Define `BINDINGS` for keybindings
3. Implement `compose()` to add widgets
4. Add screen to `SCREENS` dict in `SampleTUIApp`
5. Add navigation from existing screens

Example:

```python
class HelpScreen(Screen):
    BINDINGS = [
        Binding("escape", "go_back", "Back"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield Static("Help content here")

    def action_go_back(self) -> None:
        self.app.pop_screen()

# Add to app
class SampleTUIApp(App):
    SCREENS = {
        # ... existing screens ...
        "help": HelpScreen,
    }
```

### Adding Keybindings

```python
class MyScreen(Screen):
    BINDINGS = [
        Binding("h", "show_help", "Help"),
        Binding("f", "toggle_fullscreen", "Fullscreen"),
        # key, action, description
    ]

    def action_show_help(self) -> None:
        """Action handler for 'h' key."""
        self.app.push_screen("help")
```

### Styling

Edit the `CSS` class variable in `SampleTUIApp`:

```python
class SampleTUIApp(App):
    CSS = """
    /* Your custom styles here */
    Button {
        margin: 1;
    }
    """
```

## Dependencies

- **textual**: TUI framework (`pip install textual`)
- **Python**: 3.8 or higher

## License

Same as Orchestro project (MIT)

## See Also

- [Intelligence Demo](../INTELLIGENCE_DEMO.md) - Full demo walkthrough
- [Textual Documentation](https://textual.textualize.io/) - Learn more about Textual
- [Orchestro Documentation](../../README.md) - Orchestro testing framework
