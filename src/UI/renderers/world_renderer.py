import pygame

from src.registry import ore_registry, theme_registry


class WorldRenderer:
    """Renders the game world background, ores and grid."""

    MAX_CHUNK_CACHE = 256

    def __init__(self, screen, game_manager, camera):
        self.screen = screen
        self.game_manager = game_manager
        self.camera = camera

        self.bg_color = theme_registry.get_color("render", "bg")
        self.chunk_surfaces = {}
        self.scaled_cache = {}
        self.last_zoom = camera.zoom

    def draw(self):
        self._clear_scaled_cache_if_zoom_changed()

        self.screen.fill(self.bg_color)
        self._draw_ores()
        self._draw_grid_lines()

    def _clear_scaled_cache_if_zoom_changed(self):
        if self.camera.zoom != self.last_zoom:
            self.scaled_cache.clear()
            self.last_zoom = self.camera.zoom

    def _get_chunk_surface(self, cx, cy):
        cache_key = (cx, cy)

        if cache_key in self.chunk_surfaces:
            return self.chunk_surfaces[cache_key]

        chunk_size = self.game_manager.game_map.chunk_size
        base_size = self.camera.base_tile_size

        surface = pygame.Surface(
            (chunk_size * base_size, chunk_size * base_size),
            pygame.SRCALPHA
        )

        for local_x in range(chunk_size):
            for local_y in range(chunk_size):
                world_x = cx * chunk_size + local_x
                world_y = cy * chunk_size + local_y

                ore_name = self.game_manager.game_map.get_ore_at(
                    world_x,
                    world_y
                )

                if ore_name is None:
                    continue

                color = ore_registry.get_color(ore_name)
                rect = pygame.Rect(
                    local_x * base_size,
                    local_y * base_size,
                    base_size,
                    base_size
                )
                pygame.draw.rect(surface, color, rect)

        if len(self.chunk_surfaces) >= self.MAX_CHUNK_CACHE:
            oldest_key = next(iter(self.chunk_surfaces))
            self.chunk_surfaces.pop(oldest_key)

        self.chunk_surfaces[cache_key] = surface
        return surface

    def _draw_ores(self):
        min_x, max_x, min_y, max_y = self.camera.get_visible_bounds()
        chunk_size = self.game_manager.game_map.chunk_size

        min_cx = min_x // chunk_size
        max_cx = max_x // chunk_size
        min_cy = min_y // chunk_size
        max_cy = max_y // chunk_size

        for cx in range(min_cx, max_cx + 1):
            for cy in range(min_cy, max_cy + 1):
                base_surface = self._get_chunk_surface(cx, cy)

                screen_x, screen_y = self.camera.world_to_screen(
                    cx * chunk_size,
                    cy * chunk_size
                )

                next_x, next_y = self.camera.world_to_screen(
                    (cx + 1) * chunk_size,
                    (cy + 1) * chunk_size
                )

                exact_size = chunk_size * self.camera.base_tile_size * self.camera.zoom

                target_width = int(exact_size) + 1
                target_height = int(exact_size) + 1

                if target_width <= 0 or target_height <= 0:
                    continue

                if self.camera.zoom == 1.0:
                    surface = base_surface
                else:
                    cache_key = (
                        id(base_surface),
                        target_width,
                        target_height
                    )

                    if cache_key not in self.scaled_cache:
                        self.scaled_cache[cache_key] = pygame.transform.scale(
                            base_surface,
                            (target_width, target_height)
                        )

                    surface = self.scaled_cache[cache_key]

                self.screen.blit(surface, (screen_x, screen_y))

    def _draw_grid_lines(self):
        min_x, max_x, min_y, max_y = self.camera.get_visible_bounds()
        grid_color = theme_registry.get_color("render", "grid")

        for grid_x in range(min_x, max_x + 1):
            screen_x, _ = self.camera.world_to_screen(grid_x, 0)
            pygame.draw.line(
                self.screen,
                grid_color,
                (screen_x, 0),
                (screen_x, self.camera.height)
            )

        for grid_y in range(min_y, max_y + 1):
            _, screen_y = self.camera.world_to_screen(0, grid_y)
            pygame.draw.line(
                self.screen,
                grid_color,
                (0, screen_y),
                (self.camera.width, screen_y)
            )
