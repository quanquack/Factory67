import pygame

from src.registry import machine_registry, theme_registry

from .base_window import BaseWindow
from .components import ItemSlot, Scrollbar
from .window_frame import WindowFrame


class MachineWindow(BaseWindow):
    def __init__(
        self,
        screen_w,
        screen_h,
        game_manager
    ):
        frame = WindowFrame(
            screen_w,
            screen_h,
            630,
            360,
            "MACHINE STATUS"
        )

        super().__init__(frame)

        self.game_manager = game_manager
        self.player_inventory = game_manager.inventory

        self.machine = None
        self.upgrade_rect = None
        self.recipe_rows = []
        self.hovered_recipe = None
        self.hovered_upgrade = False
        self.upgrade_slots = []
        self.scroll = 0
        self.scrollbar = Scrollbar(0, 0, 6, 10)
    
    def open(self, machine):
        self.machine = machine
        name = machine.get_asset_name()
        
        if hasattr(self.machine, 'recipe_manager') and self.machine.recipe_manager.require_selection:
            self.frame.resize(630, 580)
        else:
            self.frame.resize(630, 360)

        self.frame.title = f"{name.upper()} MENU"
        self.scroll = 0
        self.frame.open()
        self._init_upgrade_slots()
        self._build_rects()

    def _init_upgrade_slots(self):
        self.upgrade_slots = []
        if not self.machine or self.machine.level >= 4:
            return
            
        x_start = self.frame.x + self.frame.PADDING
        y_start = self.frame.y + self.frame.HEADER_H + self.frame.PADDING + 35 
        slot_size = 64
        gap = 10
        
        for i in range(5):
            slot_x = x_start + i * (slot_size + gap)
            slot_y = y_start
            self.upgrade_slots.append(ItemSlot(slot_x, slot_y, slot_size))

    def _build_rects(self):
        self.recipe_rows = []
        self.upgrade_rect = None
        
        y = self.frame.y + self.frame.HEADER_H + self.frame.PADDING
        
        y += 25 
        if self.machine and self.machine.level >= 4:
            y += 75
        else:
            y += 64 + 15 
            y += self.frame.BTN_H + 15 

        if hasattr(self.machine, 'recipe_manager') and self.machine.recipe_manager.require_selection:
            y += 20
            y += 10
            y += 25

            list_height = self.frame.y + self.frame.height - self.frame.PADDING - y
            self.scrollbar.update_rect(self.frame.x + self.frame.width - 12, y, 6, list_height)
            
            m_type = self.machine.get_asset_name()
            unlock_costs = machine_registry.get_metadata(m_type).get("recipe_unlock_costs", {})
            
            slot_size = 48
            padding = 6

            valid_recipes = [r for r in self.machine.recipe_manager.recipes if not (r in unlock_costs and r not in self.player_inventory.unlocked_recipes)]

            for recipe in valid_recipes[self.scroll:]:
                rect_h = slot_size + padding * 2
                
                if y + rect_h > self.frame.y + self.frame.height - self.frame.PADDING:
                    break
                    
                row_rect = pygame.Rect(self.frame.x + self.frame.PADDING, y,
                                   self.frame.width - self.frame.PADDING * 2 - 20, rect_h)
                                   
                slot_x = row_rect.x + padding
                slot_y = row_rect.y + padding
                out_slot = ItemSlot(slot_x, slot_y, slot_size)
                out_slot.set_data(recipe)
                
                in_slots = []
                ing_x = slot_x + slot_size + 30
                ingredients = self.machine.recipe_manager.recipes[recipe]
                
                for ing_name, ing_amt in ingredients.items():
                    in_slot = ItemSlot(ing_x, slot_y, slot_size)
                    in_slot.set_data(ing_name, str(ing_amt))
                    in_slots.append(in_slot)
                    ing_x += slot_size + 15
                    
                self.recipe_rows.append({
                    'recipe': recipe,
                    'rect': row_rect,
                    'out_slot': out_slot,
                    'in_slots': in_slots
                })
                y += rect_h + 6

    def handle_event(self, event):
        if self.frame.handle_close_click(event):
            return True
            
        for slot in self.upgrade_slots:
            slot.handle_event(event)
            
        for row in self.recipe_rows:
            row['out_slot'].handle_event(event)
            for in_slot in row['in_slots']:
                in_slot.handle_event(event)
                
        if hasattr(self.machine, 'recipe_manager') and self.machine.recipe_manager.require_selection:
            m_type = self.machine.get_asset_name()
            unlock_costs = machine_registry.get_metadata(m_type).get("recipe_unlock_costs", {})
            valid_recipes = [r for r in self.machine.recipe_manager.recipes if not (r in unlock_costs and r not in self.player_inventory.unlocked_recipes)]
            
            visible_capacity = (self.frame.height - self.scrollbar.rect.y) // 60
            max_scroll = max(0, len(valid_recipes) - visible_capacity)

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
            self.hovered_upgrade = self.upgrade_rect is not None and self.upgrade_rect.collidepoint(event.pos)
            self.hovered_recipe = None
            for row in self.recipe_rows:
                if row['rect'].collidepoint(event.pos):
                    self.hovered_recipe = row['recipe']
                    
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.upgrade_rect and self.upgrade_rect.collidepoint(event.pos):
                mods = pygame.key.get_mods()
                if mods & pygame.KMOD_SHIFT:
                    target_type = getattr(self.machine, 'machine_type', 'miner') if hasattr(self.machine, 'machine_type') else 'miner'
                    target_level = self.machine.level
                    for chunk in self.game_manager.game_map.chunks.values():
                        for entity in chunk.grid.values():
                            class_name = type(entity).__name__
                            if class_name in ('Machine', 'Miner'):
                                e_type = getattr(entity, 'machine_type', 'miner') if hasattr(entity, 'machine_type') else 'miner'
                                if e_type == target_type and getattr(entity, 'level', 1) == target_level:
                                    entity.upgrade(self.player_inventory)
                else:
                    self.machine.upgrade(self.player_inventory)
                
                self._init_upgrade_slots()
                self._build_rects()
                return True
                
            for row in self.recipe_rows:
                if row['rect'].collidepoint(event.pos):
                    self.machine.set_machine_recipe(row['recipe'])
                    return True
                    
        return False

    def draw(self, screen, asset_manager=None):
        self.frame.draw_frame(screen)
        x = self.frame.x + self.frame.PADDING
        y = self.frame.y + self.frame.HEADER_H + self.frame.PADDING
        
        hovered_name_for_tooltip = None

        # --- UPGRADE SECTION ---
        self.frame.draw_label(screen, f"Level:  {self.machine.level} / 4", x, y)
        y += 25

        if self.machine.level >= 4:
            self.frame.draw_label(screen, "FULLY UPGRADED", x, y, dim=True)
            self.upgrade_rect = None
            y += 75
        else:
            m_type = self.machine.get_asset_name()
            costs = machine_registry.get_metadata(m_type).get("upgrade_costs", [])
            cost = costs[self.machine.level - 1] if self.machine.level - 1 < len(costs) else {}

            can_afford = True
            for i, slot in enumerate(self.upgrade_slots):
                if i < len(cost):
                    item_name = list(cost.keys())[i]
                    amount_needed = cost[item_name]
                    have = self.player_inventory.inventory.get(item_name, 0)
                    if have < amount_needed:
                        can_afford = False
                        color = theme_registry.get_color("windows", "expensive")
                    else:
                        color = theme_registry.get_color("windows", "affordable")
                    slot.set_data(item_name, f"{have}/{amount_needed}", color)
                    name = slot.draw(screen, asset_manager, self.frame.font, self.frame.font_small)
                    if name: hovered_name_for_tooltip = name
                else:
                    slot.set_data(None)
                    slot.draw(screen, asset_manager, self.frame.font, self.frame.font_small)

            y += 64 + 15
            self.upgrade_rect = pygame.Rect(x, y, self.frame.width - self.frame.PADDING * 2, self.frame.BTN_H)
            self.frame.draw_button(screen, self.upgrade_rect, "UPGRADE (SHIFT to mass upgrade)",
                                   active=can_afford, hovered=self.hovered_upgrade and can_afford)
            y += self.frame.BTN_H + 15

        # --- RECIPE SECTION ---
        if hasattr(self.machine, 'recipe_manager') and self.machine.recipe_manager.require_selection:
            pygame.draw.line(screen, (75, 80, 95), (x, y), (self.frame.x + self.frame.width - self.frame.PADDING, y))
            y += 10
            
            self.frame.draw_label(screen, "Select Recipe:", x, y, dim=True)
            
            selected = self.machine.recipe_manager.selected_recipe
            
            for row in self.recipe_rows:
                recipe = row['recipe']
                rect = row['rect']
                is_selected = (recipe == selected)
                is_hovered = (recipe == self.hovered_recipe)
                
                bg_color = theme_registry.get_color("windows", "button_active") if is_selected else (
                           theme_registry.get_color("windows", "button_hover") if is_hovered else 
                           theme_registry.get_color("windows", "button"))
                           
                pygame.draw.rect(screen, bg_color, rect, border_radius=4)
                pygame.draw.rect(screen, theme_registry.get_color("windows", "border"), rect, 1, border_radius=4)
                
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

            m_type = self.machine.get_asset_name()
            unlock_costs = machine_registry.get_metadata(m_type).get("recipe_unlock_costs", {})
            valid_recipes = [r for r in self.machine.recipe_manager.recipes if not (r in unlock_costs and r not in self.player_inventory.unlocked_recipes)]
            
            visible_capacity = (self.frame.height - self.scrollbar.rect.y) // 60
            max_scroll = max(0, len(valid_recipes) - visible_capacity)
            visible_ratio = min(1.0, visible_capacity / len(valid_recipes)) if valid_recipes else 1.0
            
            self.scrollbar.draw(screen, self.scroll, max_scroll, visible_ratio)

        if hovered_name_for_tooltip:
            self.frame.draw_tooltip(screen, hovered_name_for_tooltip)