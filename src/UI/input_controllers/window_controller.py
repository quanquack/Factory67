import pygame

from src.UI.windows import (
    MachineWindow,
    StorageWindow,
    RouterConfigWindow,
    RecipeUnlockWindow,
    VictoryWindow,
    StatisticsWindow,
)


class WindowController:
    """Creates, opens and routes events to game windows."""

    def __init__(self, game_manager, camera):
        self.game_manager = game_manager

        self.windows = {
            "machine": MachineWindow(
                camera.width,
                camera.height,
                game_manager
            ),
            "storage": StorageWindow(
                camera.width,
                camera.height
            ),
            "router": RouterConfigWindow(
                camera.width,
                camera.height
            ),
            "recipe_unlock": RecipeUnlockWindow(
                camera.width,
                camera.height,
                game_manager.economy
            ),
            "victory": VictoryWindow(
                camera.width,
                camera.height
            ),
            "statistics": StatisticsWindow(
                camera.width,
                camera.height,
                game_manager
            ),
        }

        self.active_window = None

    @property
    def has_active_window(self) -> bool:
        return (
            self.active_window is not None
            and self.active_window.is_open
        )

    def handle_event(self, event) -> bool:
        if not self.has_active_window:
            return False

        self.active_window.handle_event(event)

        if not self.active_window.is_open:
            self.active_window = None

        return True

    def handle_shortcut(self, key: int) -> bool:
        if key == pygame.K_b:
            self.open_recipe_unlock()
            return True

        if key == pygame.K_t:
            self.open_statistics()
            return True

        return False

    def open_recipe_unlock(self) -> None:
        window = self.windows["recipe_unlock"]
        window.open(self.game_manager.inventory)
        self.active_window = window

    def open_statistics(self) -> None:
        window = self.windows["statistics"]
        window.open()
        self.active_window = window

    def open_for_entity(self, entity) -> bool:
        class_name = type(entity).__name__

        if class_name in ("Machine", "Miner"):
            window = self.windows["machine"]
        elif class_name == "CentralStorage":
            window = self.windows["storage"]
        elif class_name == "Router":
            window = self.windows["router"]
        else:
            return False

        window.open(entity)
        self.active_window = window
        return True