import pygame
from src.registry import item_registry, machine_registry, theme_registry


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
            filepath = f"assets/{self.item_name}.png"
            try:
                surf = asset_manager.get_asset(self.item_name, filepath)
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


class MachineWindow:
    def __init__(self, screen_w, screen_h, game_manager):
        self.frame = WindowFrame(screen_w, screen_h, 630, 720, "MACHINE STATUS")
        self.game_manager = game_manager
        self.player_inventory = game_manager.inventory
        self.machine = None
        self.upgrade_rect = None
        self.recipe_rects = []
        self.hovered_recipe = None
        self.hovered_upgrade = False
        self.upgrade_slots = []

    @property
    def is_open(self):
        return self.frame.is_open

    def open(self, machine):
        self.machine = machine
        name = machine.get_asset_name()
        self.frame.title = f"{name.upper()} MENU"
        self.frame.open()
        self._init_upgrade_slots()
        self._build_rects()

    def close(self):
        self.frame.close()

    def _init_upgrade_slots(self):
        """Pre-calculate and instantiate ItemSlot components for the upgrade cost."""
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
        self.recipe_rects = []
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
            m_type = self.machine.get_asset_name()
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
            
        for slot in self.upgrade_slots:
            slot.handle_event(event)
            
        if event.type == pygame.MOUSEMOTION:
            self.hovered_upgrade = self.upgrade_rect is not None and self.upgrade_rect.collidepoint(event.pos)
            self.hovered_recipe = None
            for recipe, rect in self.recipe_rects:
                if rect.collidepoint(event.pos):
                    self.hovered_recipe = recipe
                    
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
                
            for recipe, rect in self.recipe_rects:
                if rect.collidepoint(event.pos):
                    self.machine.set_machine_recipe(recipe)
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
            
            # Bind data to the upgrade slots
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
                    if name:
                        hovered_name_for_tooltip = name
                else:
                    slot.set_data(None)
                    slot.draw(screen, asset_manager, self.frame.font, self.frame.font_small)

            y += 64 + 15
            
            self.upgrade_rect = pygame.Rect(x, y, self.frame.width - self.frame.PADDING * 2, self.frame.BTN_H)
            self.frame.draw_button(screen, self.upgrade_rect, "UPGRADE (SHIFT to mass upgrade)",
                                   active=can_afford,
                                   hovered=self.hovered_upgrade and can_afford)
            y += self.frame.BTN_H + 15

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

        # Delegate tooltip drawing to the main frame at the very end
        if hovered_name_for_tooltip:
            self.frame.draw_tooltip(screen, hovered_name_for_tooltip)


