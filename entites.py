class Block:
    """
    Base class for any placeable object on the game grid.

    Attributes
    ----------
    x_pos : int
        The x-coordinate of the block.
    y_pos : int
        The y-coordinate of the block.
    """
    def __init__(self, x_pos, y_pos):
        self.x_pos = x_pos
        self.y_pos = y_pos

    def process_tick(self):
        """
        Defines the behavior of the block during a game tick.
        
        Raises
        ------
        NotImplementedError
            If the child class does not implement this method.
        """
        raise NotImplementedError

class Machine(Block):
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
        super().__init__(x_pos, y_pos)
        self.level = 1
        self.processing_speed = base_speed

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

class Conveyor(Block):
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
        super().__init__(x_pos, y_pos)
        self.direction = direction
        self.carrying_item = None

    def process_tick(self):
        """
        Moves the carried item to the next grid cell based on direction.
        """
        pass

class FunctionalBlock(Block):
    """
    Base class for destination blocks like containers or sellers.
    """
    def accept_item(self, item_name):
        """
        Determines if the block can receive the incoming item.

        Parameters
        ----------
        item_name : str
            The name of the incoming item.

        Raises
        ------
        NotImplementedError
            If the child class does not implement this method.
        """
        raise NotImplementedError

class InventorySlot:
    """
    Represents a single storage slot within a container.

    Attributes
    ----------
    item_name : str or None
        The name of the item stored in this slot.
    current_amount : int
        The current number of items in this slot.
    max_capacity : int
        The maximum number of items this slot can hold.
    """
    def __init__(self, max_capacity):
        self.item_name = None
        self.current_amount = 0
        self.max_capacity = max_capacity

class Container(FunctionalBlock):
    """
    Storage unit that holds items using a slot-based system.

    Attributes
    ----------
    slots : list of InventorySlot
        The list of slots available in this container.
    """
    def __init__(self, x_pos, y_pos, max_slots, stack_limit):
        super().__init__(x_pos, y_pos)
        self.slots = [InventorySlot(stack_limit) for _ in range(max_slots)]

    def accept_item(self, item_name):
        """
        Attempts to store an incoming item into an available slot.

        Parameters
        ----------
        item_name : str
            The name of the item to store.

        Returns
        -------
        bool
            True if the item was successfully stored, False if the container is full.
        """
        for slot in self.slots:
            if slot.item_name == item_name and slot.current_amount < slot.max_capacity:
                slot.current_amount += 1
                return True
        
        for slot in self.slots:
            if slot.item_name is None:
                slot.item_name = item_name
                slot.current_amount = 1
                return True
                
        return False

    def process_tick(self):
        """
        Containers are passive and do not perform active tick actions.
        """
        pass

class Seller(FunctionalBlock):
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
        super().__init__(x_pos, y_pos)
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
            # Tra cứu giá, nếu không có mặc định là 0
            price = self.prices.get(item, 0) 
            total += price

        self.economy.add_money(total)
        self.input_buffer.clear()