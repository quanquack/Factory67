from collections import deque
from registry import machine_registry, item_registry

class Position:
    """
    Component handling spatial data on the grid.

    Attributes
    ----------
    x : int or float
        The x-coordinate of the position.
    y : int or float
        The y-coordinate of the position.
    """
    def __init__(self, x, y):
        """
        Initializes the Position component.

        Parameters
        ----------
        x : int or float
            The x-coordinate.
        y : int or float
            The y-coordinate.
        """
        self.x = x
        self.y = y

    def get_coord(self):
        return (self.x, self.y)

    def get_adjacent(self):
        """
        Calculates the coordinates of all directly adjacent tiles.

        Returns
        -------
        dict
            A mapping of cardinal directions ('N', 'S', 'E', 'W') to (x, y) tuples.
        """
        return {
            "N": Position(self.x, self.y + 1),
            "E": Position(self.x + 1, self.y),
            "S": Position(self.x, self.y - 1),
            "W": Position(self.x - 1, self.y)
        }


class InventorySlot:
    """
    Represent a single storage slot within a container.

    Attributes
    ----------
    current_amount : int
        The current number of items in this slot.
    max_capacity : int
        The maximum number of items this slot can hold.
    """
    def __init__(self, max_capacity):
        """
        Initializes the InventorySlot.

        Parameters
        ----------
        max_capacity : int
            The maximum capacity for this specific slot.
        """
        self.current_amount = 0
        self.max_capacity = max_capacity


class InventoryComponent:
    """
    Component handling storage logic.

    Attributes
    ----------
    slots : dict
        A dictionary mapping item names to their respective InventorySlot.
    is_static : bool
        Determines whether the inventory slots are fixed or can be dynamically added.
    """
    def __init__(self):
        """Initializes an empty inventory component."""
        self.slots = {}
        self.is_static = False

    def add_item(self, item_name) -> bool:
        """
        Attempts to add an item to the inventory.

        Parameters
        ----------
        item_name : str
            The name of the item to add.

        Returns
        -------
        bool
            True if the item was successfully added, False if the inventory is full
            or cannot accept the item.
        """
        if item_name in self.slots:
            if self.slots[item_name].current_amount >= self.slots[item_name].max_capacity:
                return False
            self.slots[item_name].current_amount += 1
            return True
        if not self.is_static:
            self.slots[item_name] = InventorySlot(128)
            self.slots[item_name].current_amount = 1
            return True
        return False
    
    def remove_items(self, item_list: dict[str, int]) -> bool:
        """
        Attempts to remove a specific list of items from the inventory.

        Parameters
        ----------
        item_list : dict[str, int]
            A dictionary of item names and the quantities to remove.

        Returns
        -------
        bool
            True if all items were successfully removed, False if there were 
            insufficient items in the inventory.
        """
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
        """
        Configures static inventory slots with specific stack limits.

        Parameters
        ----------
        stack_limit : dict[str, int], optional
            A dictionary mapping item names to their maximum capacity.
        """
        self.slots.clear()
        self.is_static = True
        if stack_limit:
            for item in stack_limit:
                self.slots[item] = InventorySlot(stack_limit[item])