class StorageWindow:
    def __init__(self, screen_w, screen_h):
        self.frame = WindowFrame(screen_w, screen_h, 600, 700, "STORAGE")
        self.storage = None
        self.scroll = 0
        self.slots = []
        self.cols = 0
        self._init_slots()

    def _init_slots(self):
        slot_size = 64
        gap = 10
        x_start = self.frame.x + self.frame.PADDING
        y_start = self.frame.y + self.frame.HEADER_H + self.frame.PADDING + 50 
        
        self.cols = (self.frame.width - self.frame.PADDING * 2) // (slot_size + gap)
        rows = (self.frame.height - self.frame.HEADER_H - self.frame.PADDING * 2 - 50) // (slot_size + gap)
        
        for row in range(rows):
            for col in range(self.cols):
                slot_x = x_start + col * (slot_size + gap)
                slot_y = y_start + row * (slot_size + gap)
                self.slots.append(ItemSlot(slot_x, slot_y, slot_size))

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
            
        for slot in self.slots:
            slot.handle_event(event)
            
        if event.type == pygame.MOUSEWHEEL:
            items = list(self.storage.inventory.inventory.items())
            max_rows = max(0, (len(items) + self.cols - 1) // self.cols - 1)
            self.scroll = max(0, min(self.scroll - event.y, max_rows))
            
        return False

    def draw(self, screen, asset_manager=None):
        self.frame.draw_frame(screen)
        x_start = self.frame.x + self.frame.PADDING
        y_start = self.frame.y + self.frame.HEADER_H + self.frame.PADDING

        items = list(self.storage.inventory.inventory.items())
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

        if hovered_name_for_tooltip:
            self.frame.draw_tooltip(screen, hovered_name_for_tooltip)


class RouterConfigWindow:
    def __init__(self, screen_w, screen_h):
        self.frame = WindowFrame(screen_w, screen_h, 600, 510, "ROUTER CONFIG")
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
        self.direction_text = {'N': '↑', 'S': '↓', 'E': '→', 'W': '←'}

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


class RecipeUnlockWindow:
    def __init__(self, screen_w, screen_h, economy):
        self.frame = WindowFrame(screen_w, screen_h, 660, 630, "UNLOCK RECIPES")
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

    def draw(self, screen, asset_manager=None):
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
            

class VictoryWindow:
    def __init__(self, screen_w, screen_h):
        self.frame = WindowFrame(screen_w, screen_h, 720, 420, "VICTORY!")
        self.continue_rect = None
        self.hovered = False

    @property
    def is_open(self):
        return self.frame.is_open

    def open(self):
        self.frame.open()

    def close(self):
        self.frame.close()

    def handle_event(self, event):
        if self.frame.handle_close_click(event):
            return True
            
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.continue_rect is not None and self.continue_rect.collidepoint(event.pos)
            
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.continue_rect and self.continue_rect.collidepoint(event.pos):
                self.close()
                return True
        return False

    def draw(self, screen, asset_manager=None):
        self.frame.draw_frame(screen)
        x = self.frame.x + self.frame.PADDING
        y = self.frame.y + self.frame.HEADER_H + self.frame.PADDING + 10

        text_lines = [
            "CONGRATULATIONS, ENGINEER!",
            "",
            "You have successfully automated the production",
            "and achived the rate of 10 robots produced per second.",
            "Your factory is a masterpiece of logistics.",
            "",
            "You can stop now, or continue expanding your factory."
        ]
        
        for line in text_lines:
            if line.startswith("CONGRATULATIONS"):
                surf = self.frame.font_title.render(line, True, (255, 215, 0))
                screen.blit(surf, (self.frame.x + (self.frame.width - surf.get_width()) // 2, y))
                y += 28
            else:
                surf = self.frame.font.render(line, True, theme_registry.get_color("windows","text"))
                screen.blit(surf, (self.frame.x + (self.frame.width - surf.get_width()) // 2, y))
                y += 20

        y += 15
        btn_w = 200
        self.continue_rect = pygame.Rect(self.frame.x + (self.frame.width - btn_w) // 2, y, btn_w, self.frame.BTN_H)
        self.frame.draw_button(screen, self.continue_rect, "CONTINUE PLAYING", active=False, hovered=self.hovered)


class StatisticsWindow:
    def __init__(self, screen_w, screen_h, game_manager):
        self.frame = WindowFrame(screen_w, screen_h, 570, 750, "FACTORY STATISTICS")
        self.game_manager = game_manager
        self.scroll = 0
        self.slots = []
        self.cols = 0
        self._init_slots()

    def _init_slots(self):
        slot_size = 64
        gap = 10
        x_start = self.frame.x + self.frame.PADDING
        
        text_area_offset = 70
        y_start = self.frame.y + self.frame.HEADER_H + self.frame.PADDING + text_area_offset
        
        self.cols = (self.frame.width - self.frame.PADDING * 2) // (slot_size + gap)
        rows = (self.frame.height - self.frame.HEADER_H - self.frame.PADDING * 2 - text_area_offset) // (slot_size + gap)
        
        for row in range(rows):
            for col in range(self.cols):
                slot_x = x_start + col * (slot_size + gap)
                slot_y = y_start + row * (slot_size + gap)
                self.slots.append(ItemSlot(slot_x, slot_y, slot_size))

    @property
    def is_open(self):
        return self.frame.is_open

    def open(self):
        self.scroll = 0
        self.frame.open()

    def close(self):
        self.frame.close()

    def handle_event(self, event):
        if self.frame.handle_close_click(event):
            return True
            
        for slot in self.slots:
            slot.handle_event(event)
            
        if event.type == pygame.MOUSEWHEEL:
            self.scroll = max(0, min(self.scroll - event.y, 50)) 
            return True
            
        return False
    
    def draw(self, screen, asset_manager=None):
        self.frame.draw_frame(screen)
        x_start = self.frame.x + self.frame.PADDING
        y_start = self.frame.y + self.frame.HEADER_H + self.frame.PADDING

        money_rate = getattr(self.game_manager.economy, 'money_rate', 0.0)
        self.frame.draw_label(screen, f"Income Rate: ${money_rate:.1f} / sec", x_start, y_start)
        y_start += 30
        
        from src.registry import theme_registry
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

        if hovered_name_for_tooltip:
            self.frame.draw_tooltip(screen, hovered_name_for_tooltip)