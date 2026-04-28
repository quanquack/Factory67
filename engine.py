class GameMap:
    """
    Manages the grid layout and resources of the game world.

    Attributes
    ----------
    grid : dict
        Dictionary to store grid entities using (x, y) coordinates as keys.
    ores : list
        List to track all randomly spawned ore locations.
    """
    def __init__(self):
        self.grid = {} 
        self.ores = []

    def place_block(self, block_object):
        """
        Places a new block on the grid at its specified coordinates.

        Parameters
        ----------
        block_object : Block
            The block instance to be placed on the map.
        """
        pass
        
    def get_block_at(self, x, y):
        """
        Retrieves the block object located at the given coordinates.

        Parameters
        ----------
        x : int
            The x-coordinate on the grid.
        y : int
            The y-coordinate on the grid.

        Returns
        -------
        Block or None
            The block object at the specified location, or None if empty.
        """
        pass

class GameManager:
    """
    Core controller that manages the main game loop and global states.

    Attributes
    ----------
    game_map : GameMap
        The main map of the game.
    economy : Economy
        The economy manager handling player's money.
    """
    def __init__(self, game_map, economy_manager):
        self.game_map = game_map
        self.economy = economy_manager

    def update(self):
        """
        Executes the logic for a single game tick across all entities.
        """
        pass