class RecipeManager:
    """
    Manages crafting recipes for machines.

    Attributes
    ----------
    recipes : dict
        A dictionary of recipes available for the machine type.
    cached_recipe : str or None
        The last successfully used recipe.
    selected_recipe : str or None
        A manually selected recipe to force the machine to craft.
    require_selection : bool
        If True, the machine requires a recipe to be manually selected.
    lookup_map : dict
        A mapping of input items to output items for quick lookup.
    """
    def __init__(self, machine_type: str, require_selection: bool):
        """
        Initializes the RecipeManager.

        Parameters
        ----------
        machine_type : str
            The type of machine requesting recipes.
        require_selection : bool
            Whether the machine strictly requires manual recipe selection.
        """
        self.recipes = machine_registry.get_recipes(machine_type)
        self.cached_recipe = None
        self.selected_recipe = None
        self.require_selection = require_selection

        self.lookup_map = {}
        if not self.require_selection:
            for output_item, ingredients in self.recipes.items():
                input_name = next(iter(ingredients.keys()))
                self.lookup_map[input_name] = output_item

    def set_recipe(self, recipe_name):
        """
        Manually sets a specific recipe for the machine.

        Parameters
        ----------
        recipe_name : str
            The name of the recipe to set.

        Returns
        -------
        bool
            True if the recipe is valid and set, False otherwise.
        """
        if recipe_name in self.recipes:
            self.selected_recipe = recipe_name
            self.cached_recipe = None
            return True
        return False

    def has_ingredients(self, required_items, inventory):
        """
        Checks if the inventory has the required ingredients for a recipe.

        Parameters
        ----------
        required_items : dict
            The required items and their quantities.
        inventory : InventoryComponent
            The inventory to check against.

        Returns
        -------
        bool
            True if all ingredients are present in sufficient quantities, False otherwise.
        """
        for item_name, amount in required_items.items():
            if item_name not in inventory.slots:
                return False
            if inventory.slots.get(item_name).current_amount < amount:
                return False
        return True

    def find_valid_recipe(self, inventory: InventoryComponent):
        """
        Finds a valid recipe based on the current inventory contents.

        Parameters
        ----------
        inventory : InventoryComponent
            The machine's input inventory.

        Returns
        -------
        str or None
            The name of the valid recipe if found, otherwise None.
        """
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


class InputComponent:
    """
    Component that handles incoming connections and items from other entities.

    Attributes
    ----------
    owner : object
        The parent object owning this component.
    sources : list
        A list of source objects connected to this input.
    max_sources : int or None
        The maximum number of sources allowed to connect.
    """
    def __init__(self, owner, max_sources=3):
        """
        Initializes the InputComponent.

        Parameters
        ----------
        owner : object
            The entity that owns this input.
        max_sources : int, optional
            The maximum number of input sources allowed.
        """
        self.owner = owner
        self.sources = []
        self.max_sources = max_sources

    def add(self, source):
        """
        Adds a new source to the input.

        Parameters
        ----------
        source : object
            The source object trying to connect.

        Returns
        -------
        bool
            True if the source was successfully added, False otherwise.
        """
        if source not in self.sources:
            if self.max_sources is not None and len(self.sources) >= self.max_sources:
                return False
            self.sources.append(source)
            return True
        return False

    def remove(self, source):
        """
        Removes a source from the input.

        Parameters
        ----------
        source : object
            The source object to remove.
        """
        if source in self.sources:
            self.sources.remove(source)

    def ping(self):
        """
        Pings all connected sources to notify them of an update or unjamming event.
        """
        for source in self.sources:
            source.is_jammed = False
            if hasattr(source, 'inventory_changed'):
                source.inventory_changed = True


class OutputComponent:
    """
    Component that handles outgoing connections to forward items to other entities.

    Attributes
    ----------
    owner : object
        The parent object owning this component.
    target : object or None
        The current target entity connected to this output.
    """
    def __init__(self, owner):
        """
        Initializes the OutputComponent.

        Parameters
        ----------
        owner : object
            The entity that owns this output.
        """
        self.owner = owner
        self.target = None

    def bind(self, target):
        """
        Binds this output to a target entity's input.

        Parameters
        ----------
        target : object
            The target entity to connect to.
        """
        self.target = target
        if hasattr(target, 'input'):
            target.input.add(self.owner)

    def unbind(self):
        """Unbinds this output from the current target entity."""
        if self.target and hasattr(self.target, 'input'):
            self.target.input.remove(self.owner)
            self.target = None


class ConnectionComponent:
    def __init__(self, owner):
        self.owner = owner

    def update_outbound(self, game_map):
        adj_pos = self.owner.position.get_adjacent()

        if hasattr(self.owner, "output_dir") and hasattr(self.owner, "output"):
            out_pos = adj_pos.get(self.owner.output_dir)
            if out_pos:
                target_block = game_map.get_block_at(*out_pos.get_coord())
                if target_block and hasattr(target_block, "input"):
                    self.owner.output.bind(target_block)
                else:
                    self.owner.output.unbind()

        if hasattr(self.owner, "output_dirs") and hasattr(self.owner, "outputs"):
            for i, out_dir in enumerate(self.owner.output_dirs):
                out_coord = adj_pos.get(out_dir)
                if out_coord:
                    target_block = game_map.get_block_at(*out_coord.get_coord())
                    if target_block and hasattr(target_block, "input"):
                        self.owner.bind_output(target_block, i)
                    else:
                        self.owner.bind_output(i)

    def _ping_adj(self, game_map):
        for direction, pos in self.owner.position.get_adjacent().items():
            neighbor = game_map.get_block_at(*pos.get_coord())
            if neighbor and hasattr(neighbor, "connection"):
                neighbor.connection.update_outbound(game_map)

    def on_place(self, game_map):
        self.update_outbound(game_map)
        self._ping_adj(game_map)

    def on_break(self, game_map):
        if hasattr(self.owner, "output"):
            self.owner.output.unbind()
            
        game_map.grid.pop(self.owner.position.get_coord(), None)
        self._ping_neighbors(game_map)


