import pygame

from src.registry import item_registry, theme_registry
from .base_window import BaseWindow
from .window_frame import WindowFrame

class RouterConfigWindow(BaseWindow):
    def __init__(self, screen_w, screen_h):
        frame = WindowFrame(
            screen_w,
            screen_h,
            600,
            510,
            "ROUTER CONFIG"
        )

        super().__init__(frame)

        self.router = None
        self.slot_rects = []
        self.hovered_slot = None
        self.editing_slot = None
        self.input_text = ""

        self.dropdown_open = False
        self.dropdown_slot = None
        self.dropdown_options = []
        self.dropdown_scroll = 0
        self.dropdown_hovered = None
        self.dropdown_visible_items = 5

        self.direction_text = {
            "N": "↑",
            "S": "↓",
            "E": "→",
            "W": "←",
        }
        
    def open(self, router):
        self.router = router
        self.editing_slot = None
        self.input_text = ""
        
        self.dropdown_open = False
        self.dropdown_slot = None
        self.dropdown_scroll = 0
        
        self.frame.open()
        self._build_slot_rects()
        
        if self.router.mode == 'filter':
            self.dropdown_options = [("FALLBACK", 0), ("NONE", -1)]
            for item_name in item_registry.item_data.keys():
                display = item_registry.get_display_name(item_name)
                self.dropdown_options.append((display.upper(), item_name))

    def _build_slot_rects(self):
        self.slot_rects = []
        y = self.frame.y + self.frame.HEADER_H + self.frame.PADDING + 24
        for i, direction in enumerate(self.router.output_dirs):
            rect = pygame.Rect(self.frame.x + self.frame.PADDING, y,
                               self.frame.width - self.frame.PADDING * 2,
                               self.frame.BTN_H)
            self.slot_rects.append((i, direction, rect))
            y += self.frame.BTN_H + 8

    def _get_dropdown_rect(self):
        if self.dropdown_slot is None:
            return pygame.Rect(0, 0, 0, 0)
        slot_rect = self.slot_rects[self.dropdown_slot][2]
        h = min(len(self.dropdown_options), self.dropdown_visible_items) * self.frame.BTN_H
        return pygame.Rect(slot_rect.x, slot_rect.bottom, slot_rect.width, h)

    def _apply_filter_selection(self, val):
        new_config = list(self.router.config) if self.router.config else [0] * 3
        slot = self.dropdown_slot
        
        if val == 0:
            for idx in range(3):
                if idx != slot and new_config[idx] == 0:
                    new_config[idx] = -1
        
        if val != 0 and self.router.config[slot] == 0:
            for idx in range(3):
                if idx != slot and new_config[idx] == -1:
                    new_config[idx] = 0
                    break
            else: 
                for idx in range(3):
                    if idx != slot:
                        new_config[idx] = 0
                        break

        new_config[slot] = val
        self.router.set_config(new_config)

    def handle_event(self, event):
        if self.frame.handle_close_click(event):
            return True
            
        if self.dropdown_open:
            dd_rect = self._get_dropdown_rect()
            
            if event.type == pygame.MOUSEWHEEL:
                mouse_pos = pygame.mouse.get_pos()
                if dd_rect.collidepoint(mouse_pos):
                    max_scroll = max(0, len(self.dropdown_options) - self.dropdown_visible_items)
                    self.dropdown_scroll = max(0, min(self.dropdown_scroll - event.y, max_scroll))
                    
                    rel_y = mouse_pos[1] - dd_rect.y
                    idx = self.dropdown_scroll + (rel_y // self.frame.BTN_H)
                    if idx < len(self.dropdown_options):
                        self.dropdown_hovered = idx
                return True
                
            if event.type == pygame.MOUSEMOTION:
                self.dropdown_hovered = None
                if dd_rect.collidepoint(event.pos):
                    rel_y = event.pos[1] - dd_rect.y
                    idx = self.dropdown_scroll + (rel_y // self.frame.BTN_H)
                    if idx < len(self.dropdown_options):
                        self.dropdown_hovered = idx
                return True
                
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if dd_rect.collidepoint(event.pos):
                    rel_y = event.pos[1] - dd_rect.y
                    idx = self.dropdown_scroll + (rel_y // self.frame.BTN_H)
                    if idx < len(self.dropdown_options):
                        val = self.dropdown_options[idx][1]
                        self._apply_filter_selection(val)
                self.dropdown_open = False
                self.dropdown_slot = None
                return True
        
        if event.type == pygame.MOUSEMOTION:
            self.hovered_slot = None
            for i, direction, rect in self.slot_rects:
                if rect.collidepoint(event.pos):
                    self.hovered_slot = i
                    
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            clicked_inside_slot = False
            for i, direction, rect in self.slot_rects:
                if rect.collidepoint(event.pos):
                    if self.router.mode == 'splitter':
                        self.editing_slot = i
                        current = self.router.config[i] if self.router.config else 0
                        self.input_text = str(current) if current != 0 else ""
                    else:
                        self.dropdown_open = True
                        self.dropdown_slot = i
                        self.dropdown_scroll = 0
                        self.dropdown_hovered = None
                    clicked_inside_slot = True
                    return True
                    
            if not clicked_inside_slot:
                self.editing_slot = None
                
        if event.type == pygame.KEYDOWN and self.editing_slot is not None:
            if event.key == pygame.K_RETURN:
                new_config = list(self.router.config) if self.router.config else [0] * 3
                if self.router.mode == 'splitter':
                    try:
                        val = int(self.input_text)
                        if val >= 0:
                            new_config[self.editing_slot] = val
                            self.router.set_config(new_config)
                    except ValueError:
                        pass
                self.editing_slot = None
                self.input_text = ""
            elif event.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
            elif event.unicode.isprintable():
                self.input_text += event.unicode
                
            return True 
            
        return False

    def draw(self, screen, asset_manager=None):
        self.frame.draw_frame(screen)
        x = self.frame.x + self.frame.PADDING
        y = self.frame.y + self.frame.HEADER_H + self.frame.PADDING

        if self.router.mode == 'splitter':
            self.frame.draw_label(screen, "Mode: SPLITTER  |  Click to set weights", x, y, dim=True)
        else:
            self.frame.draw_label(screen, "Mode: FILTER  |  Click to select item", x, y, dim=True)

        for i, direction, rect in self.slot_rects:
            is_editing = (self.editing_slot == i) or (self.dropdown_slot == i)
            is_hovered = self.hovered_slot == i

            if self.router.mode == 'splitter':
                weight = self.router.config[i] if self.router.config else 0
                label = f"[{self.direction_text[direction]}] Slot {i}:  weight = {self.input_text if self.editing_slot == i else weight}"
            else:
                rule = self.router.config[i] if self.router.config else 0
                if rule == 0:
                    display_rule = "FALLBACK"
                elif rule == -1:
                    display_rule = "NONE"
                else:
                    display_rule = item_registry.get_display_name(rule).upper()
                    
                label = f"[{self.direction_text[direction]}] Slot {i}:  {display_rule}"

            self.frame.draw_button(screen, rect, label,
                                   active=is_editing,
                                   hovered=is_hovered and not is_editing)

        if self.dropdown_open:
            dd_rect = self._get_dropdown_rect()
            
            pygame.draw.rect(screen, theme_registry.get_color("windows","bg"), dd_rect, border_radius=4)
            pygame.draw.rect(screen, theme_registry.get_color("windows","border"), dd_rect, 1, border_radius=4)
            
            for i in range(self.dropdown_visible_items):
                idx = self.dropdown_scroll + i
                if idx >= len(self.dropdown_options):
                    break
                    
                opt_label, opt_val = self.dropdown_options[idx]
                opt_rect = pygame.Rect(dd_rect.x, dd_rect.y + i * self.frame.BTN_H, dd_rect.width, self.frame.BTN_H)
                
                is_hovered = (self.dropdown_hovered == idx)
                is_active = (opt_val == self.router.config[self.dropdown_slot])
                
                self.frame.draw_button(screen, opt_rect, opt_label, active=is_active, hovered=is_hovered and not is_active)
