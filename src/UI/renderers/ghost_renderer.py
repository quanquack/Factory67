import pygame


class GhostRenderer:
    """Renders placement previews and hovered-tile highlights."""

    def __init__(
        self,
        screen,
        game_manager,
        input_handler,
        camera,
        entity_renderer
    ):
        self.screen = screen
        self.game_manager = game_manager
        self.input_handler = input_handler
        self.camera = camera
        self.entity_renderer = entity_renderer

    def draw(self):
        grid_x, grid_y = self.input_handler.hovered_grid
        mode = self.input_handler.interaction_mode

        if mode == "BUILD":
            self._draw_build_preview(grid_x, grid_y)
        elif mode == "PAN":
            self._draw_tile_highlight(grid_x, grid_y)

    def _draw_build_preview(self, grid_x, grid_y):
        existing_block = self.game_manager.game_map.get_block_at(
            grid_x,
            grid_y
        )

        if existing_block is not None:
            return

        temporary_entity = self.input_handler.create_preview_entity(
                grid_x, 
                grid_y
                )
        
        if temporary_entity is None:
            return

        self.entity_renderer.draw_entity(
            temporary_entity,
            grid_x,
            grid_y,
            is_ghost=True
        )

    def _draw_tile_highlight(self, grid_x, grid_y):
        pixel_x, pixel_y = self.camera.world_to_screen(
            grid_x,
            grid_y
        )
        size = self.camera.actual_tile_size

        highlight = pygame.Surface(
            (size, size),
            pygame.SRCALPHA
        )
        highlight.fill((255, 255, 255, 30))

        pygame.draw.rect(
            highlight,
            (255, 255, 255, 100),
            highlight.get_rect(),
            1
        )

        self.screen.blit(highlight, (pixel_x, pixel_y))
