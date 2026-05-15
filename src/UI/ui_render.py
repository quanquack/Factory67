class UIRenderer:
    """
    Responsible for drawing the visual representation of the game.

    Attributes
    ----------
    game_manager : GameManager
        Reference to the core game logic and states.
    """
    def __init__(self, game_manager):
        self.game_manager = game_manager
        
    def render_frame(self):
        """
        Draws all game elements and UI components onto the screen.
        """
        pass

class InputHandler:
    """
    Processes user interactions such as mouse clicks or keyboard inputs.

    Attributes
    ----------
    game_manager : GameManager
        Reference to the core game logic to pass input actions.
    """
    def __init__(self, game_manager):
        self.game_manager = game_manager

    def handle_click(self, x, y, action):
        """
        Translates screen coordinates to grid actions and executes them.

        Parameters
        ----------
        x : int
            The x-coordinate of the click on the screen.
        y : int
            The y-coordinate of the click on the screen.
        action : str
            The type of action performed (e.g., 'place_block', 'upgrade').
        """
        pass