class Machine:
    """
    Base class for functional machines capable of processing items.

    Attributes
    ----------
    level : int
        The current upgrade level of the machine.
    base_speed : float
        The base speed at which the machine processes items.
    """
    def __init__(self, x_pos, y_pos, output_dir, machine_type):
        """
        Initializes the Machine.

        Parameters
        ----------
        x_pos : int or float
            The x-coordinate of the machine.
        y_pos : int or float
            The y-coordinate of the machine.
        machine_type : str
            The identifier type of the machine.
        """
        self.position = Position(x_pos, y_pos)
        self.output_dir = output_dir
        self.machine_type = machine_type
        self.level = 1

        metadata = machine_registry.get_metadata(machine_type)

        self.base_speed = metadata.get("base_speed", 120)
        is_strict = metadata.get("require_selection", False)

        self.recipe_manager = RecipeManager(machine_type, is_strict)
        self.input_inventory = InventoryComponent()
        self.output_inventory = InventoryComponent()

        self.output = OutputComponent(self)
        self.input = InputComponent(self)
        self.connection = ConnectionComponent(self)

        self.is_processing = False
        self.processing_timer = 0.0
        self.current_crafting_item = None
        self.inventory_changed = False
        self.is_jammed = False

    def _get_timer(self):
        return self.base_speed / (2 ** (self.level - 1))

    def accept_item(self, item_name: str) -> bool:
        """
        Receives an item from an external source and wakes up the machine.

        Parameters
        ----------
        item_name : str
            The name of the item being received.

        Returns
        -------
        bool
            True if the item was accepted, False if the input inventory is full.
        """
        flag = self.input_inventory.add_item(item_name)
        if flag:
            self.inventory_changed = True
        return flag

    def process_tick(self):
        """Processes a single tick of the machine's core logic."""
        if not self.is_jammed:
            if self.output.target and self.output_inventory.slots:
                item_to_push = next(iter(self.output_inventory.slots))
                if self.output.target.accept_item(item_to_push):
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
            self.processing_timer = self._get_timer()
            self.is_processing = True
            self.inventory_changed = True
            self.input.ping()
        else:
            self.inventory_changed = False

    def set_machine_recipe(self, recipe_name):
        """
        Sets a specific recipe for the machine and configures inventories.

        Parameters
        ----------
        recipe_name : str
            The name of the recipe to set.

        Returns
        -------
        bool
            True if the recipe was successfully set, False otherwise.
        """
        flag = self.recipe_manager.set_recipe(recipe_name)

        if flag:
            ingredients = self.recipe_manager.recipes[recipe_name]

            input_limit = {}

            for item_name, amount in ingredients.items():
                input_limit[item_name] = amount * 4

            self.input_inventory.configure_stack_limit(input_limit)
            self.output_inventory.configure_stack_limit({recipe_name: 100})

            self.is_processing = False
            self.current_crafting_item = None
            self.inventory_changed = True

        return flag

    def upgrade(self, player_inventory):
        """
        Upgrades the machine to the next level by deducting required items.

        Parameters
        ----------
        player_inventory : object
            The inventory of the player making the upgrade.

        Returns
        -------
        bool
            True if the machine was upgraded successfully, False otherwise.
        """
        if self.level >= 4:
            return False
        
        costs = machine_registry.get_metadata(self.machine_type).get("upgrade_costs", [])
        cost = costs[self.level - 1]
        
        flag = player_inventory.deduct_item(cost)
        
        if flag:
            self.level += 1

        return flag
    

