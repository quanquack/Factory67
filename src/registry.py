import json
import os

class MachineRegistry:
    """
    Centralized registry loading both metadata and recipes from JSON files.
    """
    def __init__(self):
        self.machine_data = {}

    def load_from_directory(self, folder_path: str):
        """
        Iterates through a folder, loading every .json file.
        Assumes JSON structure: {"metadata": {...}, "recipes": {...}}
        """
        if not os.path.exists(folder_path):
            raise FileNotFoundError(f"Critical Error: Folder {folder_path} not found!")

        for filename in os.listdir(folder_path):
            if filename.endswith(".json"):
                machine_type = filename.replace(".json", "")
                file_path = os.path.join(folder_path, filename)
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.machine_data[machine_type] = json.load(f)
                    
        print(f"Successfully loaded data for: {list(self.machine_data.keys())}")

    def get_recipes(self, machine_type: str) -> dict:
        """
        Retrieves the recipe dictionary. Defaults to empty dict if not found.
        """
        return self.machine_data.get(machine_type, {}).get("recipes", {})

    def get_metadata(self, machine_type: str) -> dict:
        """
        Retrieves the intrinsic configuration for a machine type.
        """
        return self.machine_data.get(machine_type, {}).get("metadata", {})

registry = MachineRegistry()