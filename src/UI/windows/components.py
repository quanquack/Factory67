import pygame

from src.registry import item_registry, theme_registry


class ItemSlot:
    """A standalone UI component representing an inventory or display slot."""
    def __init__(self, x, y, size=64):
        self.rect = pygame.Rect(x, y, size, size)
        self.item_name = None
        self.amount_text = None
        self.amount_color = None
        self.is_hovered = False
        self.is_active = False

    def set_data(self, item_name, amount_text=None, amount_color=None):
        self.item_name = item_name
        self.amount_text = amount_text
        self.amount_color = amount_color

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        return self.is_hovered

    def draw(self, screen, asset_manager, font, font_small):
        bg_color = theme_registry.get_color("windows", "button_active") if self.is_active else (
                   theme_registry.get_color("windows", "button_hover") if self.is_hovered else 
                   theme_registry.get_color("windows", "button"))
                   
        pygame.draw.rect(screen, bg_color, self.rect, border_radius=4)
        pygame.draw.rect(screen, theme_registry.get_color("windows", "border"), self.rect, 1, border_radius=4)
        
        if not self.item_name:
            return None
            
        display_name = item_registry.get_display_name(self.item_name)
        
        if asset_manager:
            # filepath = f"assets/{self.item_name}.png"
            try:
                surf = asset_manager.get_item_asset(self.item_name)
                icon_size = self.rect.width - 16
                if surf.get_width() != icon_size:
                    surf = pygame.transform.scale(surf, (icon_size, icon_size))
                screen.blit(surf, (self.rect.x + 8, self.rect.y + 8))
            except Exception:
                name_surf = font_small.render(display_name[:4].upper(), True, theme_registry.get_color("windows", "text_dim"))
                screen.blit(name_surf, (self.rect.x + (self.rect.width - name_surf.get_width()) // 2, self.rect.y + 8))
        
        if self.amount_text is not None:
            color = self.amount_color if self.amount_color else theme_registry.get_color("windows", "text")
            amt_surf = font.render(str(self.amount_text), True, color)
            screen.blit(amt_surf, (self.rect.x + self.rect.width - amt_surf.get_width() - 4, 
                                   self.rect.bottom - amt_surf.get_height() - 2))
            
        if self.is_hovered:
            return display_name
        return None


class Scrollbar:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.thumb_rect = pygame.Rect(x, y, width, 20)
        self.is_dragging = False
        self.drag_offset_y = 0

    def update_rect(self, x, y, width, height):
        self.rect.update(x, y, width, height)

    def handle_event(self, event, current_scroll, max_scroll):
        if max_scroll <= 0:
            return current_scroll
            
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.thumb_rect.collidepoint(event.pos):
                self.is_dragging = True
                self.drag_offset_y = event.pos[1] - self.thumb_rect.y
                
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.is_dragging = False
            
        elif event.type == pygame.MOUSEMOTION and self.is_dragging:
            track_height = self.rect.height - self.thumb_rect.height
            if track_height > 0:
                mouse_y = min(max(event.pos[1] - self.drag_offset_y, self.rect.y), self.rect.bottom - self.thumb_rect.height)
                ratio = (mouse_y - self.rect.y) / track_height
                return int(round(ratio * max_scroll))
                
        return current_scroll

    def draw(self, screen, current_scroll, max_scroll, visible_ratio):
        if max_scroll <= 0:
            return

        pygame.draw.rect(screen, theme_registry.get_color("windows", "bg"), self.rect, border_radius=4)
        
        thumb_height = max(30, int(self.rect.height * visible_ratio))
        track_height = self.rect.height - thumb_height
        thumb_y = self.rect.y + (current_scroll / max_scroll) * track_height
        
        self.thumb_rect = pygame.Rect(self.rect.x, thumb_y, self.rect.width, thumb_height)
        
        thumb_color = theme_registry.get_color("windows", "text") if self.is_dragging else theme_registry.get_color("windows", "text_dim")
        pygame.draw.rect(screen, thumb_color, self.thumb_rect, border_radius=4)
