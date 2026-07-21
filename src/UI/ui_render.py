import pygame

from src.UI.renderers import (
    WorldRenderer,
    EntityRenderer,
    GhostRenderer,
    HUDRenderer,
)


class UIRenderer:
    """
    Coordinates the rendering pipeline.

    This class does not draw individual game elements itself.
    It delegates rendering responsibilities to specialized renderers.
    """

    def __init__(
        self,
        screen,
        game_manager,
        asset_manager,
        input_handler,
        camera,
        tile_size=16
    ):
        self.screen = screen
        self.game_manager = game_manager
        self.asset_manager = asset_manager
        self.input_handler = input_handler
        self.camera = camera
        self.tile_size = tile_size

        self.world_renderer = WorldRenderer(
            screen=screen,
            game_manager=game_manager,
            camera=camera
        )

        self.entity_renderer = EntityRenderer(
            screen=screen,
            game_manager=game_manager,
            asset_manager=asset_manager,
            camera=camera
        )

        self.ghost_renderer = GhostRenderer(
            screen=screen,
            game_manager=game_manager,
            input_handler=input_handler,
            camera=camera,
            entity_renderer=self.entity_renderer
        )

        self.hud_renderer = HUDRenderer(
            screen=screen,
            game_manager=game_manager,
            asset_manager=asset_manager,
            input_handler=input_handler,
            camera=camera
        )

    def render_frame(self, fps=0):
        self.world_renderer.draw()
        self.entity_renderer.draw()
        self.ghost_renderer.draw()
        self.hud_renderer.draw(fps)

        self._draw_active_window()

        pygame.display.flip()

    def _draw_active_window(self):
        active_window = self.input_handler.active_window

        if active_window is None or not active_window.is_open:
            return

        active_window.draw(
            self.screen,
            self.asset_manager
        )
    
    def set_screen(self, screen):
        self.screen = screen

        self.world_renderer.screen = screen
        self.entity_renderer.screen = screen
        self.ghost_renderer.screen = screen
        self.hud_renderer.screen = screen
