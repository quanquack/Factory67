class Economy:
    """
    Manages the player's primary financial resources.

    Attributes
    ----------
    money : int
        The total amount of money the player currently has.
    """
    def __init__(self):
        self.money = 0

    def add_money(self, amount):
        """
        Increases the player's total money.

        Parameters
        ----------
        amount : int
            The amount of money to add.
        """
        self.money += amount

    def deduct_money(self, amount) -> bool:
        """
        Attempts to spend money.

        Parameters
        ----------
        amount : int
            The amount of money to deduct.

        Returns
        -------
        bool
            True if deduction was successful, False if insufficient funds.
        """
        if self.money >= amount:
            self.money -= amount
            return True
        
        return False

class Inventory:
    """
    Main hub inventory for storing special upgrade items globally.

    Attributes
    ----------
    inventory : dict
        Dictionary tracking item types and their quantities.
    """
    def __init__(self):
        self.inventory = {}

    def add_item(self, item_type, amount):
        """
        Adds a specific amount of an item to the global inventory.

        Parameters
        ----------
        item_type : str
            The name/type of the item.
        amount : int
            The quantity to add.
        """
        if item_type in self.inventory:
            self.inventory[item_type] += amount
        else:
            self.inventory[item_type] = amount

    def deduct_item(self, item_type, amount) -> bool:
        """
        Attempts to consume items for upgrades.

        Parameters
        ----------
        item_type : str
            The name/type of the item to consume.
        amount : int
            The quantity required.

        Returns
        -------
        bool
            True if items were successfully deducted, False otherwise.
        """
        if item_type in self.inventory and self.inventory[item_type] >= amount:
            self.inventory[item_type] -= amount
            if self.inventory[item_type] == 0:
                self.inventory.pop(item_type)
            return True

        return False
    
class RecipeManager:
    """
    Handles the availability and unlocking of crafting formulas.

    Attributes
    ----------
    available_recipes : dict
        All recipes currently in the game.
    unlocked_recipes : list
        List of recipe IDs that the player can currently use.
    """
    def __init__(self):
        self.available_recipes = {}
        self.unlocked_recipes = []

    def unlock_recipe(self, recipe_id, player_economy):
        """
        Processes the transaction to unlock a new crafting recipe.

        Parameters
        ----------
        recipe_id : str
            The unique identifier for the recipe.
        player_economy : Economy
            The economy instance used to deduct unlock costs.
        """
        pass