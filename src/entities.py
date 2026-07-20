from abc import ABC, abstractmethod
from src.registry import machine_registry, item_registry
from src.components import (
    Position, InventoryComponent, RecipeManager,
    InputComponent, OutputComponent, ConnectionComponent,
    UpgradeComponent, BufferComponent, SinkComponent,
    TransportedItem, BuildContext
)

def spawn_entity(tool, x, y, context):
    block_class = machine_registry.get_class(tool, default=Machine)
    
    return block_class.build(x, y, context)


class BaseBlock(ABC):
    @property
    def removable(self):
        metadata = machine_registry.get_metadata(self.get_asset_name())
        return metadata.get("removable", True)

    @abstractmethod
    def process_tick(self): ...

    @abstractmethod
    def get_outbound_ports(self) -> dict: ...

    @abstractmethod
    def get_inbound_port(self, direction: str): ...

    @abstractmethod
    def to_dict(self) -> dict: ...

    @classmethod
    @abstractmethod
    def from_dict(cls, data, **kwargs): ...

    @abstractmethod
    def get_asset_name(self) -> str: ...

    @classmethod
    @abstractmethod
    def build(cls, x, y, ctx: BuildContext): ...


class Machine(BaseBlock):
    """
    Base class for functional machines capable of processing items.
    """
    def __init__(self, x_pos, y_pos, output_dir, machine_type,
                 input_component=None, output_component=None, 
                 input_inv=None, output_inv=None):
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
        self.upgrade_comp = UpgradeComponent(machine_type)

        metadata = machine_registry.get_metadata(machine_type)
        is_strict = metadata.get("require_selection", False)

        self.recipe_manager = RecipeManager(machine_registry.get_recipes(machine_type), is_strict)
        self.input_inventory = InventoryComponent() if input_inv is None else input_inv
        self.output_inventory = InventoryComponent() if output_inv is None else output_inv

        self.output = OutputComponent(self) if output_component is None else output_component
        self.input = InputComponent(self) if input_component is None else input_component
        self.output.owner = self
        self.input.owner = self
        self.connection = ConnectionComponent(self)

        self.is_processing = False
        self.processing_timer = 0.0
        self.current_crafting_item = None
        self.inventory_changed = False
        self.is_jammed = False

    @property
    def level(self):
        return self.upgrade_comp.level

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
            item_to_push = None
            
            for item_name, slot in self.output_inventory.slots.items():
                if slot.current_amount > 0:
                    item_to_push = item_name
                    break
            
            if item_to_push:
                if self.output.try_push(item_to_push):
                    self.output_inventory.remove_items({item_to_push: 1})
                    self.is_jammed = False
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
            self.processing_timer = self.upgrade_comp.get_timer()
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
        return self.upgrade_comp.process_upgrade(player_inventory)
    
    def get_outbound_ports(self):
        return {self.output_dir: self.output}
    
    def get_inbound_port(self, direction):
        if direction != self.output_dir:
            return self.input
        return None
    
    def to_dict(self):
        return {
            "class_name": "Machine",
            "type": self.machine_type,
            "x": self.position.x,
            "y": self.position.y,
            "recipe": self.recipe_manager.selected_recipe,
            "output_dir": self.output_dir,
            "level": self.upgrade_comp.level
        }
    
    @classmethod
    def from_dict(cls, data, **kwargs):
        new_block = cls(
            x_pos=data["x"],
            y_pos=data["y"],
            output_dir=data["output_dir"],
            machine_type=data["type"]
        )

        new_block.upgrade_comp.level = data.get("level", 1)
        if data.get("recipe"):
            new_block.set_machine_recipe(data.get("recipe"))

        return new_block
    
    def get_asset_name(self):
        return self.machine_type
    
    @classmethod
    def build(cls, x, y, ctx: BuildContext):
        return cls(x_pos=x, y_pos=y, output_dir=ctx.out_dir, machine_type=ctx.tool)
    

