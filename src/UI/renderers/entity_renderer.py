import pygame

from src.registry import theme_registry

OPPOSITE_DIRS = {'N': 'S', 'E': 'W', 'S': 'N', 'W': 'E'}

class EntityRenderer:
    """Renders machines, buildings and transported items."""

    NON_ROTATING_ENTITIES = {
        "Conveyor",
        "CentralStorage",
        "Seller"
    }

    DIRECTION_ANGLES = {
        "S": 0,
        "E": 90,
        "N": 180,
        "W": -90
    }

    def __init__(self, screen, game_manager, asset_manager, camera):
        self.screen = screen
        self.game_manager = game_manager
        self.asset_manager = asset_manager
        self.camera = camera

        self.scaled_cache = {}
        self.last_zoom = camera.zoom

    def draw(self):
        self._clear_cache_if_zoom_changed()

        min_x, max_x, min_y, max_y = self.camera.get_visible_bounds()
        rendered_entities = set()

        # Vẽ thân các entity.
        for grid_x in range(min_x, max_x + 1):
            for grid_y in range(min_y, max_y + 1):
                entity = self.game_manager.game_map.get_block_at(
                    grid_x,
                    grid_y
                )

                if entity is None or entity in rendered_entities:
                    continue

                self.draw_entity(
                    entity,
                    entity.position.x,
                    entity.position.y
                )
                rendered_entities.add(entity)

        # Vẽ item sau entity để item nằm trên conveyor.
        for entity in rendered_entities:
            if hasattr(entity, "items"):
                self._draw_conveyor_items(
                    entity,
                    entity.position.x,
                    entity.position.y
                )

    def _clear_cache_if_zoom_changed(self):
        if self.camera.zoom != self.last_zoom:
            self.scaled_cache.clear()
            self.last_zoom = self.camera.zoom

    def draw_entity(self, entity, grid_x, grid_y, is_ghost=False):
        pixel_x, pixel_y = self.camera.world_to_screen(grid_x, grid_y)

        machine_name = entity.get_asset_name()
        class_name = type(entity).__name__

        angle = self._get_entity_angle(entity, class_name)
        surface = self.asset_manager.get_machine_asset(
            machine_name,
            angle
        )

        width_tiles = getattr(entity, "width", 1)
        height_tiles = getattr(entity, "height", 1)
        current_size = self.camera.actual_tile_size

        target_width = current_size * width_tiles
        target_height = current_size * height_tiles

        surface = self._get_scaled_surface(
            surface,
            machine_name,
            angle,
            target_width,
            target_height
        )

        level = getattr(entity, "level", 1)
        background = self.asset_manager.get_tier_background(
            level,
            target_width,
            target_height
        )

        entity_rect = pygame.Rect(
            pixel_x,
            pixel_y,
            target_width,
            target_height
        )

        if is_ghost:
            self._draw_ghost_surface(
                background,
                surface,
                pixel_x,
                pixel_y
            )
            return

        machine_border = theme_registry.get_color(
            "render",
            "machine_border"
        )

        self.screen.blit(background, (pixel_x, pixel_y))
        pygame.draw.rect(
            self.screen,
            machine_border,
            entity_rect,
            2
        )
        self.screen.blit(surface, (pixel_x, pixel_y))

    def _get_entity_angle(self, entity, class_name):
        if class_name in self.NON_ROTATING_ENTITIES:
            return 0

        input_direction = getattr(entity, "input_dir", "N")
        default_direction = OPPOSITE_DIRS[input_direction]
        direction = getattr(entity, "output_dir", default_direction)

        return self.DIRECTION_ANGLES.get(direction, 0)

    def _get_scaled_surface(
        self,
        surface,
        machine_name,
        angle,
        target_width,
        target_height
    ):
        if (
            surface.get_width() == target_width
            and surface.get_height() == target_height
        ):
            return surface

        cache_key = (
            f"entity_{machine_name}_{angle}",
            target_width,
            target_height
        )

        if cache_key not in self.scaled_cache:
            self.scaled_cache[cache_key] = pygame.transform.scale(
                surface,
                (target_width, target_height)
            )

        return self.scaled_cache[cache_key]

    def _draw_ghost_surface(
        self,
        background,
        surface,
        pixel_x,
        pixel_y
    ):
        ghost_background = background.copy()
        ghost_background.set_alpha(100)

        ghost_surface = surface.copy()
        ghost_surface.set_alpha(128)

        self.screen.blit(ghost_background, (pixel_x, pixel_y))
        self.screen.blit(ghost_surface, (pixel_x, pixel_y))

    def _draw_conveyor_items(self, conveyor, grid_x, grid_y):
        current_size = self.camera.actual_tile_size
        item_size = max(2, current_size // 2)

        start_x, start_y = self.camera.world_to_screen(grid_x, grid_y)
        center_x = start_x + current_size / 2
        center_y = start_y + current_size / 2

        direction_offsets = {
            "N": (0, -current_size / 2),
            "S": (0, current_size / 2),
            "E": (current_size / 2, 0),
            "W": (-current_size / 2, 0)
        }

        input_offset = direction_offsets.get(
            conveyor.input_dir,
            (0, 0)
        )
        output_offset = direction_offsets.get(
            conveyor.output_dir,
            (0, 0)
        )

        entry_x = center_x + input_offset[0]
        entry_y = center_y + input_offset[1]

        exit_x = center_x + output_offset[0]
        exit_y = center_y + output_offset[1]

        for item in conveyor.items:
            item_x, item_y = self._calculate_item_position(
                item.progress,
                entry_x,
                entry_y,
                center_x,
                center_y,
                exit_x,
                exit_y
            )

            item_surface = self.asset_manager.get_item_asset(
                item.item_name
            )

            if (
                item_surface.get_width() != item_size
                or item_surface.get_height() != item_size
            ):
                cache_key = (
                    f"item_{item.item_name}",
                    item_size,
                    item_size
                )

                if cache_key not in self.scaled_cache:
                    self.scaled_cache[cache_key] = (
                        pygame.transform.scale(
                            item_surface,
                            (item_size, item_size)
                        )
                    )

                item_surface = self.scaled_cache[cache_key]

            self.screen.blit(
                item_surface,
                (
                    item_x - item_size / 2,
                    item_y - item_size / 2
                )
            )

    @staticmethod
    def _calculate_item_position(
        progress,
        entry_x,
        entry_y,
        center_x,
        center_y,
        exit_x,
        exit_y
    ):
        if progress < 0.5:
            interpolation = progress * 2.0

            return (
                entry_x + (center_x - entry_x) * interpolation,
                entry_y + (center_y - entry_y) * interpolation
            )

        interpolation = (progress - 0.5) * 2.0

        return (
            center_x + (exit_x - center_x) * interpolation,
            center_y + (exit_y - center_y) * interpolation
        )

