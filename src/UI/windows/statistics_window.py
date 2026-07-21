import pygame

from src.registry import theme_registry
from .base_window import BaseWindow
from .components import ItemSlot, Scrollbar
from .window_frame import WindowFrame


class StatisticsWindow(BaseWindow):
    def __init__(self, screen_w, screen_h, game_manager):
        frame = WindowFrame(screen_w, screen_h, 570, 750, "FACTORY STATISTICS")

        super().__init__(frame)
        self.game_manager = game_manager
        self.scroll = 0
        self.slots = []
        self.cols = 0
        self.scrollbar = Scrollbar(0, 0, 6, 10)
        self._init_slots()

    def _init_slots(self):
        self.slots.clear()
        slot_size = 64
        gap = 10
        x_start = self.frame.x + self.frame.PADDING
        
        text_area_offset = 70
        y_start = self.frame.y + self.frame.HEADER_H + self.frame.PADDING + text_area_offset
        
        self.cols = (self.frame.width - self.frame.PADDING * 2) // (slot_size + gap)
        rows = (self.frame.height - self.frame.HEADER_H - self.frame.PADDING * 2 - text_area_offset) // (slot_size + gap)

        self.scrollbar.update_rect(self.frame.x + self.frame.width - 12, y_start, 6, rows * (slot_size + gap) - gap)
        
        for row in range(rows):
            for col in range(self.cols):
                slot_x = x_start + col * (slot_size + gap)
                slot_y = y_start + row * (slot_size + gap)
                self.slots.append(ItemSlot(slot_x, slot_y, slot_size))

    def open(self):
        self.scroll = 0
        self.frame.open()

    def handle_event(self, event):
        if self.frame.handle_close_click(event):
            return True
            
        for slot in self.slots:
            slot.handle_event(event)
            
        stored_items = getattr(self.game_manager.inventory, 'total_stored', {})
        max_rows = max(0, (len(stored_items) + self.cols - 1) // self.cols - 1)
        self.scroll = self.scrollbar.handle_event(event, self.scroll, max_rows)

        if event.type == pygame.MOUSEWHEEL:
            self.scroll = max(0, min(self.scroll - event.y, max_rows)) 
            return True
            
        return False
    
    def draw(self, screen, asset_manager=None):
        self.frame.draw_frame(screen)
        x_start = self.frame.x + self.frame.PADDING
        y_start = self.frame.y + self.frame.HEADER_H + self.frame.PADDING

        money_rate = getattr(self.game_manager.economy, 'money_rate', 0.0)
        self.frame.draw_label(screen, f"Income Rate: ${money_rate:.1f} / sec", x_start, y_start)
        y_start += 30
        
        pygame.draw.line(screen, theme_registry.get_color("windows", "border"), (x_start, y_start), (self.frame.x + self.frame.width - self.frame.PADDING, y_start))
        y_start += 15
        
        self.frame.draw_label(screen, "Storage Input Rates (items/sec):", x_start, y_start, dim=True)

        stored_items = getattr(self.game_manager.inventory, 'total_stored', {})
        rates = getattr(self.game_manager.inventory, 'item_rates', {})
        
        display_list = [(item, rates.get(item, 0.0)) for item in stored_items.keys()]
        display_list.sort(key=lambda item_rate: item_rate[1], reverse=True)

        hovered_name_for_tooltip = None

        if not display_list:
            self.frame.draw_label(screen, "No items in storage", x_start, y_start + 25, dim=True)
        else:
            visible_items = display_list[self.scroll * self.cols:]

            for i, slot in enumerate(self.slots):
                if i < len(visible_items):
                    item_name, rate = visible_items[i]
                    slot.set_data(item_name, f"{rate:.1f}")
                else:
                    slot.set_data(None)
                    
                name = slot.draw(screen, asset_manager, self.frame.font, self.frame.font_small)
                if name:
                    hovered_name_for_tooltip = name

            max_rows = max(0, (len(display_list) + self.cols - 1) // self.cols - 1)
            visible_ratio = min(1.0, len(self.slots) / len(display_list)) if display_list else 1.0
            self.scrollbar.draw(screen, self.scroll, max_rows, visible_ratio)

        if hovered_name_for_tooltip:
            self.frame.draw_tooltip(screen, hovered_name_for_tooltip)