"""Data models for storing application knowledge discovered by the intelligence system."""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional
from pathlib import Path


@dataclass
class KeybindingInfo:
    """Information about a keyboard binding."""

    key: str
    action: str
    description: str
    show_in_footer: bool = True


@dataclass
class WidgetInfo:
    """Information about a widget on a screen."""

    widget_type: str
    widget_id: Optional[str] = None
    attributes: Dict[str, str] = field(default_factory=dict)


@dataclass
class ScreenInfo:
    """Information about a screen in the application."""

    name: str
    class_name: str
    file_path: Path
    keybindings: List[KeybindingInfo] = field(default_factory=list)
    widgets: List[WidgetInfo] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)
    navigation_targets: Set[str] = field(default_factory=set)

    def has_keybinding(self, key: str) -> bool:
        """Check if screen has a specific keybinding."""
        return any(kb.key == key for kb in self.keybindings)

    def get_keybinding(self, key: str) -> Optional[KeybindingInfo]:
        """Get keybinding information for a specific key."""
        for kb in self.keybindings:
            if kb.key == key:
                return kb
        return None


@dataclass
class NavigationPath:
    """A path through the application's screens."""

    start_screen: str
    end_screen: str
    steps: List[Dict[str, str]] = field(default_factory=list)
    cost: int = 0

    def add_step(self, action_type: str, action: str, target_screen: str) -> None:
        """Add a navigation step to the path."""
        self.steps.append({
            "type": action_type,  # "keybinding" or "button"
            "action": action,
            "target": target_screen,
        })
        self.cost += 1


@dataclass
class AppKnowledge:
    """Complete knowledge base about a TUI application."""

    project_path: Path
    screens: Dict[str, ScreenInfo] = field(default_factory=dict)
    entry_screen: Optional[str] = None
    navigation_paths: List[NavigationPath] = field(default_factory=list)

    def add_screen(self, screen: ScreenInfo) -> None:
        """Add a screen to the knowledge base."""
        self.screens[screen.name] = screen

    def get_screen(self, name: str) -> Optional[ScreenInfo]:
        """Get screen information by name."""
        return self.screens.get(name)

    def get_all_keybindings(self) -> Dict[str, List[KeybindingInfo]]:
        """Get all keybindings organized by screen."""
        return {
            screen_name: screen.keybindings
            for screen_name, screen in self.screens.items()
        }

    def find_navigation_path(
        self, start: str, end: str
    ) -> Optional[NavigationPath]:
        """Find a navigation path between two screens."""
        for path in self.navigation_paths:
            if path.start_screen == start and path.end_screen == end:
                return path
        return None

    def to_dict(self) -> dict:
        """Convert knowledge to dictionary for serialization."""
        return {
            "project_path": str(self.project_path),
            "entry_screen": self.entry_screen,
            "screens": {
                name: {
                    "name": screen.name,
                    "class_name": screen.class_name,
                    "file_path": str(screen.file_path),
                    "keybindings": [
                        {
                            "key": kb.key,
                            "action": kb.action,
                            "description": kb.description,
                            "show_in_footer": kb.show_in_footer,
                        }
                        for kb in screen.keybindings
                    ],
                    "widgets": [
                        {
                            "type": w.widget_type,
                            "id": w.widget_id,
                            "attributes": w.attributes,
                        }
                        for w in screen.widgets
                    ],
                    "methods": screen.methods,
                    "navigation_targets": list(screen.navigation_targets),
                }
                for name, screen in self.screens.items()
            },
            "navigation_paths": [
                {
                    "start": path.start_screen,
                    "end": path.end_screen,
                    "steps": path.steps,
                    "cost": path.cost,
                }
                for path in self.navigation_paths
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AppKnowledge":
        """Create knowledge from dictionary."""
        knowledge = cls(project_path=Path(data["project_path"]))
        knowledge.entry_screen = data.get("entry_screen")

        # Reconstruct screens
        for screen_name, screen_data in data.get("screens", {}).items():
            screen = ScreenInfo(
                name=screen_data["name"],
                class_name=screen_data["class_name"],
                file_path=Path(screen_data["file_path"]),
                keybindings=[
                    KeybindingInfo(
                        key=kb["key"],
                        action=kb["action"],
                        description=kb["description"],
                        show_in_footer=kb.get("show_in_footer", True),
                    )
                    for kb in screen_data.get("keybindings", [])
                ],
                widgets=[
                    WidgetInfo(
                        widget_type=w["type"],
                        widget_id=w.get("id"),
                        attributes=w.get("attributes", {}),
                    )
                    for w in screen_data.get("widgets", [])
                ],
                methods=screen_data.get("methods", []),
                navigation_targets=set(screen_data.get("navigation_targets", [])),
            )
            knowledge.add_screen(screen)

        # Reconstruct navigation paths
        for path_data in data.get("navigation_paths", []):
            path = NavigationPath(
                start_screen=path_data["start"],
                end_screen=path_data["end"],
                steps=path_data["steps"],
                cost=path_data["cost"],
            )
            knowledge.navigation_paths.append(path)

        return knowledge
