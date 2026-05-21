import json
import os

class Recipes:
    """
    A centralized registry holding game recipes.
    """
    def __init__(self):
        self.all_recipes = {}

    def load_from_json(self, folder_path: str):
        """
        Iterates through a folder, loading every .json file.
        The filename (without .json) becomes the machine type key.
        """
        if not os.path.exists(folder_path):
            raise FileNotFoundError(f"Critical Error: Folder {folder_path} not found!")

        for filename in os.listdir(folder_path):
            if filename.endswith(".json"):
                machine_type = filename.replace(".json", "")
                file_path = os.path.join(folder_path, filename)
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.all_recipes[machine_type] = json.load(f)
                    
        print(f"Successfully loaded recipes for: {list(self.all_recipes.keys())}")

    def get_recipes_for(self, machine_type: str) -> dict:
        """
        Retrieves the recipe dictionary for a specific machine type.
        """
        return self.all_recipes.get(machine_type, {})

recipe_registry = Recipes()