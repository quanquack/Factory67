import pygame

from src.utils import format_number
from src.registry import machine_registry, theme_registry


class HUDRenderer:
    """Renders HUD panels, hover information and world indicators."""
    def __init__(
        self,
        screen,
        game_manager,
        asset_manager,
        input_handler,
        camera
    ):
        self.screen = screen
        self.game_manager = game_manager
        self.asset_manager = asset_manager
        self.input_handler = input_handler
        self.camera = camera

        self.font = pygame.font.SysFont(
            "Arial",
            22,
            bold=True
        )
        self.font_title = pygame.font.SysFont(
            "Arial",
            26,
            bold=True
        )

        self.upgradeable_tools = {
            name
            for name, data in machine_registry.machine_data.items()
            if data["metadata"].get("upgradable")
        }

    def draw(self, fps=0):
        self._draw_hud(fps)
        self._draw_hover_info()
        self._draw_origin_indicator()

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
                if tool in self.upgradeable_tools:
                    border_color = theme_registry.get_color("windows", "border")
                    bg_surface = self.asset_manager.get_tier_background(1, slot_size, slot_size)
                    base_rect = pygame.Rect(tb_rect.x + padding, tb_rect.y + padding, slot_size, slot_size)
                    self.screen.blit(bg_surface, (base_rect.x, base_rect.y))
                    pygame.draw.rect(self.screen, border_color, base_rect, 1)

                # filepath = f"assets/{tool}.png"
                surf = self.asset_manager.get_machine_asset(tool)
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
        surf_size = 60
        arrow_surface = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)

        local_points = [
            (px - arrow_x + surf_size / 2, py - arrow_y + surf_size/2)
            for px, py in points
        ]

        pygame.draw.polygon(arrow_surface, arrow_color, local_points)
        self.screen.blit(arrow_surface, (arrow_x - surf_size/2, arrow_y - surf_size/2))
