import pygame
import src.entities
from src.utils import format_number
from src.registry import ore_registry, machine_registry, theme_registry
from src.UI.windows import MachineWindow, StorageWindow, RouterConfigWindow, RecipeUnlockWindow, VictoryWindow, StatisticsWindow

OPPOSITE_DIRS = {'N': 'S', 'E': 'W', 'S': 'N', 'W': 'E'}

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


class InputHandler:
    """
    Handles player input, including keyboard shortcuts for tool selection
    and mouse interactions for building, destroying, panning, and zooming.
    """
    def __init__(self, game_manager, camera, tile_size=16):
        """
        Initialize the input handler with references to core game systems.

        Args:
            game_manager: The main game manager containing game state and map data.
            camera (Camera): The camera used for coordinate transformations and viewport control.
            tile_size (int, optional): Base tile size in pixels. Defaults to 16.
        """
        self.game_manager = game_manager
        self.camera = camera
        self.tile_size = tile_size
        machine_tools = [name for name, cls in src.entities.BLOCK_REGISTRY.items() if cls is src.entities.Machine]

        self.tool_groups = [
            ['miner'],
            machine_tools,
            ['conveyor'],
            ['merger'],
            ['splitter', 'filter']
        ]

        self.group_indices = [0] * len(self.tool_groups)
        self.selected_slot = 0
        
        # Building stat
        self.current_direction = 'E'     
        self.directions = ['N', 'E', 'S', 'W'] 
        
        # Mouse & camera state
        self.hovered_grid = (0, 0) 
        self.is_panning = False
        self.last_mouse_pos = (0, 0)

        self.is_building = False
        self.is_destroying = False
        self.last_interacted_grid = None
        self.custom_in_dir = None
        self.interaction_mode = 'PAN'

        self.windows = {
            'machine': MachineWindow(camera.width, camera.height, game_manager),
            'storage': StorageWindow(camera.width, camera.height),
            'router': RouterConfigWindow(camera.width, camera.height),
            'recipe_unlock': RecipeUnlockWindow(camera.width, camera.height, game_manager.economy),
            'victory':VictoryWindow(camera.width, camera.height),
            'statistics': StatisticsWindow(camera.width, camera.height, game_manager)
        }
        self.active_window = None

    @property
    def selected_tool(self):
        return self.tool_groups[self.selected_slot][self.group_indices[self.selected_slot]]
    
    def handle_window_event(self, event):
        "Pass pygame event to the active window to process"
        if self.active_window and self.active_window.is_open:
            self.active_window.handle_event(event)
            if not self.active_window.is_open:
                self.active_window = None
            return True
        return False

    def handle_keydown(self, key):
        """
        Handle keyboard input for selecting tools and rotating direction.

        Args:
            key (int): The key code from the input event (e.g., pygame key constant).
        """

        # --- DEBUG CODE---
        # if key == pygame.K_F9:
        #     self.game_manager.inventory.total_stored['robot'] = 9999
            
        #     self.game_manager.inventory.item_rates['robot'] = 150.0
        #     return
        # -----------------------------------------------------------------

        if self.active_window and self.active_window.is_open:
            return
        
        if pygame.K_1 <= key <= pygame.K_9:
            idx = key - pygame.K_1
            if idx < len(self.tool_groups):
                if self.selected_slot == idx:
                    self.group_indices[idx] = (self.group_indices[idx] + 1) % len(self.tool_groups[idx])
                else:
                    self.selected_slot = idx
        elif key == pygame.K_r:
            current_idx = self.directions.index(self.current_direction)
            self.current_direction = self.directions[(current_idx + 1) % 4]
        elif key == pygame.K_q:
            self.interaction_mode = 'PAN' if self.interaction_mode == 'BUILD' else 'BUILD'
        elif key == pygame.K_b:
            self.active_window = self.windows['recipe_unlock']
            self.active_window.open(self.game_manager.inventory)
        elif key == pygame.K_t:
            self.active_window = self.windows['statistics']
            self.active_window.open()

    def handle_zoom(self, y_scroll, mouse_x, mouse_y):
        """
        Adjust camera zoom level while keeping the mouse position fixed in world space.

        Args:
            y_scroll (int): Scroll direction and magnitude (positive for zoom in, negative for zoom out).
            mouse_x (float): Current mouse X position on screen.
            mouse_y (float): Current mouse Y position on screen.
        """
        zoom_factor = 1.15
        old_zoom = self.camera.zoom
        
        if y_scroll > 0:
            new_zoom = min(6.0, self.camera.zoom * zoom_factor)
        elif y_scroll < 0:
            new_zoom = max(1.0, self.camera.zoom / zoom_factor)
        else:
            return

        if new_zoom != old_zoom:
            world_x = (mouse_x - self.camera.offset_x) / old_zoom
            world_y = (mouse_y - self.camera.offset_y) / old_zoom
            self.camera.zoom = new_zoom
            self.camera.offset_x = mouse_x - (world_x * new_zoom)
            self.camera.offset_y = mouse_y - (world_y * new_zoom)

    def handle_mouse_down(self, x, y, button):
        """
        Handle mouse button press events for panning or building actions.

        Args:
            x (float): Mouse X position on screen.
            y (float): Mouse Y position on screen.
            button (int): Mouse button identifier (e.g., 1 = left, 2 = middle, 3 = right).
        """
        if self.active_window and self.active_window.is_open:
            return

        if button == 1: 
            grid_x, grid_y = self.camera.screen_to_world(x, y)
            entity = self.game_manager.game_map.get_block_at(grid_x, grid_y)

            if self.interaction_mode == 'PAN':
                if entity:
                    class_name = type(entity).__name__
                    if class_name in ('Machine', 'Miner'):
                        self.active_window = self.windows['machine']
                        self.active_window.open(entity)
                        return
                    elif class_name == 'CentralStorage':
                        self.active_window = self.windows['storage']
                        self.active_window.open(entity)
                        return
                    elif class_name == 'Router':
                        self.active_window = self.windows['router']
                        self.active_window.open(entity)
                        return
                else:    
                    self.is_panning = True
                    self.last_mouse_pos = (x, y)

            elif self.interaction_mode == 'BUILD':
                self.is_building = True
                self.custom_in_dir = None
                self.last_interacted_grid = (grid_x, grid_y)
                self._handle_build_destroy(grid_x, grid_y, 1)
                
        elif button == 3 and self.interaction_mode == 'BUILD': 
            self.is_destroying = True
            grid_x, grid_y = self.camera.screen_to_world(x, y)
            self.last_interacted_grid = (grid_x, grid_y)
            self._handle_build_destroy(grid_x, grid_y, 3)

    def handle_mouse_up(self, button):
        """
        Handle mouse button release events.

        Args:
            button (int): Mouse button identifier.
        """
        if button == 1:
            self.is_panning = False
            self.is_building = False
            self.last_interacted_grid = None
            self.custom_in_dir = None
        elif button == 3:
            self.is_destroying = False
            self.last_interacted_grid = None

    def handle_mouse_motion(self, x, y):
        """
        Handle mouse movement for panning and hover tracking.

        Args:
            x (float): Current mouse X position.
            y (float): Current mouse Y position.
        """
        if self.is_panning:
            dx = x - self.last_mouse_pos[0]
            dy = y - self.last_mouse_pos[1]
            self.camera.offset_x += dx
            self.camera.offset_y += dy
            self.last_mouse_pos = (x, y)

        grid_x, grid_y = self.camera.screen_to_world(x, y)
        self.hovered_grid = (grid_x, grid_y)

        if (self.is_building or self.is_destroying) and self.hovered_grid != self.last_interacted_grid:
            
            if self.is_building and self.selected_tool == 'conveyor' and self.last_interacted_grid:
                while self.last_interacted_grid != self.hovered_grid:
                    prev_x, prev_y = self.last_interacted_grid
                    target_x, target_y = self.hovered_grid
                    
                    dx = target_x - prev_x
                    dy = target_y - prev_y
                    
                    if dx == 0 and dy == 0:
                        break
                        
                    step_x, step_y = prev_x, prev_y
                    if abs(dx) > abs(dy):
                        step_x += 1 if dx > 0 else -1
                    else:
                        step_y += 1 if dy > 0 else -1
                        
                    drag_dx = step_x - prev_x
                    drag_dy = step_y - prev_y
                    drag_dir = 'E' if drag_dx > 0 else ('W' if drag_dx < 0 else ('S' if drag_dy > 0 else 'N'))
                    
                    prev_block = self.game_manager.game_map.get_block_at(prev_x, prev_y)
                    if prev_block and type(prev_block).__name__ == 'Conveyor':
                        prev_block.output_dir = drag_dir
                        if getattr(prev_block, 'input_dir', None) == drag_dir:
                            prev_block.input_dir = OPPOSITE_DIRS[drag_dir]
                        if hasattr(prev_block, 'connection'):
                            prev_block.connection.update_outbound(self.game_manager.game_map)

                    if self.game_manager.game_map.get_block_at(step_x, step_y) is not None:
                        break

                    drag_in_dir = OPPOSITE_DIRS[drag_dir]

                    self._handle_build_destroy(step_x, step_y, 1, override_in_dir=drag_in_dir, override_out_dir=drag_dir)
                    
                    self.last_interacted_grid = (step_x, step_y)
                
                return
            
            button_action = 1 if self.is_building else 3
            self._handle_build_destroy(grid_x, grid_y, button_action)
            self.last_interacted_grid = self.hovered_grid

    def _handle_build_destroy(self, grid_x, grid_y, button, override_in_dir=None, override_out_dir=None):
        """
        Handle building or destroying entities at a given grid position.

        Args:
            grid_x (int): Grid X coordinate.
            grid_y (int): Grid Y coordinate.
            button (int): Mouse button identifier (1 = build, 3 = destroy).
        """
        if button == 1:
            if self.game_manager.game_map.get_block_at(grid_x, grid_y) is None:
                new_block = self._create_entity(grid_x, grid_y, override_in_dir, override_out_dir)
                if new_block:
                    self.game_manager.game_map.place_block(new_block)
        elif button == 3:
            self.game_manager.game_map.remove_block(grid_x, grid_y)

    def _create_entity(self, x, y, override_in_dir=None, override_out_dir=None):
        """
        Create a new game entity based on the currently selected tool.

        Args:
            x (int): Grid X coordinate.
            y (int): Grid Y coordinate.

        Returns:
            object or None: The created entity instance, or None if no valid tool is selected.
        """
        out_dir = override_out_dir if override_out_dir else self.current_direction
        
        if override_in_dir:
            final_in_dir = override_in_dir
        elif self.custom_in_dir:
            final_in_dir = self.custom_in_dir
        else:
            final_in_dir = OPPOSITE_DIRS[out_dir]

        if final_in_dir == out_dir:
            final_in_dir = OPPOSITE_DIRS[out_dir]

        context = {
            'game_map': self.game_manager.game_map,
            'economy': self.game_manager.economy,
            'inventory': self.game_manager.inventory,
            'in_dir': final_in_dir,
            'out_dir': out_dir,
            'tool': self.selected_tool
        }
        
        return src.entities.spawn_entity(self.selected_tool, x, y, context)

    def update(self):
        """
        Auto-pan camera when dragging at the edges of the screen.
        """
        if self.is_building:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            edge_margin = 40 
            pan_speed = 15.0
            
            dx = 0
            dy = 0
            
            if mouse_x <= edge_margin: 
                dx = pan_speed
            elif mouse_x >= self.camera.width - edge_margin: 
                dx = -pan_speed
                
            if mouse_y <= edge_margin: 
                dy = pan_speed
            elif mouse_y >= self.camera.height - edge_margin: 
                dy = -pan_speed
                
            if dx != 0 or dy != 0:
                self.camera.offset_x += dx
                self.camera.offset_y += dy
                
                self.handle_mouse_motion(mouse_x, mouse_y)


