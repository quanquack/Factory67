class Position:
    """Component handling spatial data on the grid."""
    def __init__(self, x, y):
        self.x = x
        self.y = y

class InventoryComponent:
    """Component handling storage logic, extracted from Container."""
    def __init__(self, max_slots, stack_limit):
        self.slots = [InventorySlot(stack_limit) for _ in range(max_slots)]

    def add_item(self, item_name):
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

class Container:
    """
    Storage unit that holds items using a slot-based system.

    Attributes
    ----------
    inventory : InventoryComponent
        The component handling inventory slots and storage logic.
    """
    def __init__(self, x_pos, y_pos, max_slots, stack_limit):
        self.position = Position(x_pos, y_pos)
        self.inventory = InventoryComponent(max_slots, stack_limit)

    def accept_item(self, item_name):
        """
        Delegates storing items to the inventory component.
        """
        return self.inventory.add_item(item_name)

    def process_tick(self):
        """
        Containers are passive and do not perform active tick actions.
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
            # Tra cứu giá, nếu không có mặc định là 0
            price = self.prices.get(item, 0) 
            total += price

        self.economy.add_money(total)
        self.input_buffer.clear()