class Miner(BaseBlock):
    """
    Extracts raw resources from the environment and outputs them continuously.

    Attributes
    ----------
    ore : str
        The identifier of the raw material being generated.
    """
    def __init__(self, x_pos, y_pos, ore, output_dir,
                 output_component=None):
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
        self.upgrade_comp = UpgradeComponent("miner")

        self.output = OutputComponent(self) if output_component is None else output_component
        self.output.owner = self
        self.connection = ConnectionComponent(self)

        self.processing_timer = self.upgrade_comp.base_speed
        self.is_jammed = False
    
    @property
    def level(self):
        return self.upgrade_comp.level

    def process_tick(self):
        """Processes a single tick, generating and pushing the target ore."""
        if self.is_jammed:
            if self.output.try_push(self.ore):
                self.processing_timer = self.upgrade_comp.get_timer()
                self.is_jammed = False
            return

        self.processing_timer -= 1
        
        if self.processing_timer <= 0:
            if self.output.try_push(self.ore):
                self.processing_timer = self.upgrade_comp.get_timer()
            else:
                self.is_jammed = True
            return

    def upgrade(self, player_inventory):
        return self.upgrade_comp.process_upgrade(player_inventory)

    def get_outbound_ports(self):
        return {self.output_dir: self.output}
    
    def get_inbound_port(self, direction):
        return None
    
    def to_dict(self):
        return {
            "class_name": "Miner",
            "x": self.position.x,
            "y": self.position.y,
            "output_dir": self.output_dir,
            "level": self.upgrade_comp.level
        }
    
    @classmethod
    def from_dict(cls, data, **kwargs):
        game_map = kwargs.get("game_map")

        target_ore = "copper"
        if game_map:
            target_ore = game_map.get_ore_at(data["x"], data["y"])

        new_block = cls(
            x_pos=data["x"],
            y_pos=data["y"],
            ore=target_ore,
            output_dir=data["output_dir"]
        )
        new_block.upgrade_comp.level = data.get("level", 1)
        return new_block
    
    def get_asset_name(self):
        return "miner"

    @classmethod
    def build(cls, x, y, ctx: BuildContext):
        ore = ctx.game_map.get_ore_at(x, y)
        if not ore: 
            return None
        return cls(x_pos=x, y_pos=y, ore=ore, output_dir=ctx.out_dir)
    

class Conveyor(BaseBlock):
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
    def __init__(self, x_pos, y_pos, input_dir, output_dir,
                 input_component=None, output_component=None):
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
        self.spacing = 0.5
        self.output = OutputComponent(self) if output_component is None else output_component
        self.input = InputComponent(self, max_sources=1) if input_component is None else input_component
        self.output.owner = self
        self.input.owner = self
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
        
        front_cap = 1.0

        if self.output.target and isinstance(self.output.target, Conveyor):
            target_conv = self.output.target
            last_item = None
            
            if target_conv.pending_items:
                last_item = target_conv.pending_items[-1]
            elif target_conv.items:
                last_item = target_conv.items[-1]
                
            if last_item:
                dynamic_cap = last_item.progress + 1.0 - self.spacing
                front_cap = min(1.0, dynamic_cap)

        for i, item in enumerate(self.items):
            if i == 0:
                cap = front_cap
            else:
                cap = self.items[i - 1].progress - self.spacing

            if item.progress < cap:
                item.progress = min(item.progress + self.speed, cap)

        front = self.items[0]
        if front.progress >= 1.0:
            if self.output.try_push(front.item_name):
                self.items.pop(0)
                self.input.ping()
                self.is_jammed = False
            else:
                self.is_jammed = True
        else:
            self.is_jammed = (front_cap < 1.0 and front.progress >= front_cap)

    def get_outbound_ports(self):
        return {self.output_dir: self.output}
    
    def get_inbound_port(self, direction):
        if direction == self.input_dir:
            return self.input
        return None
    
    def to_dict(self):
        return {
            "class_name": "Conveyor",
            "x": self.position.x,
            "y": self.position.y,
            "input_dir": self.input_dir,
            "output_dir": self.output_dir
        }
    
    @classmethod
    def from_dict(cls, data, **kwargs):
        new_block = cls(
            x_pos=data["x"],
            y_pos=data["y"],
            input_dir=data["input_dir"],
            output_dir=data["output_dir"]
        )

        return new_block
    
    def get_asset_name(self):
        return f"conveyor_{self.input_dir}_{self.output_dir}"
    
    @classmethod
    def build(cls, x, y, ctx: BuildContext):
        return cls(x_pos=x, y_pos=y, input_dir=ctx.in_dir, output_dir=ctx.out_dir)
        