class UIRenderer:
    """
    Responsible for rendering all visual elements, including the grid,
    entities, HUD, and moving items.
    """
    def __init__(self, screen, game_manager, asset_manager, input_handler, camera, tile_size=16):
        """
        Initialize the UI renderer with required systems and rendering context.

        Args:
            screen: The main display surface used for rendering.
            game_manager: The central game manager containing game state and map data.
            asset_manager: Manager responsible for loading and caching assets.
            input_handler (InputHandler): Handles user input and provides interaction state.
            camera (Camera): Camera used for coordinate transformations and viewport control.
            tile_size (int, optional): Base tile size in pixels. Defaults to 16.
        """
        self.screen = screen
        self.game_manager = game_manager
        self.asset_manager = asset_manager
        self.input_handler = input_handler 
        self.tile_size = tile_size
        self.camera = camera
        self.bg_color = theme_registry.get_color("render", "bg")
        self.font = pygame.font.SysFont("Arial", 22, bold=True)
        self.font_title = pygame.font.SysFont("Arial", 26, bold=True)
        self.chunk_surfaces = {}
        self.direction_text = {'N': '↑', 'S': '↓', 'E': '→', 'W': '←'}
        self.scaled_cache = {}
        self.last_zoom = self.camera.zoom
        self.machine_tools = [name for name, cls in src.entities.BLOCK_REGISTRY.items() if hasattr(cls, 'upgrade')]

    def _get_chunk_surface(self, cx, cy):
        if (cx, cy) in self.chunk_surfaces:
            return self.chunk_surfaces[(cx, cy)]
            
        chunk_size = self.game_manager.game_map.chunk_size
        base_size = self.camera.base_tile_size
        
        surface = pygame.Surface((chunk_size * base_size, chunk_size * base_size), pygame.SRCALPHA)
        
        for local_x in range(chunk_size):
            for local_y in range(chunk_size):
                world_x = cx * chunk_size + local_x
                world_y = cy * chunk_size + local_y
                
                ore_name = self.game_manager.game_map.get_ore_at(world_x, world_y)
                if ore_name:
                    color = ore_registry.get_color(ore_name)
                    rect = pygame.Rect(local_x * base_size, local_y * base_size, base_size, base_size)
                    pygame.draw.rect(surface, color, rect)
                    
        if len(self.chunk_surfaces) > 256:
            self.chunk_surfaces.pop(next(iter(self.chunk_surfaces)))
            
        self.chunk_surfaces[(cx, cy)] = surface
        return surface
        
    def render_frame(self, fps=0):
        """
        Render a complete frame, including background, grid, entities, ghost previews, and HUD.

        This is the main rendering pipeline executed each frame.
        """
        if self.camera.zoom != self.last_zoom:
            self.scaled_cache.clear()
            self.last_zoom = self.camera.zoom

        self.screen.fill(self.bg_color)
        self._draw_ores()
        self._draw_grid_lines()

        min_x, max_x, min_y, max_y = self.camera.get_visible_bounds()
        rendered_entities = set()

        for grid_x in range(min_x, max_x + 1):
            for grid_y in range(min_y, max_y + 1):
                entity = self.game_manager.game_map.get_block_at(grid_x, grid_y)
                if entity and entity not in rendered_entities:
                    self._draw_entity(entity, entity.position.x, entity.position.y)
                    rendered_entities.add(entity)

        rendered_entities.clear()
        for grid_x in range(min_x, max_x + 1):
            for grid_y in range(min_y, max_y + 1):
                entity = self.game_manager.game_map.get_block_at(grid_x, grid_y)
                if entity and entity not in rendered_entities:
                    if hasattr(entity, 'items'):
                        self._draw_conveyor_items(entity, entity.position.x, entity.position.y)
                    rendered_entities.add(entity)

        self._draw_ghost_block()
        self._draw_hud(fps)
        self._draw_hover_info()
        self._draw_origin_indicator()

        if self.input_handler.active_window and self.input_handler.active_window.is_open:
            self.input_handler.active_window.draw(self.screen, self.asset_manager)
            
        pygame.display.flip()

    def _draw_grid_lines(self):
        """
        Draw grid lines for the visible area based on camera bounds.

        This helps visualize tile alignment and placement.
        """
        min_x, max_x, min_y, max_y = self.camera.get_visible_bounds()
        grid_color = theme_registry.get_color("render", "grid")

        for grid_x in range(min_x, max_x + 1):
            start_x, _ = self.camera.world_to_screen(grid_x, 0)
            pygame.draw.line(self.screen, grid_color, (start_x, 0), (start_x, self.camera.height))

        for grid_y in range(min_y, max_y + 1):
            _, start_y = self.camera.world_to_screen(0, grid_y)
            pygame.draw.line(self.screen, grid_color, (0, start_y), (self.camera.width, start_y))

    def _draw_entity(self, entity, grid_x, grid_y, is_ghost=False):
        """
        Render a single entity at a given grid position.

        Args:
            entity: The game entity to render.
            grid_x (int): Grid X coordinate.
            grid_y (int): Grid Y coordinate.
            is_ghost (bool, optional): Whether to render as a semi-transparent preview. Defaults to False.
        """
        pixel_x, pixel_y = self.camera.world_to_screen(grid_x, grid_y)

        if hasattr(entity, 'get_asset_name'):
            machine_name = entity.get_asset_name()
        else:
            machine_name = type(entity).__name__.lower()

        angle = 0
        class_name = type(entity).__name__

        if class_name not in ('Conveyor', 'CentralStorage', 'Seller'):
            direction = getattr(entity, 'output_dir', OPPOSITE_DIRS[getattr(entity, 'input_dir', 'N')])
            
            dir_to_angle = {'S': 0, 'E': 90, 'N': 180, 'W': -90}
            angle = dir_to_angle.get(direction, 0)

        filepath = f"assets/{machine_name}.png"
        surface = self.asset_manager.get_asset(machine_name, filepath, angle)

        width_tiles = getattr(entity, 'width', 1)
        height_tiles = getattr(entity, 'height', 1)
        current_size = self.camera.actual_tile_size

        target_w = current_size * width_tiles
        target_h = current_size * height_tiles

        if surface.get_width() != target_w or surface.get_height() != target_h:
            cache_key = (f"ent_{machine_name}_{angle}", target_w, target_h)
            
            if cache_key not in self.scaled_cache:
                self.scaled_cache[cache_key] = pygame.transform.scale(surface, (target_w, target_h))
            
            surface = self.scaled_cache[cache_key]

        # if hasattr(entity, 'level'):
        level = getattr(entity, 'level', 1)

        bg_color = theme_registry.get_level_color(level)
        machine_border = theme_registry.get_color("render", "machine_border")
        
        bg_rect = pygame.Rect(pixel_x, pixel_y, target_w, target_h)
        
        if is_ghost:
            s = pygame.Surface((target_w, target_h), pygame.SRCALPHA)
            s.fill((*bg_color, 100))
            self.screen.blit(s, (pixel_x, pixel_y))
        else:
            pygame.draw.rect(self.screen, bg_color, bg_rect)
            pygame.draw.rect(self.screen, machine_border, bg_rect, 2)

        if is_ghost:
            ghost_surface = surface.copy()
            ghost_surface.set_alpha(128)
            self.screen.blit(ghost_surface, (pixel_x, pixel_y))
        else:
            self.screen.blit(surface, (pixel_x, pixel_y))

    def _draw_ores(self):
        min_grid_x, max_grid_x, min_grid_y, max_grid_y = self.camera.get_visible_bounds()
        chunk_size = self.game_manager.game_map.chunk_size
        
        min_cx = min_grid_x // chunk_size
        max_cx = max_grid_x // chunk_size
        min_cy = min_grid_y // chunk_size
        max_cy = max_grid_y // chunk_size
        
        for cx in range(min_cx, max_cx + 1):
            for cy in range(min_cy, max_cy + 1):
                base_surface = self._get_chunk_surface(cx, cy)
                
                screen_x, screen_y = self.camera.world_to_screen(cx * chunk_size, cy * chunk_size)
                
                next_x, next_y = self.camera.world_to_screen((cx + 1) * chunk_size, (cy + 1) * chunk_size)
                
                target_width = next_x - screen_x
                target_height = next_y - screen_y
                
                if target_width > 0 and target_height > 0:
                    if self.camera.zoom != 1.0:
                        cache_key = (id(base_surface), target_width, target_height)
                        
                        if cache_key not in self.scaled_cache:
                            self.scaled_cache[cache_key] = pygame.transform.scale(base_surface, (target_width, target_height))
                        
                        scaled_surface = self.scaled_cache[cache_key]
                    else:
                        scaled_surface = base_surface
                        
                    self.screen.blit(scaled_surface, (screen_x, screen_y))

    def _draw_conveyor_items(self, conveyor, grid_x, grid_y):
        """
        Render items moving smoothly along a conveyor using two-phase linear interpolation.

        The movement is split into:
        - Phase 1: From input edge to tile center
        - Phase 2: From tile center to output edge

        Args:
            conveyor (Conveyor): The conveyor entity containing moving items.
            grid_x (int): Grid X coordinate of the conveyor.
            grid_y (int): Grid Y coordinate of the conveyor.
        """
        current_size = self.camera.actual_tile_size
        item_size = max(2, current_size // 2)

        start_x, start_y = self.camera.world_to_screen(grid_x, grid_y)
        center_x = start_x + current_size / 2
        center_y = start_y + current_size / 2

        # Direction offsets relative to tile center
        dir_offsets = {
            "N": (0, -current_size / 2),
            "S": (0, current_size / 2),
            "E": (current_size / 2, 0),
            "W": (-current_size / 2, 0)
        }

        in_offset = dir_offsets.get(conveyor.input_dir, (0, 0))
        out_offset = dir_offsets.get(conveyor.output_dir, (0, 0))

        entry_x, entry_y = center_x + in_offset[0], center_y + in_offset[1]
        exit_x, exit_y = center_x + out_offset[0], center_y + out_offset[1]

        for item in conveyor.items:
            if item.progress < 0.5:
                t = item.progress * 2.0
                item_x = entry_x + (center_x - entry_x) * t
                item_y = entry_y + (center_y - entry_y) * t
            else:
                t = (item.progress - 0.5) * 2.0
                item_x = center_x + (exit_x - center_x) * t
                item_y = center_y + (exit_y - center_y) * t

            filepath = f"assets/{item.item_name}.png"
            item_surface = self.asset_manager.get_asset(item.item_name, filepath)

            if item_surface.get_width() != item_size:
                cache_key = (f"item_{item.item_name}", item_size, item_size)
                
                if cache_key not in self.scaled_cache:
                    self.scaled_cache[cache_key] = pygame.transform.scale(item_surface, (item_size, item_size))
                
                item_surface = self.scaled_cache[cache_key]

            render_x = item_x - item_size / 2
            render_y = item_y - item_size / 2
            self.screen.blit(item_surface, (render_x, render_y))

    def _draw_ghost_block(self):
        """
        Render a ghost (preview) entity at the hovered grid position.

        This provides visual feedback for placement before committing.
        """
        grid_x, grid_y = self.input_handler.hovered_grid
        mode = self.input_handler.interaction_mode
        
        if mode == 'BUILD':
            if self.game_manager.game_map.get_block_at(grid_x, grid_y) is None:
                temp_block = self.input_handler._create_entity(grid_x, grid_y)
                if temp_block:
                    self._draw_entity(temp_block, grid_x, grid_y, is_ghost=True)
                    
        elif mode == 'PAN':
            pixel_x, pixel_y = self.camera.world_to_screen(grid_x, grid_y)
            current_size = self.camera.actual_tile_size
            
            highlight = pygame.Surface((current_size, current_size), pygame.SRCALPHA)
            highlight.fill((255, 255, 255, 30)) 
            pygame.draw.rect(highlight, (255, 255, 255, 100), (0, 0, current_size, current_size), 1)
            
            self.screen.blit(highlight, (pixel_x, pixel_y))

    def _draw_hud(self, fps=0):
        hud_bg = theme_registry.get_color("render", "hud_bg")
        hud_border = theme_registry.get_color("render", "hud_border")
        hud_text_color = theme_registry.get_color("render", "hud_text")
        screen_w, screen_h = self.screen.get_size()

        # --- PANEL 1: SYSTEM INFO (TOP LEFT) ---
        mode = self.input_handler.interaction_mode
        sys_text = f"MODE: {mode.upper()}(Q)  |  FPS: {int(fps)}"
        sys_surf = self.font.render(sys_text, True, hud_text_color)
        sys_rect = pygame.Rect(15, 15, sys_surf.get_width() + 24, 36)
        
        pygame.draw.rect(self.screen, hud_bg, sys_rect, border_radius=6)
        pygame.draw.rect(self.screen, hud_border, sys_rect, 1, border_radius=6)
        self.screen.blit(sys_surf, (sys_rect.x + 12, sys_rect.y + (sys_rect.height - sys_surf.get_height()) // 2))

        # --- PANEL 2: ECONOMY (TOP RIGHT) ---
        money = self.game_manager.economy.money if self.game_manager.economy else 0
        from src.utils import format_number
        cash_text = f"CASH: ${format_number(money)}"
        
        cash_color = theme_registry.get_color("render", "cash_color")
        cash_surf = self.font_title.render(cash_text, True, cash_color)
        
        cash_rect = pygame.Rect(screen_w - cash_surf.get_width() - 35, 15, cash_surf.get_width() + 24, 36)
        pygame.draw.rect(self.screen, hud_bg, cash_rect, border_radius=6)
        pygame.draw.rect(self.screen, hud_border, cash_rect, 1, border_radius=6)
        self.screen.blit(cash_surf, (cash_rect.x + 12, cash_rect.y + (cash_rect.height - cash_surf.get_height()) // 2))

        # --- PANEL 3: TOOLBAR (BOTTOM CENTER) ---
        tool = self.input_handler.selected_tool.lower()
        direction = getattr(self.input_handler, 'current_direction', 'N')
        total_groups = len(getattr(self.input_handler, 'tool_groups', []))
        
        slot_size = 72
        padding = 10
        
        tb_rect = pygame.Rect((screen_w - slot_size - padding * 2) // 2, 
                              screen_h - slot_size - padding * 2 - 25, 
                              slot_size + padding * 2, 
                              slot_size + padding * 2)

        pygame.draw.rect(self.screen, hud_bg, tb_rect, border_radius=8)
        pygame.draw.rect(self.screen, theme_registry.get_color("windows", "button_active"), tb_rect, 2, border_radius=8)
        
        if tool and hasattr(self, 'asset_manager'):
            try:
                if tool in self.machine_tools:
                    base_color = theme_registry.get_color("levels", "1")
                    border_color = theme_registry.get_color("windows", "border")
                    
                    base_rect = pygame.Rect(tb_rect.x + padding, tb_rect.y + padding, slot_size, slot_size)
                    pygame.draw.rect(self.screen, base_color, base_rect)
                    pygame.draw.rect(self.screen, border_color, base_rect, 1)

                filepath = f"assets/{tool}.png"
                surf = self.asset_manager.get_asset(tool, filepath)
                if surf.get_width() != slot_size:
                    surf = pygame.transform.scale(surf, (slot_size, slot_size))
                self.screen.blit(surf, (tb_rect.x + padding, tb_rect.y + padding))
            except Exception:
                txt_surf = self.font.render(tool[:4].upper(), True, hud_text_color)
                self.screen.blit(txt_surf, (tb_rect.centerx - txt_surf.get_width() // 2, tb_rect.centery - txt_surf.get_height() // 2))

        header_text = f"GROUP [1-{total_groups}]   |   {tool.upper()}"
        header_surf = self.font.render(header_text, True, hud_text_color)
        header_rect = pygame.Rect(tb_rect.centerx - header_surf.get_width() // 2 - 12, 
                                  tb_rect.y - 38, 
                                  header_surf.get_width() + 24, 
                                  30)
                                  
        pygame.draw.rect(self.screen, hud_bg, header_rect, border_radius=4)
        self.screen.blit(header_surf, (header_rect.x + 12, header_rect.y + (header_rect.height - header_surf.get_height()) // 2))

    def _draw_hover_info(self):
        """
        Render a dynamic tooltip panel at the bottom right of the screen
        showing information about the currently hovered tile.
        """
        hud_bg = theme_registry.get_color("render", "hud_bg")
        hud_border = theme_registry.get_color("render", "hud_border")
        hud_text = theme_registry.get_color("render", "hud_text")

        grid_x, grid_y = self.input_handler.hovered_grid
        entity = self.game_manager.game_map.get_block_at(grid_x, grid_y)
        info_lines = [f"({grid_x}, {grid_y})"]
        if entity:
            class_name = type(entity).__name__
            info_lines.append(f"BLOCK: {class_name.upper()}")
            
            if hasattr(entity, 'level'):
                info_lines.append(f"LEVEL: {entity.level}")
                
            if hasattr(entity, 'ore'):
                info_lines.append(f"MINING: {entity.ore.upper()}")
                
            elif hasattr(entity, 'machine_type'):
                info_lines.append(f"TYPE: {entity.machine_type.upper()}")
                recipe_mgr = getattr(entity, 'recipe_manager', None)
                if recipe_mgr and recipe_mgr.selected_recipe:
                    info_lines.append(f"RECIPE: {recipe_mgr.selected_recipe.upper()}")
            
            if hasattr(entity, 'output_dir'):
                info_lines.append(f"OUTPUT DIRECTION: {entity.output_dir}")
                
        else:
            ore_name = self.game_manager.game_map.get_ore_at(grid_x, grid_y)
            if ore_name:
                info_lines.append(f"GROUND: {ore_name.upper()} ORE")
            else:
                info_lines.append("GROUND: EMPTY")

        rendered_lines = [self.font.render(line, True, hud_text) for line in info_lines]
        
        padding = 12
        line_height = self.font.get_linesize() + 4
        
        max_width = max(surf.get_width() for surf in rendered_lines)
        box_width = max_width + padding * 2
        box_height = padding * 2 + len(info_lines) * line_height - 4
        
        box_x = self.camera.width - box_width - 20
        box_y = self.camera.height - box_height - 20
        
        hud_rect = pygame.Rect(box_x, box_y, box_width, box_height)
        pygame.draw.rect(self.screen, hud_bg, hud_rect)
        pygame.draw.rect(self.screen, hud_border, hud_rect, 1)
        
        for i, surf in enumerate(rendered_lines):
            self.screen.blit(surf, (box_x + padding, box_y + padding + i * line_height))

    def _draw_origin_indicator(self):
        """
        Draws a low-opacity arrow pointing toward (0, 0) when it is off-screen.
        """
        origin_screen_x, origin_screen_y = self.camera.world_to_screen(0, 0)

        on_screen = (
            0 <= origin_screen_x <= self.camera.width and
            0 <= origin_screen_y <= self.camera.height
        )

        if on_screen:
            return

        cx = self.camera.width / 2
        cy = self.camera.height / 2

        dx = origin_screen_x - cx
        dy = origin_screen_y - cy
        length = (dx ** 2 + dy ** 2) ** 0.5
        if length == 0:
            return
        dx /= length
        dy /= length

        padding = 30
        if abs(dx) > 1e-6:
            t_x = ((self.camera.width - padding) if dx > 0 else padding) - cx
            t_x /= dx
        else:
            t_x = float('inf')

        if abs(dy) > 1e-6:
            t_y = ((self.camera.height - padding) if dy > 0 else padding) - cy
            t_y /= dy
        else:
            t_y = float('inf')

        t = min(t_x, t_y)
        arrow_x = cx + dx * t
        arrow_y = cy + dy * t

        arrow_len = 28
        arrow_half_width = 12

        tip_x = arrow_x + dx * arrow_len / 2
        tip_y = arrow_y + dy * arrow_len / 2
        base_x = arrow_x - dx * arrow_len / 2
        base_y = arrow_y - dy * arrow_len / 2

        px, py = -dy, dx

        points = [
            (tip_x, tip_y),
            (base_x + px * arrow_half_width, base_y + py * arrow_half_width),
            (base_x - px * arrow_half_width, base_y - py * arrow_half_width),
        ]

        arrow_color = theme_registry.get_color("render", "indicator_arrow")
        arrow_surface = pygame.Surface((self.camera.width, self.camera.height), pygame.SRCALPHA)
        pygame.draw.polygon(arrow_surface, arrow_color, points)
        self.screen.blit(arrow_surface, (0, 0))