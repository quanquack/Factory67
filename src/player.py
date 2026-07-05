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
        self.total_earned = 0
        self.last_total_earned = 0
        self.money_rate = 0

    def add_money(self, amount: int):
        """
        Increases the player's total money.

        Parameters
        ----------
        amount : int
            The amount of money to add.
        """
        self.money += amount

    def deduct_money(self, amount: int) -> bool:
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
        self.unlocked_recipes = []
        self.total_stored = {}
        self.last_total_stored = {}
        self.item_rates = {}

    def add_item(self, item_type: str, amount: int):
        """
        Adds a specific amount of an item to the global inventory.

        Parameters
        ----------
        item_type : str
            The internal name or type of the item.
        amount : int
            The quantity to add.
        """
        if item_type in self.inventory:
            self.inventory[item_type] += amount
        else:
            self.inventory[item_type] = amount

    def deduct_item(self, item_list: dict[str, int]) -> bool:
        """
        Attempts to consume multiple items simultaneously, ensuring all requirements are met.

        Parameters
        ----------
        item_list : dict[str, int]
            A dictionary mapping item names to their required quantities.

        Returns
        -------
        bool
            True if all items were successfully deducted, False if any requirement fails.
        """
        for entry in item_list:
            if entry not in self.inventory:
                return False
            if self.inventory[entry] < item_list[entry]:
                return False
        
        for entry in item_list:
            self.inventory[entry] -= item_list[entry]
            if self.inventory[entry] == 0:
                self.inventory.pop(entry)
            
        return True
    
    def to_dict(self):
        return {
            "items": self.inventory,
            "unlocked_recipes": self.unlocked_recipes
        }
    
    def from_dict(self, data):
        self.inventory = data.get("items", {})
        self.unlocked_recipes = data.get("unlocked_recipes", [])


class RecipeManager:
    """
    Handles the availability and unlocking of crafting formulas.

    Attributes
    ----------
    available_recipes : dict
        All recipes currently registered in the game.
    unlocked_recipes : list
        List of recipe IDs that the player is currently permitted to use.
    """
    def __init__(self):
        self.available_recipes = {}
        self.unlocked_recipes = []

    def unlock_recipe(self, recipe_id: str, player_economy: Economy):
        """
        Processes the transaction to unlock a new crafting recipe.

        Parameters
        ----------
        recipe_id : str
            The unique identifier for the requested recipe.
        player_economy : Economy
            The global economy instance used to deduct unlock costs.
        """
        pass