import pygame
import sys
import os
from src.engine import GameMap, GameManager, SaveLoadManager
from src.asset_manager import AssetManager
from src.player import Economy, Inventory
from src.UI.ui_render import UIRenderer, InputHandler, Camera 
from src.UI.menu import MainMenu
from src.registry import ore_registry

def main():
    """
    Entry point of the game application.

    This function initializes all core systems required for running the game,
    including the Pygame environment, rendering window, game state managers,
    input handling, camera, and UI systems. It also sets up the save/load
    mechanism using a JSON file.

    The game operates with two main states:
        - "MENU": Displays the main menu and handles user interactions such as
          starting a new game, continuing from a saved game, or quitting.
        - "PLAYING": Runs the main gameplay loop, including event handling,
          game updates, rendering, and user input processing.

    Key responsibilities:
        - Initialize game components (map, economy, managers, renderer, etc.)
        - Maintain and switch between game states (MENU <-> PLAYING)
        - Handle user input events (keyboard, mouse, zoom)
        - Automatically save game data on exit or when returning to the menu
        - Load saved game data from disk when requested
        - Run the main game loop at a fixed frame rate (60 FPS)

    Notes:
        - Game progress is saved to "data/savegame.json".
        - The game automatically saves when:
            + The user exits the game via the window close button while playing
            + The user presses ESC to return to the main menu
        - A new game resets the map and player economy.

    Raises:
        SystemExit: Triggered when the game loop ends and the application exits.
    """

    pygame.init()
    screen_width, screen_height = 800, 600
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Factory67")
    clock = pygame.time.Clock()

    ore_registry.load_from_file("data/ores.json")

    game_map = GameMap()
    economy = Economy()
    player_inventory = Inventory()
    game_manager = GameManager(game_map, economy_manager=economy, player_inventory=player_inventory)

    asset_manager = AssetManager(tile_size=16)
    camera = Camera(screen_width, screen_height, base_tile_size=16)
    input_handler = InputHandler(game_manager, camera, tile_size=16)
    renderer = UIRenderer(screen, game_manager, asset_manager, input_handler, camera, tile_size=16)
    main_menu = MainMenu(screen_width, screen_height)

    # SAVE/LOAD
    save_manager = SaveLoadManager(game_manager)
    save_file_path = "save/savegame.json"

    #"MENU" and "PLAYING"
    current_state = "MENU" 

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if current_state == "PLAYING":
                    save_manager.save_game(save_file_path)
                    print("[System] Automatically saved!")
                running = False
                
            if current_state == "MENU":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    action = main_menu.handle_click(event.pos)
                    
                    if action == "new_game":
                        game_manager.game_map.chunks.clear()
                        game_manager.economy.money = 0
                        game_manager.game_map.spawn_fixed_hubs(
                            game_manager.inventory, 
                            game_manager.economy
                        )
                        current_state = "PLAYING"
                        print("[System] New game start!")
                        
                    elif action == "continue":
                        if os.path.exists(save_file_path):
                            save_manager.load_game(save_file_path)
                            print("[System] Successfully download file save!")
                            current_state = "PLAYING"
                        else:
                            print("[System] No recent data, please start up new game.")
                        
                    elif action == "quit":
                        running = False

            elif current_state == "PLAYING":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    save_manager.save_game(save_file_path)
                    current_state = "MENU"
                    print("[System] Game saved!")

                elif event.type == pygame.KEYDOWN:
                    input_handler.handle_keydown(event.key)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    input_handler.handle_mouse_down(event.pos[0], event.pos[1], event.button)
                elif event.type == pygame.MOUSEBUTTONUP:
                    input_handler.handle_mouse_up(event.button)
                elif event.type == pygame.MOUSEMOTION:
                    input_handler.handle_mouse_motion(event.pos[0], event.pos[1])
                elif event.type == pygame.MOUSEWHEEL:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    input_handler.handle_zoom(event.y, mouse_x, mouse_y)

        if current_state == "MENU":
            main_menu.draw(screen)
        elif current_state == "PLAYING":
            game_manager.update()
            renderer.render_frame()

        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()