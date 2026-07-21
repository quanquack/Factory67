from dataclasses import dataclass


GridPosition = tuple[int, int]


@dataclass
class InputState:
    """Stores temporary mouse and interaction state."""

    hovered_grid: GridPosition = (0, 0)

    is_panning: bool = False
    last_mouse_pos: tuple[float, float] = (0, 0)

    is_building: bool = False
    is_destroying: bool = False

    last_interacted_grid: GridPosition | None = None
    custom_in_dir: str | None = None