from abc import ABC, abstractmethod


class BaseWindow(ABC):
    """Common interface for all game windows."""

    def __init__(self, frame):
        self.frame = frame

    @property
    def is_open(self) -> bool:
        return self.frame.is_open

    def close(self) -> None:
        self.frame.close()

    def handle_close_event(self, event) -> bool:
        return self.frame.handle_close_click(event)

    @abstractmethod
    def handle_event(self, event) -> bool:
        """Handle a Pygame event."""
        raise NotImplementedError

    @abstractmethod
    def draw(self, screen, asset_manager=None) -> None:
        """Draw the window."""
        raise NotImplementedError