from registry import registry

class Position:
    """Component handling spatial data on the grid."""
    def __init__(self, x, y):
        self.x = x
        self.y = y


class InventorySlot:
    """
    Represents a single storage slot within a container.

    Attributes
    ----------
    current_amount : int
        The current number of items in this slot.
    max_capacity : int
        The maximum number of items this slot can hold.
    """
    def __init__(self, max_capacity):
        self.current_amount = 0
        self.max_capacity = max_capacity


class InventoryComponent:
    """
    Component handling storage logic.

    Attributes
    ----------
    slots : dict
        A dictionary mapping item names to their respective InventorySlot.
    stack_limit : dict[str, int]
        The default maximum capacity for each type of item.
    """
    def __init__(self):
        self.slots = {}
        self.is_static = False

    def add_item(self, item_name) -> bool:
        if item_name in self.slots:
            if self.slots[item_name].current_amount >= self.slots[item_name].max_capacity:
                return False
            self.slots[item_name].current_amount += 1
            return True
        if not self.is_static:
            self.slots[item_name] = InventorySlot(100)
            self.slots[item_name].current_amount = 1
            return True
        return False
    
    def remove_items(self, item_list: dict[str, int]) -> bool:
        for entry in item_list:
            if entry not in self.slots:
                return False
            if self.slots[entry].current_amount < item_list[entry]:
                return False
        
        for entry in item_list:
            self.slots[entry].current_amount -= item_list[entry]
            if self.slots[entry].current_amount == 0 and not self.is_static:
                self.slots.pop(entry)
            
        return True
    
    def configure_stack_limit(self, stack_limit: dict[str, int] = None):
        self.slots.clear()
        self.is_static = True
        for item in stack_limit:
            self.slots[item] = InventorySlot(stack_limit[item])

class RecipeManager:
    def __init__(self, machine_type: str, require_selection: bool):
        self.recipes = registry.get_recipes(machine_type)
        self.cached_recipe = None
        self.selected_recipe = None
        self.require_selection = require_selection

        self.lookup_map = {}
        if not self.require_selection:
            for output_item, ingredients in self.recipes.items():
                input_name = next(iter(ingredients.keys()))
                self.lookup_map[input_name] = output_item

    def set_recipe(self, recipe_name):
        if recipe_name in self.recipes:
            self.selected_recipe = recipe_name
            self.cached_recipe = None
            return True
        return False

    def has_ingredients(self, required_items, inventory):
        for item_name, amount in required_items.items():
            if item_name not in inventory.slots:
                return False
            if inventory.slots.get(item_name).current_amount < amount:
                return False
        return True

    def find_valid_recipe(self, inventory: InventoryComponent):
        if self.selected_recipe is not None:
            required_ingredients = self.recipes[self.selected_recipe]
            if self.has_ingredients(required_ingredients, inventory):
                return self.selected_recipe
            return None
        
        if self.require_selection:
            return None

        if self.cached_recipe is not None:
            required_ingredients = self.recipes[self.cached_recipe]
            if self.has_ingredients(required_ingredients, inventory):
                return self.cached_recipe
            else:
                self.cached_recipe = None

        if not inventory.slots:
            return None
        
        for item_name in inventory.slots:
            if item_name in self.lookup_map:
                output = self.lookup_map[item_name]
                required_items = self.recipes[output]

                if self.has_ingredients(required_items, inventory):
                    self.cached_recipe = output
                    return output

        return None