class Miner:
    """
    Extracts raw resources from the environment and outputs them continuously.

    Attributes
    ----------
    target_ore : str
        The identifier of the raw material being generated.
    base_speed : float
        The base time in ticks required to mine a single unit.
    level : int
        The current upgrade level of the miner.
    """
    def __init__(self, x_pos, y_pos, ore, output_dir):
        """
        Initializes the Miner block.

        Parameters
        ----------
        x_pos : int or float
            The x-coordinate of the miner.
        y_pos : int or float
            The y-coordinate of the miner.
        ore : str
            The name of the item this miner produces.
        """
        self.position = Position(x_pos, y_pos)
        self.output_dir = output_dir
        self.ore = ore
        self.level = 1
        self.base_speed = machine_registry.get_metadata("miner").get("base_speed", 60)

        self.output = OutputComponent(self)
        self.connection = ConnectionComponent(self)

        self.processing_timer = self.base_speed
        self.is_jammed = False
    
    def _get_timer(self):
        return self.base_speed / (2 ** (self.level - 1))

    def process_tick(self):
        """Processes a single tick, generating and pushing the target ore."""
        if self.is_jammed:
            if self.output.target and self.output.target.accept_item(self.ore):
                self.is_jammed = False
                self.processing_timer = self._get_timer()
            return

        self.processing_timer -= 1
        
        if self.processing_timer <= 0:
            if self.output.target and self.output.target.accept_item(self.ore):
                self.processing_timer = self._get_timer()
            else:
                self.is_jammed = True

    def upgrade(self, player_inventory):
        """
        Upgrades the miner to significantly its generation speed.

        Parameters
        ----------
        player_inventory : object
            The player's main inventory to deduct upgrade costs from.

        Returns
        -------
        bool
            True if the upgrade was successful, False otherwise.
        """
        if self.level >= 4:
            return False
        
        metadata = machine_registry.get_metadata("miner")
        costs = metadata.get("upgrade_costs", [])
        
        if self.level - 1 < len(costs):
            cost = costs[self.level - 1]
            flag = player_inventory.deduct_item(cost)
            if flag:
                self.level += 1
            return flag
            
        return False

class TransportedItem:
    """
    Represents an item currently being transported on a conveyor.

    Attributes
    ----------
    item_name : str
        The name of the item.
    progress : float
        The progress of the item along the conveyor (between 0.0 and 1.0).
    """
    def __init__(self, item_name, progress=0.0):
        """
        Initializes the TransportedItem.

        Parameters
        ----------
        item_name : str
            The name of the item being transported.
        progress : float, optional
            The initial progress value.
        """
        self.item_name = item_name
        self.progress = progress


class Conveyor:
    """
    Transports items between different blocks on the map.

    Attributes
    ----------
    items : list
        A list of TransportedItem objects currently on the conveyor.
    speed : float
        The speed at which items move.
    spacing : float
        The minimum progress gap between consecutive items.
    """
    def __init__(self, x_pos, y_pos, input_dir, output_dir):
        """
        Initializes the Conveyor.

        Parameters
        ----------
        x_pos : int or float
            The x-coordinate of the conveyor.
        y_pos : int or float
            The y-coordinate of the conveyor.
        input_dir : str
            The direction from which items enter.
        output_dir : str
            The direction to which items are forwarded.
        """
        self.position = Position(x_pos, y_pos)
        self.input_dir = input_dir
        self.output_dir = output_dir

        self.items = []
        self.pending_items = []
        
        self.speed = 0.1
        self.spacing = 0.25
        self.input = InputComponent(self, max_sources=1)
        self.output = OutputComponent(self)
        self.connection = ConnectionComponent(self)

        self.is_jammed = False

    def accept_item(self, item_name: str) -> bool:
        """
        Accepts a new item onto the start of the conveyor.

        Parameters
        ----------
        item_name : str
            The name of the item to accept.

        Returns
        -------
        bool
            True if the item was accepted, False if there is not enough spacing.
        """
        last_item = None
        
        if self.pending_items:
            last_item = self.pending_items[-1]
        elif self.items:
            last_item = self.items[-1]

        if last_item and last_item.progress < self.spacing:
            return False
                
        new_item = TransportedItem(item_name, progress=0.0)
        self.pending_items.append(new_item)
        return True

    def process_tick(self):
        """Processes the movement of all items on the conveyor for a single tick."""
        if self.pending_items:
            self.items.extend(self.pending_items)
            self.pending_items.clear()

        if not self.items:
            self.is_jammed = False
            self.input.ping()
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
            if self.output.target and self.output.target.accept_item(front.item_name):
                self.items.pop(0)
                self.is_jammed = False
                self.input.ping()
            else:
                self.is_jammed = True
        

