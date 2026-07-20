from collections import deque
from dataclasses import dataclass, field
from src.registry import machine_registry, item_registry

@dataclass
class BuildContext:
    """
    Typed context object passed to block `build()` classmethods.

    Carries all game-level services a block may need during construction.
    Blocks extract only what they need and do not store this object.

    Attributes
    ----------
    tool : str
        The tool/block type being placed.
    out_dir : str
        The cardinal direction of the output port.
    in_dir : str
        The cardinal direction of the input port.
    game_map : object, optional
        The game map, needed by blocks that query tile data on placement.
    economy : object, optional
        The economy manager, needed by terminal selling blocks.
    inventory : object, optional
        The player inventory, needed by storage blocks.
    """
    tool: str
    out_dir: str = ""
    in_dir: str = ""
    game_map: object = field(default=None, repr=False)
    economy: object = field(default=None, repr=False)
    inventory: object = field(default=None, repr=False)
    game_manager: object = field(default=None, repr=False)


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
            "N": Position(self.x, self.y - 1),
            "E": Position(self.x + 1, self.y),
            "S": Position(self.x, self.y + 1),
            "W": Position(self.x - 1, self.y)
        }
    
    def get_opposite(self, direction):
        opposite = {
            "N": "S",
            "S": "N",
            "W": "E",
            "E": "W"
        }
        return opposite.get(direction, "")


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
    def __init__(self, recipes, require_selection: bool):
        """
        Initializes the RecipeManager.

        Parameters
        ----------
        machine_type : str
            The type of machine requesting recipes.
        require_selection : bool
            Whether the machine strictly requires manual recipe selection.
        """
        self.recipes = recipes
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

    def try_push(self, item_name):
        if self.target:
            return self.target.accept_item(item_name)
        return False


class ConnectionComponent:
    def __init__(self, owner):
        self.owner = owner

    def update_outbound(self, game_map):
        adj_pos = self.owner.position.get_adjacent()

        outbound_ports = self.owner.get_outbound_ports()

        for output_dir, output_component in outbound_ports.items():
            target_pos = adj_pos.get(output_dir)
            target_block = game_map.get_block_at(*target_pos.get_coord()) if target_pos else None

            if target_block:
                opposite_dir = self.owner.position.get_opposite(output_dir)
                in_comp = target_block.get_inbound_port(opposite_dir)
                if in_comp:
                    output_component.bind(target_block)
                    continue
            
            output_component.unbind()

    def _ping_adj(self, game_map):
        for direction, pos in self.owner.position.get_adjacent().items():
            neighbor = game_map.get_block_at(*pos.get_coord())
            if neighbor and hasattr(neighbor, "connection"):
                neighbor.connection.update_outbound(game_map)

    def on_place(self, game_map):
        self.update_outbound(game_map)
        self._ping_adj(game_map)

    def on_break(self, game_map):
        for out_comp in self.owner.get_outbound_ports().values():
            out_comp.unbind()
        self._ping_adj(game_map)


class UpgradeComponent:
    """
    Component handling level, speed, and upgrade logic for upgradable entities.

    Attributes
    ----------
    level : int
        The current upgrade level.
    base_speed : float
        The base processing duration in ticks at level 1.
    registry_key : str
        The registry key used to look up upgrade costs and metadata.
    """
    def __init__(self, registry_key: str):
        """
        Initializes the UpgradeComponent, loading speed from registry metadata.

        Parameters
        ----------
        registry_key : str
            The registry key of the owning entity type.
        """
        metadata = machine_registry.get_metadata(registry_key)
        self.level = 1
        self.base_speed = metadata.get("base_speed", 120)
        self.registry_key = registry_key

    def get_timer(self) -> float:
        """Returns the current processing duration in ticks based on upgrade level."""
        return self.base_speed / (2 ** (self.level - 1))

    def process_upgrade(self, player_inventory) -> bool:
        metadata = machine_registry.get_metadata(self.registry_key)
        costs = metadata.get("upgrade_costs", [])
        max_level = len(costs) + 1

        if self.level >= max_level:
            return False

        cost = costs[self.level - 1]
        if player_inventory.deduct_item(cost):
            self.level += 1
            return True

        return False


class BufferComponent:
    """
    Component managing a double-buffered item queue for routing blocks.

    Separates incoming items (pending) from items ready to be processed
    (live buffer), preventing mid-tick mutations from affecting the
    current tick's processing.

    Attributes
    ----------
    buffer : deque
        The live queue of items ready to be pushed downstream.
    pending : deque
        Items accepted this tick, waiting to be flushed into the live queue.
    """
    def __init__(self, maxlen: int = 16):
        """
        Initializes the BufferComponent.

        Parameters
        ----------
        maxlen : int, optional
            The maximum combined capacity of buffer and pending.
        """
        self.buffer = deque(maxlen=maxlen)
        self.pending = deque(maxlen=maxlen)

    @property
    def is_full(self) -> bool:
        """True if the combined live and pending queues are at capacity."""
        return len(self.buffer) + len(self.pending) >= self.buffer.maxlen

    def accept(self, item_name: str) -> bool:
        """
        Accepts an item into the pending queue.

        Parameters
        ----------
        item_name : str
            The name of the item to accept.

        Returns
        -------
        bool
            True if accepted, False if at capacity.
        """
        if self.is_full:
            return False
        self.pending.append(item_name)
        return True

    def flush_pending(self):
        """Moves all pending items into the live buffer. Call at the start of each tick."""
        while self.pending:
            self.buffer.append(self.pending.popleft())

    def peek(self) -> str | None:
        """Returns the front item without removing it, or None if the buffer is empty."""
        return self.buffer[0] if self.buffer else None

    def pop(self) -> str | None:
        """Removes and returns the front item, or None if the buffer is empty."""
        return self.buffer.popleft() if self.buffer else None

    def __bool__(self) -> bool:
        return bool(self.buffer) or bool(self.pending)

    def __len__(self) -> int:
        return len(self.buffer) + len(self.pending)


class SinkComponent:
    """
    Component that buffers incoming items for batch processing each tick.

    Intended for terminal blocks (e.g., sellers, storage) that consume
    items rather than forwarding them downstream.

    Attributes
    ----------
    _buffer : list
        Internal list of item names waiting to be processed.
    """
    def __init__(self):
        """Initializes an empty SinkComponent."""
        self._buffer = []

    def accept(self, item_name: str) -> bool:
        """
        Accepts an item into the buffer. Always succeeds.

        Parameters
        ----------
        item_name : str
            The name of the item to buffer.

        Returns
        -------
        bool
            Always True.
        """
        self._buffer.append(item_name)
        return True

    def drain(self) -> list:
        """
        Returns all buffered items and clears the buffer.

        Returns
        -------
        list
            All item names that were buffered since the last drain.
        """
        items = list(self._buffer)
        self._buffer.clear()
        return items

    def __bool__(self) -> bool:
        return bool(self._buffer)
    

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
