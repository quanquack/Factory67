import pygame

from src.registry import theme_registry


class WindowFrame:
    """Handles shared drawing and close button logic."""
    def __init__(self, screen_w, screen_h, width, height, title):
        self.screen_w = screen_w
        self.screen_h = screen_h

        self.width = width
        self.height = height
        self.x = (screen_w - width) // 2
        self.y = (screen_h - height) // 2
        self.title = title
        self.is_open = False

        self.HEADER_H = 32
        self.PADDING = 14
        self.BTN_H = 28

        self.font       = pygame.font.SysFont("Arial", 18)
        self.font_title = pygame.font.SysFont("Arial", 20, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 16)

        close_size = 20
        self.close_rect = pygame.Rect(
            self.x + self.width - close_size - 8,
            self.y + (self.HEADER_H - close_size) // 2,
            close_size, close_size
        )

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def open(self):
        self.is_open = True

    def close(self):
        self.is_open = False

    def handle_close_click(self, event) -> bool:
        """Returns True if the close button was clicked."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.close_rect.collidepoint(event.pos):
                self.close()
                return True
        return False
    
    def resize(self, width, height):
        self.width = width
        self.height = height
        
        self.x = (self.screen_w - self.width) // 2
        self.y = (self.screen_h - self.height) // 2
        
        close_size = 20
        self.close_rect = pygame.Rect(
            self.x + self.width - close_size - 8,
            self.y + (self.HEADER_H - close_size) // 2,
            close_size, close_size
        )

    def draw_frame(self, screen):
        shadow_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (0, 0, 0, 100), shadow_surf.get_rect(), border_radius=6)
        screen.blit(shadow_surf, (self.x + 6, self.y + 6))

        pygame.draw.rect(screen, theme_registry.get_color("windows","bg"), self.rect, border_radius=6)
        pygame.draw.rect(screen, theme_registry.get_color("windows","border"), self.rect, 1, border_radius=6)

        header_rect = pygame.Rect(self.x, self.y, self.width, self.HEADER_H)
        pygame.draw.rect(screen, theme_registry.get_color("windows","header"), header_rect,
                         border_top_left_radius=6, border_top_right_radius=6)

        title_surf = self.font_title.render(self.title, True, theme_registry.get_color("windows","text"))
        screen.blit(title_surf, (self.x + self.PADDING,
                                  self.y + (self.HEADER_H - title_surf.get_height()) // 2))

        mouse_pos = pygame.mouse.get_pos()
        close_color = theme_registry.get_color("windows","close_hover") if self.close_rect.collidepoint(mouse_pos) else theme_registry.get_color("windows","close")
        pygame.draw.rect(screen, close_color, self.close_rect, border_radius=4)
        x_surf = self.font_title.render("x", True, theme_registry.get_color("windows","text"))
        screen.blit(x_surf, (
            self.close_rect.centerx - x_surf.get_width() // 2,
            self.close_rect.centery - x_surf.get_height() // 2
        ))

    def draw_button(self, screen, rect, label, active=False, hovered=False):
        color = theme_registry.get_color("windows","button_active") if active else (theme_registry.get_color("windows","button_hover") if hovered else theme_registry.get_color("windows","button"))
        pygame.draw.rect(screen, color, rect, border_radius=4)
        pygame.draw.rect(screen, theme_registry.get_color("windows","border"), rect, 1, border_radius=4)
        surf = self.font.render(label, True, theme_registry.get_color("windows","text"))
        screen.blit(surf, (rect.centerx - surf.get_width() // 2,
                           rect.centery - surf.get_height() // 2))

    def draw_label(self, screen, text, x, y, dim=False):
        color = theme_registry.get_color("windows","text_dim") if dim else theme_registry.get_color("windows","text")
        surf = self.font.render(text, True, color)
        screen.blit(surf, (x, y))
        return surf.get_height()
    
    def draw_tooltip(self, screen, text):
        if not text:
            return
            
        mouse_pos = pygame.mouse.get_pos()
        tooltip_surf = self.font.render(f" {text} ", True, theme_registry.get_color("windows", "text"))
        
        tooltip_rect = tooltip_surf.get_rect(bottomleft=(mouse_pos[0] + 15, mouse_pos[1] - 15))
        
        pygame.draw.rect(screen, theme_registry.get_color("windows", "bg"), tooltip_rect, border_radius=3)
        pygame.draw.rect(screen, theme_registry.get_color("windows", "highlight"), tooltip_rect, 1, border_radius=3)
        
        screen.blit(tooltip_surf, tooltip_rect)