class Merger:
    """
    Merges items from multiple input sources into a single output stream.

    Attributes
    ----------
    buffer : deque
        A queue temporarily holding items before they are pushed out.
    """
    def __init__(self, x_pos, y_pos, output_dir, buffer_size=16):
        """
        Initializes the Merger.

        Parameters
        ----------
        x_pos : int or float
            The x-coordinate of the merger.
        y_pos : int or float
            The y-coordinate of the merger.
        buffer_size : int, optional
            The maximum number of items the merger can hold in its buffer.
        """
        self.position = Position(x_pos, y_pos)
        self.output_dir = output_dir

        self.input = InputComponent(self)
        self.output = OutputComponent(self)
        self.connection = ConnectionComponent(self)

        self.is_jammed = False
        self.buffer = deque(maxlen=buffer_size)
        self.pending_buffer = deque(maxlen=buffer_size)

    def accept_item(self, item_name: str) -> bool:
        """
        Accepts an item into the merger's buffer.

        Parameters
        ----------
        item_name : str
            The name of the incoming item.

        Returns
        -------
        bool
            True if accepted, False if the buffer is full.
        """
        if len(self.buffer) + len(self.pending_buffer) >= self.buffer.maxlen:
            return False
        self.buffer.append(item_name)
        if len(self.buffer) + len(self.pending_buffer) >= self.buffer.maxlen:
            for source in self.input.sources:
                source.is_jammed = True
        return True

    def process_tick(self):
        """Processes a single tick, pushing buffered items to the target output."""
        while self.pending_buffer:
            self.buffer.append(self.pending_buffer.popleft())

        if not self.buffer or not self.output.target:
            return

        if self.output.target.accept_item(self.buffer[0]):
            self.buffer.popleft()
            self.input.ping()
        else:
            self.is_jammed = True


class Router:
    """
    Distributes an incoming stream of items across multiple outputs based on weights.

    Attributes
    ----------
    buffer : deque
        A queue temporarily holding items before they are pushed out.
    outputs : list
        A list of OutputComponent instances for the split paths.
    weights : list of int
        Ratios dictating the distribution of items to each output.
    """
    def __init__(self, x_pos, y_pos, input_dir, mode="split", buffer_size=16):
        """
        Initializes the Splitter.

        Parameters
        ----------
        x_pos : int or float
            The x-coordinate of the splitter.
        y_pos : int or float
            The y-coordinate of the splitter.
        weights : list of int, optional
            Ratios determining the distribution weight per output.
        buffer_size : int, optional
            The maximum number of items the merger can hold in its buffer.
        """
        self.position = Position(x_pos, y_pos)
        self.mode = mode

        self.input = InputComponent(self, max_sources=1)
        self.outputs = [OutputComponent(self) for _ in range(3)]
        self.connection = ConnectionComponent(self)

        self.input_dir = input_dir
        self.output_dirs = [d for d in ["N", "E", "S", "W"] if d != self.input_dir]

        if self.mode == "split":
            self.config = [1, 1, 1]
            self.current_output = 0
            self.current_count = 0
        elif self.mode == "filter":
            self.config = [-1, -1, 0]

        self.is_jammed = False
        self.buffer = deque(maxlen=buffer_size)
        self.pending_buffer = deque(maxlen=buffer_size)


    def bind_output(self, target, slot: int):
        """
        Binds a specific output slot to a target.

        Parameters
        ----------
        target : object
            The target entity.
        slot : int
            The output slot index (0-2).
        """
        
        self.outputs[slot].bind(target)

    def unbind_output(self, slot: int):
        """
        Unbinds a specific output slot.

        Parameters
        ----------
        slot : int
            The output slot index (0-2).
        """
        self.outputs[slot].unbind()

    def accept_item(self, item_name: str) -> bool:
        """
        Accepts an item into the splitter's buffer.

        Parameters
        ----------
        item_name : str
            The name of the incoming item.

        Returns
        -------
        bool
            True if accepted, False if the buffer is full.
        """
        if len(self.buffer) + len(self.pending_buffer) >= self.buffer.maxlen:
            return False
        
        self.pending_buffer.append(item_name)
        return True
    
    def _get_split_slot(self):
        """
        Finds the next available valid output slot based on weights.

        Returns
        -------
        int or None
            The index of the next valid output slot, or None if none are available.
        """
        for i in range(3):
            slot = (self.current_output + i) % 3
            if self.config[slot] > 0 and self.outputs[slot].target:
                return slot
        return None
    
    def _get_filter_slot(self, item_name):
        """
        Finds the valid output slot based on item_name.

        Parameters
        ----------
        item_name : str
            The name of the outputting item.

        Returns
        -------
        int or None
            The index of the next valid output slot, or None if none are available.
        """
        if item_name in self.config:
            return self.config.index(item_name)
        return self.config.index(0)
    
    def set_config(self, config):
        if len(config) != 3:
            return False
        if self.mode == 'split':
            if sum(1 for i in config if i >= 0):
                self.config = config
                return True
            return False
        if self.mode == 'filter':
            if config.count(0) == 1:
                self.config = config
                return True
            return False

    def process_tick(self):
        """Processes a single tick, routing items to the valid outputs."""
        while self.pending_buffer:
            self.buffer.append(self.pending_buffer.popleft())
            
        if not self.buffer:
            self.is_jammed = False
            self.input.ping()
            return

        item_name = self.buffer[0]

        if self.mode == "split":
            slot = self._get_split_slot()
            if slot is None:
                return
        else:
            slot = self._get_filter_slot(item_name)

        out_component = self.outputs[slot]  

        if out_component.target and out_component.target.accept_item(item_name):
            self.buffer.popleft()

            if self.mode == "split":
                self.current_count += 1
                if self.current_count >= self.config[slot]:
                    self.current_count = 0
                    self.current_output = (self.current_output + 1) % 3

            self.is_jammed = False
            self.input.ping()
        else:
            self.is_jammed = True


