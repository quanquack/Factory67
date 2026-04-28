class Block:
    """Base class for any placeable object on the game grid."""
    def __init__(self, x_pos, y_pos):
        self.x_pos = x_pos
        self.y_pos = y_pos

    def process_tick(self):
        """Defines the behavior of the block during a game tick."""
        raise NotImplementedError

class Machine(Block):
    """Base class for functional machines capable of processing items."""
    def __init__(self, x_pos, y_pos, base_speed):
        super().__init__(x_pos, y_pos)
        self.level = 1
        self.processing_speed = base_speed

    def upgrade(self, player_inventory):
        """Handles the logic for leveling up the machine."""
        raise NotImplementedError

class Conveyor(Block):
    """Transports items between different blocks on the map."""
    def __init__(self, x_pos, y_pos, direction):
        super().__init__(x_pos, y_pos)
        self.direction = direction
        # Holds the item currently being transported
        self.carrying_item = None

    def process_tick(self):
        """Moves the carried item to the next grid cell based on direction."""
        pass

class FunctionalBlock(Block):
    """Base class for destination blocks like containers or sellers."""
    def accept_item(self, item_name):
        """Determines if the block can receive the incoming item."""
        raise NotImplementedError

class InventorySlot:
    """Represents a single storage slot within a container."""
    def __init__(self, max_capacity):
        self.item_name = None
        self.current_amount = 0
        self.max_capacity = max_capacity

class Container(FunctionalBlock):
    """Storage unit that holds items using a slot-based system."""
    def __init__(self, x_pos, y_pos, max_slots, stack_limit):
        super().__init__(x_pos, y_pos)
        # Initialize a list of empty inventory slots
        self.slots = [InventorySlot(stack_limit) for _ in range(max_slots)]

    def accept_item(self, item_name):
        """Attempts to store an incoming item into an available slot."""
        # Try to add to an existing stack of the same item
        for slot in self.slots:
            if slot.item_name == item_name and slot.current_amount < slot.max_capacity:
                slot.current_amount += 1
                return True
        
        # Try to find an empty slot for the new item
        for slot in self.slots:
            if slot.item_name is None:
                slot.item_name = item_name
                slot.current_amount = 1
                return True
                
        # Return False if the container is entirely full
        return False

    def process_tick(self):
        """Containers are passive and do not perform active tick actions."""
        pass

class Seller(FunctionalBlock):
    """Consumes items and adds corresponding funds to the player economy."""
    def __init__(self, x_pos, y_pos, economy_manager, price_catalog):
        super().__init__(x_pos, y_pos)
        self.economy = economy_manager
        self.prices = price_catalog
        # Temporarily stores incoming items before they are sold
        self.input_buffer = []

    def accept_item(self, item_name):
        """Receives an item into the internal buffer for sale."""
        self.input_buffer.append(item_name)
        return True

    def process_tick(self):
        """Sells all items in the buffer and clears it."""
        if not self.input_buffer:
            return

        total = 0
        # Calculate total revenue based on the price catalog
        for item in self.input_buffer:
            price = self.prices.get(item, 0) 
            total += price

        self.economy.add_money(total)
        self.input_buffer.clear()