class Machine:
    """
    Base class for functional machines capable of processing items.

    Attributes
    ----------
    level : int
        The current upgrade level of the machine.
    processing_speed : float
        The base speed at which the machine processes items.
    """
    def __init__(self, x_pos, y_pos, machine_type):
        self.position = Position(x_pos, y_pos)
        self.machine_type = machine_type
        self.level = 1

        metadata = registry.get_metadata(machine_type)

        self.base_speed = metadata.get("base_speed", 120)
        is_strict = metadata.get("require_selection", False)

        self.recipe_manager = RecipeManager(machine_type, is_strict)
        self.input_inventory = InventoryComponent()
        self.output_inventory = InventoryComponent()

        self.output_target = None
        self.input_sources = []

        self.is_processing = False
        self.processing_timer = 0.0
        self.current_crafting_item = None
        self.inventory_changed = False
        self.is_jammed = False

    def bind_output(self, target):
        self.output_target = target
        if hasattr(target, 'input_sources'):
            target.input_sources.append(self)
        elif hasattr(target, 'input_source'):
            target.input_source = self

    def unbind_output(self):
        if hasattr(self.output_target, 'input_sources'):
            self.output_target.input_sources.remove(self)
        elif hasattr(self.output_target, 'input_source'):
            self.output_target.input_source = None

        self.output_target = None

    def ping_inputs(self):
        for input_src in self.input_sources:
            input_src.is_jammed = False
            if hasattr(input_src, 'inventory_changed'):
                input_src.inventory_changed = True

    def accept_item(self, item_name: str) -> bool:
        """
        Receives an item from an external source and wakes up the machine.
        """
        flag = self.input_inventory.add_item(item_name)
        if flag:
            self.inventory_changed = True
        return flag

    def process_tick(self):
        if not self.is_jammed:
            if self.output_target and self.output_inventory.slots:
                item_to_push = next(iter(self.output_inventory.slots))
                if self.output_target.accept_item(item_to_push):
                    self.output_inventory.remove_items({item_to_push: 1})
                else:
                    self.is_jammed = True

        if self.is_processing:
            self.processing_timer -= 1
            if self.processing_timer <= 0:
                flag = self.output_inventory.add_item(self.current_crafting_item)
                if flag:
                    self.is_processing = False
                    self.current_crafting_item = None
                    self.inventory_changed = True
                    self.is_jammed = False
            return
        
        if not self.inventory_changed:
            return
        
        recipe = self.recipe_manager.find_valid_recipe(self.input_inventory)

        if recipe is not None:
            ingredients = self.recipe_manager.recipes[recipe]
            self.input_inventory.remove_items(ingredients)

            self.current_crafting_item = recipe
            #Implement speed change here based on level (prolly base_speed / (2 ** level))
            self.processing_timer = self.base_speed / (2 ** (self.level - 1))
            self.is_processing = True
            self.inventory_changed = True
            self.ping_inputs()
        else:
            self.inventory_changed = False

    def set_machine_recipe(self, recipe_name):
        flag = self.recipe_manager.set_recipe(recipe_name)

        if flag:
            ingredients = self.recipe_manager.recipes[recipe_name]

            input_limit = {}

            for item_name, amount in ingredients.items():
                input_limit[item_name] = amount * 5

            self.input_inventory.configure_stack_limit(input_limit)
            self.output_inventory.configure_stack_limit({recipe_name: 100})

            self.is_processing = False
            self.current_crafting_item = None
            self.inventory_changed = True

        return flag


    def upgrade(self, player_inventory):
        #Deduct item in player_inventory here
        if self.level >= 4:
            return
        self.level += 1


class TransportedItem:
    def __init__(self, item_name, progress = 0.0):
        self.item_name = item_name
        self.progress = progress


class Conveyor:
    """
    Transport items between different blocks on the map.
    """
    def __init__(self, x_pos, y_pos, input_dir, output_dir):
        self.position = Position(x_pos, y_pos)
        self.input_dir = input_dir
        self.output_dir = output_dir

        self.items = []
        
        self.speed = 0.1
        self.spacing = 0.25
        self.input_source = None
        self.output_target = None
        self.is_jammed = False

    def bind_output(self, target):
        self.output_target = target
        if hasattr(target, 'input_sources'):
            target.input_sources.append(self)
        elif hasattr(target, 'input_source'):
            target.input_source = self

    def unbind_output(self):
        if hasattr(self.output_target, 'input_sources'):
            self.output_target.input_sources.remove(self)
        elif hasattr(self.output_target, 'input_source'):
            self.output_target.input_source = None

        self.output_target = None

    def ping_input(self):
        if self.input_source:
            self.input_source.is_jammed = False
            if hasattr(self.input_source, 'inventory_changed'):
                self.input_source.inventory_changed = True

    def accept_item(self, item_name: str) -> bool:
        if self.items:
            last_item = self.items[-1]
            if last_item.progress < self.spacing:
                return False
                
        new_item = TransportedItem(item_name, progress=0.0)
        self.items.append(new_item)
        return True

    def process_tick(self):
        if not self.items:
            self.is_jammed = False
            self.ping_input()
            return

        for i, item in enumerate(self.items):
            if i == 0:
                cap = 1.0
            else:
                cap = self.items[i - 1].progress - self.spacing

            if item.progress < cap:
                item.progress = min(item.progress + self.speed, cap)

        front = self.items[0]
        if front.progress >= 1.0:
            if self.output_target and self.output_target.accept_item(front.item_name):
                self.items.pop(0)
                self.is_jammed = False
                self.ping_input()
            else:
                self.is_jammed = True
        

class Seller:
    """
    Consumes items and adds corresponding funds to the player economy.

    Attributes
    ----------
    economy : Economy
        Reference to the global economy manager.
    prices : dict
        Catalog mapping item names to their respective prices.
    input_buffer : list
        Temporarily stores incoming items before they are sold.
    """
    def __init__(self, x_pos, y_pos, economy_manager, price_catalog):
        self.position = Position(x_pos, y_pos)
        self.economy = economy_manager
        self.prices = price_catalog
        self.input_buffer = []

    def accept_item(self, item_name):
        """
        Receives an item into the internal buffer for sale.

        Parameters
        ----------
        item_name : str
            The name of the item to be sold.

        Returns
        -------
        bool
            Always returns True as the seller has no capacity limit.
        """
        self.input_buffer.append(item_name)
        return True

    def process_tick(self):
        """
        Sells all items in the buffer and clears it.
        """
        if not self.input_buffer:
            return

        total = 0
        for item in self.input_buffer:
            price = self.prices.get(item, 0) 
            total += price

        self.economy.add_money(total)
        self.input_buffer.clear()