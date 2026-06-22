import json
import entities

class GameMap:
    def __init__(self):
        self.grid = {} 
        self.ores = []

    def get_block_at(self, x_pos, y_pos):
        return self.grid.get((x_pos, y_pos))
    
    def place_block(self, block_object):
        coord = block_object.get_coord()
         
        if coord in self.grid:
            return False
        
        self.grid[coord] = block_object

        if hasattr(block_object, 'connection'):
            block_object.connection.on_place(self)

        return True

    def remove_block(self, x_pos, y_pos):
        block_object = self.grid.get((x_pos, y_pos))
        
        if not block_object:
            return False
            
        if hasattr(block_object, 'connection'):
            block_object.connection.on_break(self)
        else:
            self.grid.pop((x_pos, y_pos), None)
            
        return True

class GameManager:
    def __init__(self, game_map, economy_manager, player_inventory):
        self.game_map = game_map
        self.economy = economy_manager
        self.inventory = player_inventory

    def update(self):
        for coordinate, entity in self.game_map.grid.items():
            if hasattr(entity, 'process_tick'):
                entity.process_tick()

class SaveLoadManager:
    """ 
    Manages the serialization and deserialization of the game state.
    """
    def __init__(self, game_manager):
        self.game_manager = game_manager
        self.game_map = game_manager.game_map
        self.economy = game_manager.economy
        self.inventory = game_manager.inventory

    def save_game(self, filepath="save.json"):
        save_data = {
            "money": self.economy.money,
            "entities": []
        }
        
        for pos, entity in self.game_map.grid.items():
            if hasattr(entity, "to_dict"):
                save_data["entities"].append(entity.to_dict())
                
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=4)

    def load_game(self, filepath="save.json"):
        self.game_map.grid.clear()
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                save_data = json.load(f)
        except FileNotFoundError:
            return False

        self.economy.money = save_data.get("money", 0)

        for data in save_data.get("entities", []):
            class_name = data.get("class_name")
            
            block_class = getattr(entities, class_name, None)
            
            if block_class and hasattr(block_class, 'from_dict'):
                new_block = block_class.from_dict(
                    data, 
                    game_map=self.game_map,
                    economy_manager=self.economy,
                    player_inventory=self.inventory
                )
                self.game_map.place_block(new_block)

        return True