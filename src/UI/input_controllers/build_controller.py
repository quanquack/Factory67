import src.entities


OPPOSITE_DIRS = {
    "N": "S",
    "E": "W",
    "S": "N",
    "W": "E",
}


class BuildController:
    """Handles entity creation, placement, removal and drag building."""

    def __init__(
        self,
        game_manager,
        tool_controller,
        state
    ):
        self.game_manager = game_manager
        self.tool_controller = tool_controller
        self.state = state

    def begin_build(self, grid_x: int, grid_y: int) -> None:
        self.state.is_building = True
        self.state.custom_in_dir = None
        self.state.last_interacted_grid = (
            grid_x,
            grid_y
        )

        self._handle_action(
            grid_x,
            grid_y,
            build=True
        )

    def begin_destroy(
        self,
        grid_x: int,
        grid_y: int
    ) -> None:
        self.state.is_destroying = True
        self.state.last_interacted_grid = (
            grid_x,
            grid_y
        )

        self._handle_action(
            grid_x,
            grid_y,
            build=False
        )

    def stop_build(self) -> None:
        self.state.is_building = False
        self.state.last_interacted_grid = None
        self.state.custom_in_dir = None

    def stop_destroy(self) -> None:
        self.state.is_destroying = False
        self.state.last_interacted_grid = None

    def handle_drag(
        self,
        grid_x: int,
        grid_y: int
    ) -> None:
        if not (
            self.state.is_building
            or self.state.is_destroying
        ):
            return

        current_grid = (grid_x, grid_y)

        if current_grid == self.state.last_interacted_grid:
            return

        if (
            self.state.is_building
            and self.tool_controller.selected_tool == "conveyor"
            and self.state.last_interacted_grid is not None
        ):
            self._extend_conveyor_path(current_grid)
            return

        self._handle_action(
            grid_x,
            grid_y,
            build=self.state.is_building
        )

        self.state.last_interacted_grid = current_grid

    def _extend_conveyor_path(
        self,
        target_grid: tuple[int, int]
    ) -> None:
        while self.state.last_interacted_grid != target_grid:
            previous_x, previous_y = (
                self.state.last_interacted_grid
            )
            target_x, target_y = target_grid

            difference_x = target_x - previous_x
            difference_y = target_y - previous_y

            if difference_x == 0 and difference_y == 0:
                break

            next_x, next_y = previous_x, previous_y

            if abs(difference_x) > abs(difference_y):
                next_x += 1 if difference_x > 0 else -1
            else:
                next_y += 1 if difference_y > 0 else -1

            direction = self._get_drag_direction(
                previous_x,
                previous_y,
                next_x,
                next_y
            )

            self._update_previous_conveyor(
                previous_x,
                previous_y,
                direction
            )

            game_map = self.game_manager.game_map

            if game_map.get_block_at(next_x, next_y) is not None:
                break

            input_direction = OPPOSITE_DIRS[direction]

            self._handle_action(
                next_x,
                next_y,
                build=True,
                override_in_dir=input_direction,
                override_out_dir=direction
            )

            self.state.last_interacted_grid = (
                next_x,
                next_y
            )

    @staticmethod
    def _get_drag_direction(
        previous_x: int,
        previous_y: int,
        next_x: int,
        next_y: int
    ) -> str:
        dx = next_x - previous_x
        dy = next_y - previous_y

        if dx > 0:
            return "E"
        if dx < 0:
            return "W"
        if dy > 0:
            return "S"

        return "N"

    def _update_previous_conveyor(
        self,
        grid_x: int,
        grid_y: int,
        direction: str
    ) -> None:
        game_map = self.game_manager.game_map
        previous_block = game_map.get_block_at(
            grid_x,
            grid_y
        )

        if (
            previous_block is None
            or type(previous_block).__name__ != "Conveyor"
        ):
            return

        previous_block.output_dir = direction

        if getattr(
            previous_block,
            "input_dir",
            None
        ) == direction:
            previous_block.input_dir = (
                OPPOSITE_DIRS[direction]
            )

        connection = getattr(
            previous_block,
            "connection",
            None
        )

        if connection is not None:
            connection.update_outbound(game_map)

    def _handle_action(
        self,
        grid_x: int,
        grid_y: int,
        build: bool,
        override_in_dir: str | None = None,
        override_out_dir: str | None = None
    ) -> None:
        game_map = self.game_manager.game_map

        if not build:
            game_map.remove_block(grid_x, grid_y)
            return

        if game_map.get_block_at(grid_x, grid_y) is not None:
            return

        new_block = self.create_entity(
            grid_x,
            grid_y,
            override_in_dir,
            override_out_dir
        )

        if new_block is not None:
            game_map.place_block(new_block)

    def create_entity(
        self,
        x: int,
        y: int,
        override_in_dir: str | None = None,
        override_out_dir: str | None = None
    ):
        output_direction = (
            override_out_dir
            or self.tool_controller.current_direction
        )

        if override_in_dir is not None:
            input_direction = override_in_dir
        elif self.state.custom_in_dir is not None:
            input_direction = self.state.custom_in_dir
        else:
            input_direction = OPPOSITE_DIRS[
                output_direction
            ]

        if input_direction == output_direction:
            input_direction = OPPOSITE_DIRS[
                output_direction
            ]

        context = src.entities.BuildContext(
            tool=self.tool_controller.selected_tool,
            out_dir=output_direction,
            in_dir=input_direction,
            game_map=self.game_manager.game_map,
            economy=self.game_manager.economy,
            inventory=self.game_manager.inventory,
            game_manager=self.game_manager
        )

        return src.entities.spawn_entity(
            self.tool_controller.selected_tool,
            x,
            y,
            context
        )