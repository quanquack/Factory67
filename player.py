class Economy:
    """Manages the player's primary financial resources."""
    def __init__(self):
        self.money = 0

    def add_money(self, amount):
        """Increases the player's total money."""
        self.money += amount

    def deduct_money(self, amount) -> bool:
        """Attempts to spend money, returning True if successful."""
        if self.money >= amount:
            self.money -= amount
            return True
        
        return False

class Inventory:
    """Main hub inventory for storing special upgrade items globally."""
    def __init__(self):
        # Dictionary tracking item types and their quantities
        self.inventory = {}

    def add_item(self, type, amount):
        """Adds a specific amount of an item to the global inventory."""
        if type in self.inventory:
            self.inventory[type] += amount
        else:
            self.inventory[type] = amount

    def deduct_item(self, type, amount) -> bool:
        """Attempts to consume items for upgrades, removing the key if empty."""
        if type in self.inventory and self.inventory[type] >= amount:
            self.inventory[type] -= amount
            if self.inventory[type] == 0:
                self.inventory.pop(type)
            return True

        return False
    
class RecipeManager:
    """Handles the availability and unlocking of crafting formulas."""
    def __init__(self):
        self.available_recipes = {}
        self.unlocked_recipes = []

    def unlock_recipe(self, recipe_id, player_economy):
        """Processes the transaction to unlock a new crafting recipe."""
        pass