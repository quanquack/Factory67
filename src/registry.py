import json
import os

class MachineRegistry:
    """
    Centralized registry loading both metadata and recipes from JSON files.

    Attributes
    ----------
    machine_data : dict
        A dictionary storing parsed JSON data for all machine types.
    """
    def __init__(self):
        self.machine_data = {}

    def load_from_directory(self, folder_path: str):
        """
        Iterates through a folder, loading every .json file.
        Assumes JSON structure: {"metadata": {...}, "recipes": {...}}

        Parameters
        ----------
        folder_path : str
            The path to the directory containing machine JSON files.

        Raises
        ------
        FileNotFoundError
            If the specified folder_path does not exist.
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
        Retrieves the recipe dictionary for a specific machine type.

        Parameters
        ----------
        machine_type : str
            The identifier for the machine type.

        Returns
        -------
        dict
            The recipes available for the machine, or an empty dictionary if not found.
        """
        return self.machine_data.get(machine_type, {}).get("recipes", {})

    def get_metadata(self, machine_type: str) -> dict:
        """
        Retrieves the intrinsic configuration metadata for a machine type.

        Parameters
        ----------
        machine_type : str
            The identifier for the machine type.

        Returns
        -------
        dict
            The metadata configuration, or an empty dictionary if not found.
        """
        return self.machine_data.get(machine_type, {}).get("metadata", {})
    
    def generate_ore_recipes(self, ore_configs: dict):
        for machine, data in self.machine_data.items():
            metadata = data.get("metadata", {})
            templates = metadata.get("recipe_templates", {})

            if not templates:
                continue

            for ore_name, ore_config in ore_configs.items():
                for product in ore_config.get("products", []):
                    if product in templates:
                        template = templates[product]
                        output_name = template["output"].replace("{ore}", ore_name)
                        
                        ingredients = {
                            k.replace("{ore}", ore_name): v
                            for k, v in template["ingredients"].items()
                        }

                        self.machine_data[machine].setdefault("recipes", {})
                        if output_name not in self.machine_data[machine]["recipes"]:
                            self.machine_data[machine]["recipes"][output_name] = ingredients

    def resolve_class(self, block_classes):
        class_map = {cls.__name__: cls for cls in block_classes}
        for data in self.machine_data.values():
            class_name = data["metadata"].get("class_name")
            if class_name:
                data["class"] = class_map[class_name]

    def get_class(self, machine_type, default=None):
        return self.machine_data.get(machine_type, {}).get("class", default)


class ItemRegistry:
    """
    Centralized registry managing item properties and values.

    Attributes
    ----------
    item_data : dict
        A dictionary storing properties for all items.
    """
    def __init__(self):
        self.item_data = {}

    def load_from_directory(self, folder_path: str):
        """
        Loads item data from all JSON files within a specified directory.

        Parameters
        ----------
        folder_path : str
            The path to the directory containing item JSON files.

        Raises
        ------
        FileNotFoundError
            If the specified folder_path does not exist.
        """
        if not os.path.exists(folder_path):
            raise FileNotFoundError(f"Critical Error: Folder {folder_path} not found!")
        
        for filename in os.listdir(folder_path):
            if filename.endswith(".json"):
                with open(os.path.join(folder_path, filename), 'r', encoding='utf-8') as f:
                    self.item_data.update(json.load(f))

    def load_from_file(self, file_path: str):
        """
        Loads item data from a single JSON file.

        Parameters
        ----------
        file_path : str
            The exact path to the target JSON file.
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            self.item_data = json.load(f)

    def get_price(self, item_name: str) -> int:
        """
        Retrieves the base price of an item.

        Parameters
        ----------
        item_name : str
            The internal identifier of the item.

        Returns
        -------
        int
            The price of the item, or 0 if not defined.
        """
        return self.item_data.get(item_name, {}).get("price", 0)

    def get_image(self, item_name: str) -> str:
        """
        Retrieves the file path or identifier for the item's texture.

        Parameters
        ----------
        item_name : str
            The internal identifier of the item.

        Returns
        -------
        str or None
            The image path, or None if not defined.
        """
        return self.item_data.get(item_name, {}).get("image", None)

    def get_display_name(self, item_name: str) -> str:
        """
        Retrieves the localized or formatted display name of an item.

        Parameters
        ----------
        item_name : str
            The internal identifier of the item.

        Returns
        -------
        str
            The display name, or the internal item_name if no display name is defined.
        """
        return self.item_data.get(item_name, {}).get("display_name", item_name)
    
    def generate_ore_items(self, ore_configs: dict):
        product_multipliers = {
            "plate":  4,
            "wire":   6,
            "liquid": 5
        }

        for ore_name, config in ore_configs.items():
            base_price = config.get("base_price", 1)

            color = tuple(config.get("color", [255, 255, 255]))

            self.item_data[ore_name] = {
                "display_name": f"{ore_name.capitalize()} Ore",
                "price": base_price,
                "image": f"assets/{ore_name}.png",
                "metadata": {
                    "color": color,
                    "template": "ore"
                }
            }

            for product in config.get("products", []):
                item_name = f"{ore_name}_{product}"
                multiplier = product_multipliers.get(product, 1)
                self.item_data[item_name] = {
                    "display_name": f"{ore_name.capitalize()} {product.capitalize()}",
                    "price": base_price * multiplier,
                    "image": f"assets/{item_name}.png",
                    "metadata": {
                        "color": color,
                        "template": product
                    }
                }


class OreRegistry:
    def __init__(self):
        self.ore_data = {}

    def load_from_file(self, file_path: str):
        with open(file_path, 'r', encoding='utf-8') as f:
            self.ore_data = json.load(f)

    def get_all_ores(self):
        return self.ore_data

    def get_color(self, ore_name: str):
        color_list = self.ore_data.get(ore_name, {}).get("color", [255, 0, 255])
        return tuple(color_list)


class ThemeRegistry:
    """
    Centralized registry managing all color themes and UI styling from a JSON file.
    """
    def __init__(self):
        self.theme_data = {}

    def load_from_file(self, file_path: str):
        """Loads the color theme configuration from a JSON file."""
        if not os.path.exists(file_path):
            print(f"Warning: Theme file {file_path} not found. Using defaults.")
            return
            
        with open(file_path, 'r', encoding='utf-8') as f:
            self.theme_data = json.load(f)

    def get_color(self, category: str, key: str, default=(255, 255, 255)):
        """Retrieves a specific RGB color tuple from a category."""
        category_data = self.theme_data.get(category, {})
        color_list = category_data.get(key, default)
        return tuple(color_list)

    def get_level_color(self, level: int):
        """Retrieves the background color for a specific machine level."""
        level_data = self.theme_data.get("levels", {})
        color_list = level_data.get(str(level), [120, 125, 135])
        return tuple(color_list)


machine_registry = MachineRegistry()
item_registry = ItemRegistry()
ore_registry = OreRegistry()
theme_registry = ThemeRegistry()