class Merger(BaseBlock):
    """
    Merges items from multiple input sources into a single output stream.

    Attributes
    ----------
    buffer_comp : BufferComponent
        Manages the double-buffered item queue.
    """
    def __init__(self, x_pos, y_pos, output_dir, buffer_size=16, 
                 input_component=None, output_component=None):
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

        self.output = OutputComponent(self) if output_component is None else output_component
        self.input = InputComponent(self) if input_component is None else input_component
        self.output.owner = self
        self.input.owner = self
        self.connection = ConnectionComponent(self)

        self.is_jammed = False
        self.buffer_comp = BufferComponent(maxlen=buffer_size)

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
        accepted = self.buffer_comp.accept(item_name)
        if not accepted:
            return False
        if self.buffer_comp.is_full:
            for source in self.input.sources:
                source.is_jammed = True
        return True

    def process_tick(self):
        """Processes a single tick, pushing buffered items to the target output."""
        self.buffer_comp.flush_pending()

        if not self.buffer_comp.buffer or not self.output.target:
            return

        if self.output.try_push(self.buffer_comp.peek()):
            self.buffer_comp.pop()
            self.input.ping()
            self.is_jammed = False
        else:
            self.is_jammed = True
        
    def get_outbound_ports(self):
        return {self.output_dir: self.output}
    
    def get_inbound_port(self, direction):
        if direction != self.output_dir:
            return self.input
        return None
    
    def to_dict(self):
        return {
            "class_name": "Merger",
            "x": self.position.x,
            "y": self.position.y,
            "output_dir": self.output_dir
        }
    
    @classmethod
    def from_dict(cls, data, **kwargs):
        new_block = cls(
            x_pos=data["x"],
            y_pos=data["y"],
            output_dir=data["output_dir"]
        )

        return new_block
    
    def get_asset_name(self):
        return "merger"
    
    @classmethod
    def build(cls, x, y, ctx: BuildContext):
        return cls(x_pos=x, y_pos=y, output_dir=ctx.out_dir)


class Router(BaseBlock):
    """
    Distributes an incoming stream of items across multiple outputs based on weights.

    Attributes
    ----------
    buffer_comp : BufferComponent
        Manages the double-buffered item queue.
    outputs : list
        A list of OutputComponent instances for the split paths.
    """
    def __init__(self, x_pos, y_pos, input_dir, mode="split", buffer_size=16,
                 input_component=None, output_component=None):
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

        self.outputs = [OutputComponent(self) for _ in range(3)] if output_component is None else output_component
        self.input = InputComponent(self, max_sources=1) if input_component is None else input_component
        for out_comp in self.outputs:
            out_comp.owner = self
        self.input.owner = self
        self.connection = ConnectionComponent(self)

        self.input_dir = input_dir
        self.output_dirs = [d for d in ["N", "E", "S", "W"] if d != self.input_dir]

        if self.mode == "splitter":
            self.config = [1, 1, 1]
            self.current_output = 0
            self.current_count = 0
        elif self.mode == "filter":
            self.config = [-1, -1, 0]

        self.is_jammed = False
        self.buffer_comp = BufferComponent(maxlen=buffer_size)

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
        return self.buffer_comp.accept(item_name)
    
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
        if self.mode == 'splitter':
            if any(i > 0 for i in config):
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
        self.buffer_comp.flush_pending()
            
        if not self.buffer_comp.buffer:
            self.is_jammed = False
            self.input.ping()
            return

        item_name = self.buffer_comp.peek()

        if self.mode == "splitter":
            slot = self._get_split_slot()
            if slot is None:
                return
        else:
            slot = self._get_filter_slot(item_name)

        out_component = self.outputs[slot]  

        if out_component.try_push(item_name):

            if self.mode == "splitter":
                self.current_count += 1
                if self.current_count >= self.config[slot]:
                    self.current_count = 0
                    self.current_output = (self.current_output + 1) % 3

            self.buffer_comp.pop()
            self.is_jammed = False
            self.input.ping()
        else:
            self.is_jammed = True

    def get_outbound_ports(self):
        return dict(zip(self.output_dirs, self.outputs))
        
    def get_inbound_port(self, from_dir):
        if from_dir == self.input_dir:
            return self.input
        return None

    def to_dict(self):
        return {
            "class_name": "Router",
            "mode": self.mode,
            "x": self.position.x,
            "y": self.position.y,
            "config": self.config,
            "input_dir": self.input_dir
        }
    
    @classmethod
    def from_dict(cls, data, **kwargs):
        new_block = cls(
            x_pos=data["x"],
            y_pos=data["y"],
            mode=data["mode"],
            input_dir=data["input_dir"]
        )
        new_block.set_config(data["config"])
        return new_block
    
    def get_asset_name(self):
        return self.mode
    
    @classmethod
    def build(cls, x, y, ctx: BuildContext):
        return cls(x_pos=x, y_pos=y, input_dir=ctx.in_dir, mode=ctx.tool)