class Seller:
    """
    Consumes items and adds corresponding funds to the player economy.

    Attributes
    ----------
    economy : Economy
        Reference to the global economy manager.
    input_buffer : list
        Temporarily stores incoming items before they are sold.
    """
    def __init__(self, x_pos, y_pos, economy_manager):
        """
        Initializes the Seller block.

        Parameters
        ----------
        x_pos : int or float
            The x-coordinate of the seller.
        y_pos : int or float
            The y-coordinate of the seller.
        economy_manager : Economy
            The economy manager handling player funds.
        """
        self.position = Position(x_pos, y_pos)
        self.economy = economy_manager
        self.input = InputComponent(self)
        self.connection = ConnectionComponent(self)
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
        """Sells all items in the buffer and clears it."""
        if not self.input_buffer:
            return

        total = 0
        for item in self.input_buffer:
            price = item_registry.get_price(item) 
            total += price

        self.economy.add_money(total)
        self.input_buffer.clear()


class CentralStorage:
    """
    Accepts items and places them directly into the player's main inventory.

    Attributes
    ----------
    inventory : object
        The main player inventory.
    input_buffer : list
        Temporarily stores incoming items before moving them to storage.
    """
    def __init__(self, x_pos, y_pos, player_inventory):
        """
        Initializes the CentralStorage.

        Parameters
        ----------
        x_pos : int or float
            The x-coordinate of the storage.
        y_pos : int or float
            The y-coordinate of the storage.
        player_inventory : object
            The player's main inventory to deposit items into.
        """
        self.position = Position(x_pos, y_pos)
        self.inventory = player_inventory
        self.input = InputComponent(self)
        self.connection = ConnectionComponent(self)
        self.input_buffer = []

    def accept_item(self, item_name):
        """
        Receives an item into the internal buffer for storage.

        Parameters
        ----------
        item_name : str
            The name of the item to be stored.

        Returns
        -------
        bool
            Always returns True as the storage component buffers dynamically.
        """
        self.input_buffer.append(item_name)
        return True

    def process_tick(self):
        """Deposits all items currently in the buffer into the player inventory."""
        if not self.input_buffer:
            return
        for item in self.input_buffer:
            self.inventory.add_item(item, 1)
        self.input_buffer.clear()