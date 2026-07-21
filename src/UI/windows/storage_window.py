import pygame
from .base_window import BaseWindow
from .components import ItemSlot, Scrollbar
from .window_frame import WindowFrame


class StorageWindow(BaseWindow):
    def __init__(self, screen_w, screen_h):
        frame = WindowFrame(screen_w, screen_h, 600, 700, "STORAGE")

        super().__init__(frame)
        self.storage = None
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
        y_start = self.frame.y + self.frame.HEADER_H + self.frame.PADDING + 50 
        
        self.cols = (self.frame.width - self.frame.PADDING * 2 - 20) // (slot_size + gap)
        rows = (self.frame.height - self.frame.HEADER_H - self.frame.PADDING * 2 - 50) // (slot_size + gap)
        
        self.scrollbar.update_rect(self.frame.x + self.frame.width - 12, y_start, 6, rows * (slot_size + gap) - gap)
        
        for row in range(rows):
            for col in range(self.cols):
                slot_x = x_start + col * (slot_size + gap)
                slot_y = y_start + row * (slot_size + gap)
                self.slots.append(ItemSlot(slot_x, slot_y, slot_size))

    def open(self, storage):
        self.storage = storage
        self.scroll = 0
        self.frame.open()


    def handle_event(self, event):
        if self.frame.handle_close_click(event):
            return True
            
        for slot in self.slots:
            slot.handle_event(event)
            
        items = list(self.storage.inventory.inventory.items()) if self.storage else []
        max_rows = max(0, (len(items) + self.cols - 1) // self.cols - 1)
        
        self.scroll = self.scrollbar.handle_event(event, self.scroll, max_rows)
            
        if event.type == pygame.MOUSEWHEEL:
            self.scroll = max(0, min(self.scroll - event.y, max_rows))
            
        return False

    def draw(self, screen, asset_manager=None):
        self.frame.draw_frame(screen)
        x_start = self.frame.x + self.frame.PADDING
        y_start = self.frame.y + self.frame.HEADER_H + self.frame.PADDING

        items = list(self.storage.inventory.inventory.items()) if self.storage else []
        hovered_name_for_tooltip = None

        if not items:
            self.frame.draw_label(screen, "Empty Storage", x_start, y_start, dim=True)
            return

        self.frame.draw_label(screen, f"Total item types: {len(items)}", x_start, y_start, dim=True)
        
        visible_items = items[self.scroll * self.cols:]

        for i, slot in enumerate(self.slots):
            if i < len(visible_items):
                item_name, amount = visible_items[i]
                slot.set_data(item_name, str(amount))
            else:
                slot.set_data(None)
                
            name = slot.draw(screen, asset_manager, self.frame.font, self.frame.font_small)
            if name:
                hovered_name_for_tooltip = name

        max_rows = max(0, (len(items) + self.cols - 1) // self.cols - 1)
        visible_ratio = min(1.0, len(self.slots) / len(items)) if items else 1.0
        self.scrollbar.draw(screen, self.scroll, max_rows, visible_ratio)

        if hovered_name_for_tooltip:
            self.frame.draw_tooltip(screen, hovered_name_for_tooltip)

