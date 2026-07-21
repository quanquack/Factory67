class Camera:
    """
    Manages the player's viewport, handling panning and zooming operations.
    """
    def __init__(self, screen_width, screen_height, base_tile_size=16):
        """
        Initialize the camera with screen dimensions and base tile size.

        Args:
            screen_width (int): Width of the screen in pixels.
            screen_height (int): Height of the screen in pixels.
            base_tile_size (int, optional): Original size of a tile in pixels. Defaults to 16.
        """
        self.width = screen_width
        self.height = screen_height
        self.base_tile_size = base_tile_size
        
        # Camera state
        self.zoom = 1.0
        self.offset_x = screen_width / 2.0 
        self.offset_y = screen_height / 2.0 

    @property
    def actual_tile_size(self):
        """
        Compute the effective tile size after applying zoom.

        Returns:
            int: The scaled tile size, always at least 1 pixel.
        """
        return max(1, int(self.base_tile_size * self.zoom))

    def screen_to_world(self, screen_x, screen_y):
        """
        Convert screen pixel coordinates to grid coordinates.

        Args:
            screen_x (float): X coordinate on the screen (e.g., mouse position).
            screen_y (float): Y coordinate on the screen.

        Returns:
            Tuple[int, int]: Corresponding grid coordinates (grid_x, grid_y).
        """ 
        world_x = (screen_x - self.offset_x) / self.zoom
        world_y = (screen_y - self.offset_y) / self.zoom
        grid_x = int(world_x // self.base_tile_size)
        grid_y = int(world_y // self.base_tile_size)
        return (grid_x, grid_y)

    def world_to_screen(self, grid_x, grid_y):
        """
        Convert grid coordinates to screen pixel coordinates.

        Args:
            grid_x (int): Grid X coordinate.
            grid_y (int): Grid Y coordinate.

        Returns:
            Tuple[int, int]: Screen pixel coordinates (screen_x, screen_y).
        """
        screen_x = (grid_x * self.base_tile_size * self.zoom) + self.offset_x
        screen_y = (grid_y * self.base_tile_size * self.zoom) + self.offset_y
        return (int(screen_x), int(screen_y))

    def get_visible_bounds(self):
        """
        Calculate the grid bounds currently visible on the screen.

        This method is typically used for culling (render optimization),
        by determining which tiles are within the visible area.

        Returns:
            Tuple[int, int, int, int]:
                (min_grid_x, max_grid_x, min_grid_y, max_grid_y) representing
                the visible grid range with a small margin.
        """
        min_grid_x, min_grid_y = self.screen_to_world(0, 0)
        max_grid_x, max_grid_y = self.screen_to_world(self.width, self.height)
        return (min_grid_x - 1, max_grid_x + 1, min_grid_y - 1, max_grid_y + 1)
    
    def set_screen(self, screen):
        self.screen = screen

        width, height = screen.get_size()
        self.camera.width = width
        self.camera.height = height

        for child_renderer in (
            self.world_renderer,
            self.entity_renderer,
            self.ghost_renderer,
            self.hud_renderer,
        ):
            child_renderer.screen = screen  