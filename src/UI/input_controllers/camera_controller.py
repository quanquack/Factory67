import pygame


class CameraController:
    """Handles camera panning, zooming and hover coordinates."""

    ZOOM_FACTOR = 1.15
    MIN_ZOOM = 1.0
    MAX_ZOOM = 6.0

    EDGE_MARGIN = 40
    AUTO_PAN_SPEED = 15.0

    def __init__(self, camera, state):
        self.camera = camera
        self.state = state

    def handle_zoom(
        self,
        y_scroll: int,
        mouse_x: float,
        mouse_y: float
    ) -> None:
        old_zoom = self.camera.zoom

        if y_scroll > 0:
            new_zoom = min(
                self.MAX_ZOOM,
                old_zoom * self.ZOOM_FACTOR
            )
        elif y_scroll < 0:
            new_zoom = max(
                self.MIN_ZOOM,
                old_zoom / self.ZOOM_FACTOR
            )
        else:
            return

        if new_zoom == old_zoom:
            return

        world_x = (
            mouse_x - self.camera.offset_x
        ) / old_zoom

        world_y = (
            mouse_y - self.camera.offset_y
        ) / old_zoom

        self.camera.zoom = new_zoom

        self.camera.offset_x = (
            mouse_x - world_x * new_zoom
        )
        self.camera.offset_y = (
            mouse_y - world_y * new_zoom
        )

    def start_pan(self, x: float, y: float) -> None:
        self.state.is_panning = True
        self.state.last_mouse_pos = (x, y)

    def stop_pan(self) -> None:
        self.state.is_panning = False

    def handle_mouse_motion(
        self,
        x: float,
        y: float
    ) -> tuple[int, int]:
        if self.state.is_panning:
            self._pan_from_mouse_motion(x, y)

        grid_position = self.camera.screen_to_world(x, y)
        self.state.hovered_grid = grid_position

        return grid_position

    def _pan_from_mouse_motion(
        self,
        x: float,
        y: float
    ) -> None:
        previous_x, previous_y = (
            self.state.last_mouse_pos
        )

        dx = x - previous_x
        dy = y - previous_y

        self.camera.offset_x += dx
        self.camera.offset_y += dy

        self.state.last_mouse_pos = (x, y)

    def auto_pan(self) -> bool:
        """
        Move the camera when the mouse is near a screen edge.

        Returns:
            True if the camera was moved.
        """
        mouse_x, mouse_y = pygame.mouse.get_pos()

        dx = 0.0
        dy = 0.0

        if mouse_x <= self.EDGE_MARGIN:
            dx = self.AUTO_PAN_SPEED
        elif mouse_x >= self.camera.width - self.EDGE_MARGIN:
            dx = -self.AUTO_PAN_SPEED

        if mouse_y <= self.EDGE_MARGIN:
            dy = self.AUTO_PAN_SPEED
        elif mouse_y >= self.camera.height - self.EDGE_MARGIN:
            dy = -self.AUTO_PAN_SPEED

        if dx == 0 and dy == 0:
            return False

        self.camera.offset_x += dx
        self.camera.offset_y += dy

        return True