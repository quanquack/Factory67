import pygame

class MainMenu:
    """
    Represents the main menu interface of the game, including title and interactive buttons.
    """
    def __init__(self, screen_width, screen_height):
        """
        Initialize the main menu layout, styles, and UI elements.

        Args:
            screen_width (int): Width of the screen in pixels.
            screen_height (int): Height of the screen in pixels.
        """
        self.width = screen_width
        self.height = screen_height
        
        self.title_font = pygame.font.SysFont("Arial", 64, bold=True)
        self.button_font = pygame.font.SysFont("Arial", 32, bold=True)
        
        # Colors
        self.bg_color = (20, 22, 26)       
        self.btn_color = (50, 54, 63)      
        self.btn_hover_color = (75, 80, 95)
        self.text_color = (240, 240, 245)
        
        # Button layout setup
        btn_width = 300
        btn_height = 60
        center_x = self.width // 2 - btn_width // 2
        start_y = self.height // 2 - 50
        gap = 80
        
        
        self.buttons = {
            "continue": {"text": "CONTINUE GAME", "rect": pygame.Rect(center_x, start_y, btn_width, btn_height)},
            "new_game": {"text": "NEW GAME", "rect": pygame.Rect(center_x, start_y + gap, btn_width, btn_height)},
            "quit": {"text": "QUIT TO DESKTOP", "rect": pygame.Rect(center_x, start_y + gap * 2, btn_width, btn_height)}
        }

    def draw(self, screen):
        """
        Render the entire main menu, including background, title, and buttons.

        This method also applies hover effects based on the current mouse position.

        Args:
            screen: The surface to render the menu onto.
        """
        screen.fill(self.bg_color)
        
        # Draw title
        title_surf = self.title_font.render("FACTORY 67", True, (255, 215, 0)) # Màu vàng Gold
        title_rect = title_surf.get_rect(center=(self.width // 2, self.height // 4))
        screen.blit(title_surf, title_rect)
        
        # Draw shadow for depth effect  
        shadow_surf = self.title_font.render("FACTORY 67", True, (0, 0, 0))
        screen.blit(shadow_surf, (title_rect.x + 4, title_rect.y + 4))
        screen.blit(title_surf, title_rect)

        # Draw buttons with hover effect
        mouse_pos = pygame.mouse.get_pos()

        for key, btn in self.buttons.items():
            rect = btn["rect"]
            text = btn["text"]
            
            if rect.collidepoint(mouse_pos):
                pygame.draw.rect(screen, self.btn_hover_color, rect, border_radius=8)
            else:
                pygame.draw.rect(screen, self.btn_color, rect, border_radius=8)
                
            pygame.draw.rect(screen, self.text_color, rect, 2, border_radius=8)
            text_surf = self.button_font.render(text, True, self.text_color)
            text_rect = text_surf.get_rect(center=rect.center)
            screen.blit(text_surf, text_rect)

        pygame.display.flip()

    def handle_click(self, mouse_pos):
        """
        Determine which menu button was clicked based on mouse position.

        Args:
            mouse_pos (Tuple[int, int]): Mouse position on screen (x, y).

        Returns:
            str or None: The key of the clicked button ('continue', 'new_game', 'quit'),
            or None if no button was clicked.
        """
        for key, btn in self.buttons.items():
            if btn["rect"].collidepoint(mouse_pos):
                return key
        return None