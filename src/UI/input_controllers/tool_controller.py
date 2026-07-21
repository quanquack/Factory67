import pygame

from src.registry import machine_registry


class ToolController:
    """Manages tool selection, direction and interaction mode."""

    DIRECTIONS = ("N", "E", "S", "W")

    def __init__(self):
        machine_tools = [
            name
            for name, data in machine_registry.machine_data.items()
            if data["metadata"].get("class_name") == "Machine"
        ]

        self.tool_groups = [
            ["miner"],
            machine_tools,
            ["conveyor"],
            ["merger"],
            ["splitter", "filter"],
        ]

        self.group_indices = [0] * len(self.tool_groups)
        self.selected_slot = 0

        self.current_direction = "E"
        self.interaction_mode = "PAN"

    @property
    def selected_tool(self) -> str:
        return self.tool_groups[
            self.selected_slot
        ][
            self.group_indices[self.selected_slot]
        ]

    def handle_keydown(self, key: int) -> bool:
        """
        Handle tool-related keyboard input.

        Returns:
            True if the key was handled.
        """
        if pygame.K_1 <= key <= pygame.K_9:
            self._select_tool_group(key)
            return True

        if key == pygame.K_r:
            self.rotate_direction()
            return True

        if key == pygame.K_q:
            self.toggle_interaction_mode()
            return True

        return False

    def _select_tool_group(self, key: int) -> None:
        index = key - pygame.K_1

        if index >= len(self.tool_groups):
            return
        
        group_size = len(self.tool_groups[index])

        if group_size == 0:
            return 
        
        if self.selected_slot == index:
            self.group_indices[index] = (
                self.group_indices[index] + 1
            ) % group_size
        else:
            self.selected_slot = index

    def rotate_direction(self) -> None:
        current_index = self.DIRECTIONS.index(
            self.current_direction
        )

        next_index = (current_index + 1) % len(
            self.DIRECTIONS
        )

        self.current_direction = self.DIRECTIONS[next_index]

    def toggle_interaction_mode(self) -> None:
        if self.interaction_mode == "BUILD":
            self.interaction_mode = "PAN"
        else:
            self.interaction_mode = "BUILD"