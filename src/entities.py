from recipes import recipe_registry

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
    def __init__(self, stack_limit: dict[str, int] = None):
        self.slots = {}
        self.is_static = False
        if stack_limit is not None:
            self.is_static = True
            for item in stack_limit:
                self.slots[item] = InventorySlot(stack_limit[item])

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

class RecipeManager:
    def __init__(self, machine_type: str, require_selection: bool):
        self.recipes = recipe_registry.get_recipes_for(machine_type)
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
    def __init__(self, x_pos, y_pos, base_speed):
        self.position = Position(x_pos, y_pos)
        self.level = 1
        self.processing_speed = base_speed

    def process_tick(self):
        raise NotImplementedError

    def upgrade(self, player_inventory):
        """
        Handles the logic for leveling up the machine.

        Parameters
        ----------
        player_inventory : Inventory
            The global inventory holding upgrade items.

        Raises
        ------
        NotImplementedError
            If the child class does not implement the upgrade logic.
        """
        raise NotImplementedError

class Conveyor:
    """
    Transports items between different blocks on the map.

    Attributes
    ----------
    direction : str
        The direction the conveyor is moving items (e.g., 'UP', 'DOWN').
    carrying_item : str or None
        The item currently being transported.
    """
    def __init__(self, x_pos, y_pos, direction):
        self.position = Position(x_pos, y_pos)
        self.direction = direction
        self.carrying_item = None

    def process_tick(self):
        """
        Moves the carried item to the next grid cell based on direction.
        """
        pass

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