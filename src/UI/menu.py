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
            "new_game": {"text": "NEW GAME", "rect": pygame.Rect(center_x, start_y, btn_width, btn_height)},
            "continue": {"text": "CONTINUE GAME", "rect": pygame.Rect(center_x, start_y + gap, btn_width, btn_height)},
            "tutorial": {"text": "HOW TO PLAY", "rect": pygame.Rect(center_x, start_y + gap * 2, btn_width, btn_height)},
            "quit": {"text": "QUIT TO DESKTOP", "rect": pygame.Rect(center_x, start_y + gap * 3, btn_width, btn_height)}
        }

        self.show_tutorial = False
        self.tutorial_font = pygame.font.SysFont("Arial", 22)
        self.tutorial_lines = [
            "WELCOME TO THE FACTORY",
            "",
            "- Camera: Press Q to toggle PAN/BUILD. Click & drag to pan, scroll to zoom.",
            "- Extracting: Press 1 to build Miners directly on ore patches.",
            "- Logistics: Press 3 for Conveyors. Hold left click and drag to build lines.",
            "- Processing: Press 2 to cycle Smelters/Assemblers. Click them to set recipes.",
            "- Traffic: Press 4 for Mergers, 5 for Routers (Filters/Splitters).",
            "- Economy: Route items to Seller to earn cash, or Storage to keep them.",
            "- Hotkeys: Press R to rotate. Press ESC to pause and save."
        ]
        self.back_btn_rect = pygame.Rect(self.width // 2 - 100, self.height - 90, 200, 50)

    def draw(self, screen):
        """
        Render the entire main menu, including background, title, and buttons.

        This method also applies hover effects based on the current mouse position.

        Args:
            screen: The surface to render the menu onto.
        """
        screen.fill(self.bg_color)

        if self.show_tutorial:
            panel_rect = pygame.Rect(self.width // 2 - 380, 40, 760, self.height - 150)
            pygame.draw.rect(screen, (30, 33, 40), panel_rect, border_radius=12)
            pygame.draw.rect(screen, (75, 80, 95), panel_rect, 2, border_radius=12)
            
            y_offset = 70
            for line in self.tutorial_lines:
                color = (255, 215, 0) if line == "WELCOME TO THE FACTORY" else self.text_color
                text_surf = self.tutorial_font.render(line, True, color)
                screen.blit(text_surf, (self.width // 2 - text_surf.get_width() // 2, y_offset))
                y_offset += 40
                
            mouse_pos = pygame.mouse.get_pos()
            if self.back_btn_rect.collidepoint(mouse_pos):
                pygame.draw.rect(screen, self.btn_hover_color, self.back_btn_rect, border_radius=8)
            else:
                pygame.draw.rect(screen, self.btn_color, self.back_btn_rect, border_radius=8)
            pygame.draw.rect(screen, self.text_color, self.back_btn_rect, 2, border_radius=8)
            
            back_surf = self.button_font.render("BACK", True, self.text_color)
            screen.blit(back_surf, back_surf.get_rect(center=self.back_btn_rect.center))
        else:
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
        if self.show_tutorial:
            if self.back_btn_rect.collidepoint(mouse_pos):
                self.show_tutorial = False
            return None
            
        for key, btn in self.buttons.items():
            if btn["rect"].collidepoint(mouse_pos):
                if key == "tutorial":
                    self.show_tutorial = True
                    return None
                return key
        return None