class Seller(BaseBlock):
    """
    Consumes items and adds corresponding funds to the player economy.

    Attributes
    ----------
    economy : Economy
        Reference to the global economy manager.
    sink : SinkComponent
        Buffers incoming items each tick before they are sold.
    """
    def __init__(self, x_pos, y_pos, economy_manager,
                 input_component=None):
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
        self.input = InputComponent(self) if input_component is None else input_component
        self.input.owner = self
        self.connection = ConnectionComponent(self)
        self.sink = SinkComponent()
        self.height = 4
        self.width = 4

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
        return self.sink.accept(item_name)

    def process_tick(self):
        """Sells all items in the buffer and clears it."""
        items = self.sink.drain()
        if not items:
            return

        total = sum(item_registry.get_price(item) for item in items)
        self.economy.add_money(total)

        if hasattr(self.economy, 'total_earned'):
            self.economy.total_earned += total

    def get_outbound_ports(self):
        return {}
        
    def get_inbound_port(self, from_dir):
        return self.input
    
    def to_dict(self):
        # return {
        #     "class_name": "Seller",
        #     "x": self.position.x,
        #     "y": self.position.y,
        # }
        return None
    
    @classmethod
    def from_dict(cls, data, **kwargs):
        # economy_manager = kwargs.get("economy_manager")
        # new_block = cls(
        #     x_pos=data["x"],
        #     y_pos=data["y"],
        #     economy_manager=economy_manager
        # )

        # return new_block
        return None

    def get_asset_name(self):
        return "seller"
    
    @classmethod
    def build(cls, x, y, ctx: BuildContext):
        return cls(x_pos=x, y_pos=y, economy_manager=ctx.economy)


class CentralStorage(BaseBlock):
    """
    Accepts items and places them directly into the player's main inventory.

    Attributes
    ----------
    inventory : object
        The main player inventory.
    sink : SinkComponent
        Buffers incoming items each tick before depositing them.
    """
    def __init__(self, x_pos, y_pos, player_inventory,
                 input_component=None):
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
        self.input = InputComponent(self) if input_component is None else input_component
        self.input.owner = self
        self.connection = ConnectionComponent(self)
        self.sink = SinkComponent()
        self.height = 4
        self.width = 4

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
        return self.sink.accept(item_name)

    def process_tick(self):
        """Deposits all items currently in the buffer into the player inventory."""
        for item in self.sink.drain():
            self.inventory.add_item(item, 1)
            if hasattr(self.inventory, 'total_stored'):
                self.inventory.total_stored[item] = self.inventory.total_stored.get(item, 0) + 1

    def get_outbound_ports(self):
        return {}
        
    def get_inbound_port(self, from_dir):
        return self.input
    
    def to_dict(self):
        # return {
        #     "class_name": "CentralStorage",
        #     "x": self.position.x,
        #     "y": self.position.y,
        # }
        return None
    
    @classmethod
    def from_dict(cls, data, **kwargs):
        # player_inventory = kwargs.get("player_inventory")
        # new_block = cls(
        #     x_pos=data["x"],
        #     y_pos=data["y"],
        #     player_inventory=player_inventory
        # )

        # return new_block
        return None
    
    def get_asset_name(self):
        return "storage"
    
    @classmethod
    def build(cls, x, y, ctx: BuildContext):
        return cls(x_pos=x, y_pos=y, player_inventory=ctx.inventory)