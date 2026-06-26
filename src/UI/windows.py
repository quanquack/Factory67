import pygame
from src.registry import item_registry, machine_registry

COLORS = {
    "bg":          (20, 22, 26),
    "border":      (75, 80, 95),
    "header":      (30, 33, 40),
    "button":      (50, 55, 68),
    "button_hover":(70, 76, 92),
    "button_active":(80, 120, 80),
    "text":        (240, 240, 245),
    "text_dim":    (150, 155, 165),
    "close":       (160, 60, 60),
    "close_hover": (200, 80, 80),
}

class WindowFrame:
    """Handles shared drawing and close button logic."""
    def __init__(self, screen_w, screen_h, width, height, title):
        self.width = width
        self.height = height
        self.x = (screen_w - width) // 2
        self.y = (screen_h - height) // 2
        self.title = title
        self.is_open = False

        self.HEADER_H = 32
        self.PADDING = 14
        self.BTN_H = 28

        self.font       = pygame.font.SysFont("Arial", 13)
        self.font_title = pygame.font.SysFont("Arial", 14, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 11)

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

    def draw_frame(self, screen):
        pygame.draw.rect(screen, COLORS["bg"], self.rect, border_radius=6)
        pygame.draw.rect(screen, COLORS["border"], self.rect, 1, border_radius=6)

        header_rect = pygame.Rect(self.x, self.y, self.width, self.HEADER_H)
        pygame.draw.rect(screen, COLORS["header"], header_rect,
                         border_top_left_radius=6, border_top_right_radius=6)

        title_surf = self.font_title.render(self.title, True, COLORS["text"])
        screen.blit(title_surf, (self.x + self.PADDING,
                                  self.y + (self.HEADER_H - title_surf.get_height()) // 2))

        mouse_pos = pygame.mouse.get_pos()
        close_color = COLORS["close_hover"] if self.close_rect.collidepoint(mouse_pos) else COLORS["close"]
        pygame.draw.rect(screen, close_color, self.close_rect, border_radius=4)
        x_surf = self.font_title.render("x", True, COLORS["text"])
        screen.blit(x_surf, (
            self.close_rect.centerx - x_surf.get_width() // 2,
            self.close_rect.centery - x_surf.get_height() // 2
        ))

    def draw_button(self, screen, rect, label, active=False, hovered=False):
        color = COLORS["button_active"] if active else (COLORS["button_hover"] if hovered else COLORS["button"])
        pygame.draw.rect(screen, color, rect, border_radius=4)
        pygame.draw.rect(screen, COLORS["border"], rect, 1, border_radius=4)
        surf = self.font.render(label, True, COLORS["text"])
        screen.blit(surf, (rect.centerx - surf.get_width() // 2,
                           rect.centery - surf.get_height() // 2))

    def draw_label(self, screen, text, x, y, dim=False):
        color = COLORS["text_dim"] if dim else COLORS["text"]
        surf = self.font.render(text, True, color)
        screen.blit(surf, (x, y))
        return surf.get_height()
    
class MachineWindow:
    def __init__(self, screen_w, screen_h, player_inventory):
        self.frame = WindowFrame(screen_w, screen_h, 420, 480, "MACHINE STATUS")
        self.player_inventory = player_inventory
        self.machine = None
        self.upgrade_rect = None
        self.recipe_rects = []
        self.hovered_recipe = None
        self.hovered_upgrade = False

    @property
    def is_open(self):
        return self.frame.is_open

    def open(self, machine):
        self.machine = machine

        name = machine.get_asset_name()
        self.frame.title = f"{name.upper()} MENU"
            
        self.frame.open()
        self._build_rects()

    def close(self):
        self.frame.close()

    def _build_rects(self):
        self.recipe_rects = []
        self.upgrade_rect = None
        
        y = self.frame.y + self.frame.HEADER_H + self.frame.PADDING
        y += 120

        if hasattr(self.machine, 'recipe_manager') and self.machine.recipe_manager.require_selection:
            y += 20
            
            m_type = getattr(self.machine, 'machine_type', '')
            unlock_costs = machine_registry.get_metadata(m_type).get("recipe_unlock_costs", {})
            
            for recipe in self.machine.recipe_manager.recipes:
                if recipe in unlock_costs and recipe not in self.player_inventory.unlocked_recipes:
                    continue
                    
                rect = pygame.Rect(self.frame.x + self.frame.PADDING, y,
                                   self.frame.width - self.frame.PADDING * 2,
                                   self.frame.BTN_H)
                self.recipe_rects.append((recipe, rect))
                y += self.frame.BTN_H + 6

    def handle_event(self, event):
        if self.frame.handle_close_click(event):
            return True
            
        if event.type == pygame.MOUSEMOTION:
            self.hovered_upgrade = self.upgrade_rect is not None and self.upgrade_rect.collidepoint(event.pos)
            self.hovered_recipe = None
            for recipe, rect in self.recipe_rects:
                if rect.collidepoint(event.pos):
                    self.hovered_recipe = recipe
                    
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.upgrade_rect and self.upgrade_rect.collidepoint(event.pos):
                self.machine.upgrade(self.player_inventory)
                return True
                
            for recipe, rect in self.recipe_rects:
                if rect.collidepoint(event.pos):
                    self.machine.set_machine_recipe(recipe)
                    return True
                    
        return False

    def draw(self, screen):
        self.frame.draw_frame(screen)
        x = self.frame.x + self.frame.PADDING
        y = self.frame.y + self.frame.HEADER_H + self.frame.PADDING

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
            for item, amount in cost.items():
                have = self.player_inventory.inventory.get(item, 0)
                if have < amount:
                    can_afford = False
                    
                color = (240, 240, 245) if have >= amount else (180, 80, 80)
                surf = self.frame.font.render(f"  {item}:  {have} / {amount}", True, color)
                screen.blit(surf, (x, y))
                y += 18

            y += 10
            self.upgrade_rect = pygame.Rect(x, y, self.frame.width - self.frame.PADDING * 2, self.frame.BTN_H)
            self.frame.draw_button(screen, self.upgrade_rect, "UPGRADE",
                                   active=can_afford,
                                   hovered=self.hovered_upgrade and can_afford)
            y += self.frame.BTN_H + 10

        # --- RECIPE SECTION ---
        if hasattr(self.machine, 'recipe_manager') and self.machine.recipe_manager.require_selection:
            pygame.draw.line(screen, (75, 80, 95), (x, y), (self.frame.x + self.frame.width - self.frame.PADDING, y))
            y += 10
            
            self.frame.draw_label(screen, "Select Recipe:", x, y, dim=True)
            y += 20
            
            selected = self.machine.recipe_manager.selected_recipe
            for recipe, rect in self.recipe_rects:
                self.frame.draw_button(screen, rect, recipe.upper(),
                                       active=(recipe == selected),
                                       hovered=(recipe == self.hovered_recipe))


class StorageWindow:
    def __init__(self, screen_w, screen_h):
        self.frame = WindowFrame(screen_w, screen_h, 340, 400, "STORAGE")
        self.storage = None
        self.scroll = 0

    @property
    def is_open(self):
        return self.frame.is_open

    def open(self, storage):
        self.storage = storage
        self.scroll = 0
        self.frame.open()

    def close(self):
        self.frame.close()

    def handle_event(self, event):
        if self.frame.handle_close_click(event):
            return True
        if event.type == pygame.MOUSEWHEEL:
            items = list(self.storage.inventory.inventory.items())
            self.scroll = max(0, min(self.scroll - event.y, len(items) - 1))
        return False

    def draw(self, screen):
        self.frame.draw_frame(screen)
        x = self.frame.x + self.frame.PADDING
        y = self.frame.y + self.frame.HEADER_H + self.frame.PADDING

        items = list(self.storage.inventory.inventory.items())

        if not items:
            self.frame.draw_label(screen, "Empty", x, y, dim=True)
            return

        # total count header
        self.frame.draw_label(screen, f"{len(items)} item types stored", x, y, dim=True)
        y += 22

        for item_name, amount in items[self.scroll:]:
            if y + 18 > self.frame.y + self.frame.height - self.frame.PADDING:
                break
            display = item_registry.get_display_name(item_name)
            self.frame.draw_label(screen, f"{display}:  {amount}", x, y)
            y += 20


class RouterConfigWindow:
    def __init__(self, screen_w, screen_h):
        self.frame = WindowFrame(screen_w, screen_h, 400, 340, "ROUTER CONFIG")
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

    @property
    def is_open(self):
        return self.frame.is_open

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

    def close(self):
        self.frame.close()

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

    def draw(self, screen):
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
                label = f"[{direction}] Slot {i}:  weight = {self.input_text if self.editing_slot == i else weight}"
            else:
                rule = self.router.config[i] if self.router.config else 0
                if rule == 0:
                    display_rule = "FALLBACK"
                elif rule == -1:
                    display_rule = "NONE"
                else:
                    display_rule = item_registry.get_display_name(rule).upper()
                    
                label = f"[{direction}] Slot {i}:  {display_rule}"

            self.frame.draw_button(screen, rect, label,
                                   active=is_editing,
                                   hovered=is_hovered and not is_editing)

        if self.dropdown_open:
            dd_rect = self._get_dropdown_rect()
            
            pygame.draw.rect(screen, COLORS["bg"], dd_rect, border_radius=4)
            pygame.draw.rect(screen, COLORS["border"], dd_rect, 1, border_radius=4)
            
            for i in range(self.dropdown_visible_items):
                idx = self.dropdown_scroll + i
                if idx >= len(self.dropdown_options):
                    break
                    
                opt_label, opt_val = self.dropdown_options[idx]
                opt_rect = pygame.Rect(dd_rect.x, dd_rect.y + i * self.frame.BTN_H, dd_rect.width, self.frame.BTN_H)
                
                is_hovered = (self.dropdown_hovered == idx)
                is_active = (opt_val == self.router.config[self.dropdown_slot])
                
                self.frame.draw_button(screen, opt_rect, opt_label, active=is_active, hovered=is_hovered and not is_active)


class RecipeUnlockWindow:
    def __init__(self, screen_w, screen_h, economy):
        self.frame = WindowFrame(screen_w, screen_h, 440, 420, "UNLOCK RECIPES")
        self.economy = economy
        self.inventory = None
        self.recipes = []
        self.recipe_rects = []
        self.hovered = None
        self.scroll = 0

    @property
    def is_open(self):
        return self.frame.is_open

    def open(self, inventory):
        self.inventory = inventory
        self.scroll = 0
        self.frame.open()
        self._collect_recipes()
        self._build_rects()

    def close(self):
        self.frame.close()

    def _collect_recipes(self):
        self.recipes = []
        for machine_type, data in machine_registry.machine_data.items():
            unlock_costs = data.get("metadata", {}).get("recipe_unlock_costs", {})
            for recipe_name, ingredients in data.get("recipes", {}).items():
                if recipe_name in unlock_costs:
                    cost = unlock_costs[recipe_name]
                    self.recipes.append((machine_type, recipe_name, ingredients, cost))

    def _build_rects(self):
        self.recipe_rects = []
        y = self.frame.y + self.frame.HEADER_H + self.frame.PADDING + 22
        for entry in self.recipes[self.scroll:]:
            if y + self.frame.BTN_H > self.frame.y + self.frame.height - self.frame.PADDING:
                break
            rect = pygame.Rect(self.frame.x + self.frame.PADDING, y,
                               self.frame.width - self.frame.PADDING * 2,
                               self.frame.BTN_H)
            self.recipe_rects.append((entry, rect))
            y += self.frame.BTN_H + 6

    def handle_event(self, event):
        if self.frame.handle_close_click(event):
            return True
        if event.type == pygame.MOUSEWHEEL:
            self.scroll = max(0, min(self.scroll - event.y, len(self.recipes) - 1))
            self._build_rects()
        if event.type == pygame.MOUSEMOTION:
            self.hovered = None
            for entry, rect in self.recipe_rects:
                if rect.collidepoint(event.pos):
                    self.hovered = entry[1]
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for (machine_type, recipe_name, ingredients, cost), rect in self.recipe_rects:
                if rect.collidepoint(event.pos):
                    if recipe_name not in self.inventory.unlocked_recipes:
                        if self.economy.deduct_money(cost):
                            self.inventory.unlocked_recipes.append(recipe_name)
                    return True
        return False

    def draw(self, screen):
        self.frame.draw_frame(screen)
        x = self.frame.x + self.frame.PADDING
        y = self.frame.y + self.frame.HEADER_H + self.frame.PADDING

        unlocked_count = sum(1 for _, r, _, _ in self.recipes if r in self.inventory.unlocked_recipes)
        self.frame.draw_label(screen, f"Unlocked: {unlocked_count} / {len(self.recipes)}   |   Balance: ${self.economy.money}", x, y, dim=True)
        y += 22

        for (machine_type, recipe_name, ingredients, cost), rect in self.recipe_rects:
            unlocked = recipe_name in self.inventory.unlocked_recipes
            can_afford = self.economy.money >= cost
            
            tick = "v" if unlocked else " "
            ing_str = ", ".join(f"{v}x {k}" for k, v in ingredients.items())
            
            if unlocked:
                label = f"[{tick}] {recipe_name.upper()}  —  {ing_str}"
            else:
                label = f"[ ${cost} ] {recipe_name.upper()}  —  {ing_str}"
                
            self.frame.draw_button(screen, rect, label,
                                   active=unlocked,
                                   hovered=(self.hovered == recipe_name) and not unlocked and can_afford)