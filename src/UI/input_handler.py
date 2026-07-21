from src.UI.input_controllers import (
    InputState,
    ToolController,
    CameraController,
    BuildController,
    WindowController,
)
import pygame

class InputHandler:
    """Coordinates keyboard, mouse, camera, build and window input."""

    def __init__(self, game_manager, camera, tile_size=16):
        self.game_manager = game_manager
        self.camera = camera
        self.tile_size = tile_size

        self.state = InputState()

        self.tool_controller = ToolController()

        self.camera_controller = CameraController(
            camera=camera,
            state=self.state
        )

        self.build_controller = BuildController(
            game_manager=game_manager,
            tool_controller=self.tool_controller,
            state=self.state
        )

        self.window_controller = WindowController(
            game_manager=game_manager,
            camera=camera
        )

    # ---------------------------------------------------------
    # Compatibility properties
    # ---------------------------------------------------------

    @property
    def selected_tool(self):
        return self.tool_controller.selected_tool

    @property
    def tool_groups(self):
        return self.tool_controller.tool_groups

    @property
    def current_direction(self):
        return self.tool_controller.current_direction

    @property
    def interaction_mode(self):
        return self.tool_controller.interaction_mode

    @property
    def hovered_grid(self):
        return self.state.hovered_grid

    @property
    def windows(self):
        return self.window_controller.windows

    @property
    def active_window(self):
        return self.window_controller.active_window

    @active_window.setter
    def active_window(self, value):
        self.window_controller.active_window = value

    # ---------------------------------------------------------
    # Window events
    # ---------------------------------------------------------

    def handle_window_event(self, event):
        return self.window_controller.handle_event(event)

    # ---------------------------------------------------------
    # Keyboard
    # ---------------------------------------------------------

    def handle_keydown(self, key):
        if self.window_controller.has_active_window:
            return

        if self.window_controller.handle_shortcut(key):
            return

        self.tool_controller.handle_keydown(key)

    # ---------------------------------------------------------
    # Mouse
    # ---------------------------------------------------------

    def handle_mouse_down(self, x, y, button):
        if self.window_controller.has_active_window:
            return

        grid_x, grid_y = self.camera.screen_to_world(x, y)

        if button == 1:
            self._handle_left_mouse_down(
                x,
                y,
                grid_x,
                grid_y
            )

        elif (
            button == 3
            and self.interaction_mode == "BUILD"
        ):
            self.build_controller.begin_destroy(
                grid_x,
                grid_y
            )

    def _handle_left_mouse_down(
        self,
        mouse_x,
        mouse_y,
        grid_x,
        grid_y
    ):
        if self.interaction_mode == "BUILD":
            self.build_controller.begin_build(
                grid_x,
                grid_y
            )
            return

        entity = self.game_manager.game_map.get_block_at(
            grid_x,
            grid_y
        )

        if entity is not None:
            self.window_controller.open_for_entity(entity)
            return

        self.camera_controller.start_pan(
            mouse_x,
            mouse_y
        )

    def handle_mouse_up(self, button):
        if button == 1:
            self.camera_controller.stop_pan()
            self.build_controller.stop_build()

        elif button == 3:
            self.build_controller.stop_destroy()

    def handle_mouse_motion(self, x, y):
        grid_x, grid_y = (
            self.camera_controller.handle_mouse_motion(
                x,
                y
            )
        )

        self.build_controller.handle_drag(
            grid_x,
            grid_y
        )

    def handle_zoom(self, y_scroll, mouse_x, mouse_y):
        self.camera_controller.handle_zoom(
            y_scroll,
            mouse_x,
            mouse_y
        )

    # ---------------------------------------------------------
    # Preview support
    # ---------------------------------------------------------

    def create_preview_entity(self, x, y):
        return self.build_controller.create_entity(x, y)

    # Temporary backward-compatible alias.
    def _create_entity(
        self,
        x,
        y,
        override_in_dir=None,
        override_out_dir=None
    ):
        return self.build_controller.create_entity(
            x,
            y,
            override_in_dir,
            override_out_dir
        )

    # ---------------------------------------------------------
    # Per-frame update
    # ---------------------------------------------------------

    def update(self):
        if not self.state.is_building:
            return

        camera_moved = self.camera_controller.auto_pan()

        if not camera_moved:
            return

        mouse_x, mouse_y = pygame.mouse.get_pos()

        self.handle_mouse_motion(
            mouse_x,
            mouse_y
        )