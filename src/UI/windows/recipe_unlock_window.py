import pygame

from src.utils import format_number
from src.registry import machine_registry, theme_registry

from .base_window import BaseWindow
from .components import ItemSlot, Scrollbar
from .window_frame import WindowFrame

class RecipeUnlockWindow(BaseWindow):
    def __init__(
        self,
        screen_w,
        screen_h,
        economy
    ):
        frame = WindowFrame(
            screen_w,
            screen_h,
            660,
            630,
            "UNLOCK RECIPES"
        )

        super().__init__(frame)

        self.economy = economy
        self.inventory = None
        self.recipes = []
        self.recipe_rows = []
        self.hovered = None
        self.scroll = 0
        self.scrollbar = Scrollbar(0, 0, 6, 10)
    
    def open(self, inventory):
        self.inventory = inventory
        self.scroll = 0
        self.frame.open()
        self._collect_recipes()
        self._build_rects()

    def _collect_recipes(self):
        self.recipes = []
        for machine_type, data in machine_registry.machine_data.items():
            unlock_costs = data.get("metadata", {}).get("recipe_unlock_costs", {})
            for recipe_name, ingredients in data.get("recipes", {}).items():
                if recipe_name in unlock_costs:
                    cost = unlock_costs[recipe_name]
                    self.recipes.append((machine_type, recipe_name, ingredients, cost))

    def _build_rects(self):
        self.recipe_rows = []
        y = self.frame.y + self.frame.HEADER_H + self.frame.PADDING + 22
        
        slot_size = 48
        padding = 6
        row_h = slot_size + padding * 2
        
        list_height = self.frame.y + self.frame.height - self.frame.PADDING - y
        self.scrollbar.update_rect(self.frame.x + self.frame.width - 12, y, 6, list_height)
        
        for entry in self.recipes[self.scroll:]:
            if y + row_h > self.frame.y + self.frame.height - self.frame.PADDING:
                break
                
            machine_type, recipe_name, ingredients, cost = entry
            
            row_rect = pygame.Rect(self.frame.x + self.frame.PADDING, y,
                               self.frame.width - self.frame.PADDING * 2 - 20, row_h)
                               
            slot_x = row_rect.x + padding
            slot_y = row_rect.y + padding
            out_slot = ItemSlot(slot_x, slot_y, slot_size)
            out_slot.set_data(recipe_name)
            
            in_slots = []
            ing_x = slot_x + slot_size + 30
            for ing_name, ing_amt in ingredients.items():
                in_slot = ItemSlot(ing_x, slot_y, slot_size)
                in_slot.set_data(ing_name, str(ing_amt))
                in_slots.append(in_slot)
                ing_x += slot_size + 15
                
            btn_w = 140
            btn_rect = pygame.Rect(row_rect.right - btn_w - padding, row_rect.y + (row_h - self.frame.BTN_H)//2, btn_w, self.frame.BTN_H)
                
            self.recipe_rows.append({
                'entry': entry,
                'rect': row_rect,
                'out_slot': out_slot,
                'in_slots': in_slots,
                'btn_rect': btn_rect
            })
            y += row_h + 6

    def handle_event(self, event):
        if self.frame.handle_close_click(event):
            return True
            
        slot_size = 48
        padding = 6
        row_h = slot_size + padding * 2 + 6
        visible_capacity = self.scrollbar.rect.height // row_h
        max_scroll = max(0, len(self.recipes) - visible_capacity)
        
        old_scroll = self.scroll
        self.scroll = self.scrollbar.handle_event(event, self.scroll, max_scroll)
        if self.scroll != old_scroll:
            self._build_rects()
            return True
            
        if event.type == pygame.MOUSEWHEEL:
            self.scroll = max(0, min(self.scroll - event.y, max_scroll))
            self._build_rects()
            return True
            
        if event.type == pygame.MOUSEMOTION:
            self.hovered = None
            for row in self.recipe_rows:
                row['out_slot'].handle_event(event)
                for in_slot in row['in_slots']:
                    in_slot.handle_event(event)
                    
                if row['btn_rect'].collidepoint(event.pos):
                    self.hovered = row['entry'][1]
                    
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for row in self.recipe_rows:
                if row['btn_rect'].collidepoint(event.pos):
                    machine_type, recipe_name, ingredients, cost = row['entry']
                    if recipe_name not in self.inventory.unlocked_recipes:
                        if self.economy.deduct_money(cost):
                            self.inventory.unlocked_recipes.append(recipe_name)
                    return True
        return False

    def draw(self, screen, asset_manager=None):
        self.frame.draw_frame(screen)
        x = self.frame.x + self.frame.PADDING
        y = self.frame.y + self.frame.HEADER_H + self.frame.PADDING

        unlocked_count = sum(1 for _, r, _, _ in self.recipes if r in self.inventory.unlocked_recipes)
        
        self.frame.draw_label(screen, f"Unlocked: {unlocked_count} / {len(self.recipes)}   |   Balance: ${format_number(self.economy.money)}", x, y, dim=True)

        hovered_name_for_tooltip = None

        for row in self.recipe_rows:
            machine_type, recipe_name, ingredients, cost = row['entry']
            row_rect = row['rect']
            btn_rect = row['btn_rect']
            
            unlocked = recipe_name in self.inventory.unlocked_recipes
            can_afford = self.economy.money >= cost
            
            pygame.draw.rect(screen, theme_registry.get_color("windows", "bg"), row_rect, border_radius=4)
            pygame.draw.rect(screen, theme_registry.get_color("windows", "border"), row_rect, 1, border_radius=4)
            
            name = row['out_slot'].draw(screen, asset_manager, self.frame.font, self.frame.font_small)
            if name: hovered_name_for_tooltip = name
            
            eq_surf = self.frame.font.render("=", True, theme_registry.get_color("windows", "text"))
            screen.blit(eq_surf, (row['out_slot'].rect.right + 10, row['out_slot'].rect.centery - eq_surf.get_height() // 2))
            
            for i, in_slot in enumerate(row['in_slots']):
                name = in_slot.draw(screen, asset_manager, self.frame.font, self.frame.font_small)
                if name: hovered_name_for_tooltip = name
                
                if i < len(row['in_slots']) - 1:
                    plus_surf = self.frame.font.render("+", True, theme_registry.get_color("windows", "text"))
                    screen.blit(plus_surf, (in_slot.rect.right + 4, in_slot.rect.centery - plus_surf.get_height() // 2))
                    
            if unlocked:
                self.frame.draw_button(screen, btn_rect, "UNLOCKED", active=True)
            else:
                short_cost = format_number(cost)
                label = f"UNLOCK (${short_cost})"
                is_hovered = (self.hovered == recipe_name)
                self.frame.draw_button(screen, btn_rect, label, active=False, hovered=is_hovered and can_afford)

        slot_size = 48
        padding = 6
        row_h = slot_size + padding * 2 + 6
        visible_capacity = self.scrollbar.rect.height // row_h
        max_scroll = max(0, len(self.recipes) - visible_capacity)
        visible_ratio = min(1.0, visible_capacity / len(self.recipes)) if self.recipes else 1.0
        
        self.scrollbar.draw(screen, self.scroll, max_scroll, visible_ratio)

        if hovered_name_for_tooltip:
            self.frame.draw_tooltip(screen, hovered_name_for_tooltip)
