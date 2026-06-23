import json
import os
from src.entities import Miner, Conveyor, Machine, Seller

class SaveManager:
    """
    Handles saving and loading the game's state.
    """
    def __init__(self, game_manager):
        """
        Initialize the save manager with the current game manager.

        Args:
            game_manager: The game manager that stores the map and economy data.
        """
        self.game_manager = game_manager

    def save_game(self, filepath: str):
        """
        Save the current game state to a JSON file.

        Args:
            filepath (str): Path to the save file.
        """
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        data = {
            "economy": {
                "money": self.game_manager.economy.money
            },
            "entities": []
        }

        for (x, y), entity in self.game_manager.game_map.grid.items():
            class_name = entity.__class__.__name__
            
            ent_data = {
                "class_name": class_name,
                "x": x,
                "y": y
            }
            
            if hasattr(entity, 'output_dir'):
                ent_data['output_dir'] = entity.output_dir
            if hasattr(entity, 'input_dir'):
                ent_data['input_dir'] = entity.input_dir
            if hasattr(entity, 'ore'):
                ent_data['ore'] = entity.ore
            if hasattr(entity, 'machine_type'):
                ent_data['machine_type'] = entity.machine_type
                
            data["entities"].append(ent_data)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)

    def load_game(self, filepath: str) -> bool:

        """
        Load the game state from a JSON file.

        Args:
            filepath (str): Path to the save file.

        Returns:
            bool: True if loading succeeds, False if the file does not exist.
        """
        if not os.path.exists(filepath):
            return False
            
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.game_manager.economy.money = data.get("economy", {}).get("money", 0)

        self.game_manager.game_map.grid.clear()

        for ent_data in data.get("entities", []):
            x = ent_data["x"]
            y = ent_data["y"]
            cls_name = ent_data["class_name"]

            new_ent = None
            
            if cls_name == "Conveyor":
                new_ent = Conveyor(x, y, ent_data["input_dir"], ent_data["output_dir"])
            elif cls_name == "Miner":
                new_ent = Miner(x, y, ent_data.get("ore", "copper_ore"), ent_data["output_dir"])
            elif cls_name == "Machine":
                new_ent = Machine(x, y, ent_data["output_dir"], ent_data["machine_type"])
            elif cls_name == "Seller":
                new_ent = Seller(x, y, self.game_manager.economy)

            if new_ent:
                self.game_manager.game_map.grid[(x, y)] = new_ent

        for pos, entity in self.game_manager.game_map.grid.items():
            if hasattr(entity, 'connection'):
                entity.connection.update_outbound(self.game_manager.game_map)

        return True