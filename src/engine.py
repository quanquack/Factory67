import random
import json
import os
from perlin_noise import PerlinNoise
from functools import lru_cache
import src.entities as entities
from src.registry import machine_registry, item_registry, ore_registry

class Chunk:
    def __init__(self, cx, cy):
        self.cx = cx
        self.cy = cy
        self.grid = {}
        self.is_modified = False


class MapGenerator:
    def __init__(self, seed=None):
        self.seed = seed if seed is not None else random.randint(0, 2**32)

        self.ore_configs = ore_registry.get_all_ores()

        self.noise_layers = {}
        for ore_name, config in self.ore_configs.items():
            ore_seed = self.seed + config.get("seed_offset", 0)
            self.noise_layers[ore_name] = PerlinNoise(octaves=3, seed=ore_seed)

    @lru_cache(maxsize=16384)
    def get_ore_at(self, x, y):
        for ore_name, config in self.ore_configs.items():
            noise_val = self.noise_layers[ore_name]([x * config["scale"], y * config["scale"]])
            if noise_val > config["threshold"]:
                return ore_name
        return None

class GameMap:
    def __init__(self, chunk_size=16, seed=None):
        self.chunk_size = chunk_size
        self.chunks = {} 
        self.generator = MapGenerator(seed=seed)

    def _get_chunk(self, x_pos, y_pos):
        return x_pos // self.chunk_size, y_pos // self.chunk_size
    
    def get_chunk(self, cx, cy, create_new=False):
        if (cx, cy) not in self.chunks and create_new:
            self.chunks[(cx, cy)] = Chunk(cx, cy)
        return self.chunks.get((cx, cy))

    def get_block_at(self, x_pos, y_pos):
        cx, cy = self._get_chunk(x_pos, y_pos)
        chunk = self.get_chunk(cx, cy)
        
        if chunk:
            return chunk.grid.get((x_pos, y_pos))
        return None
    
    def spawn_fixed_hubs(self, player_inventory, economy_manager):
        storage_hub = entities.CentralStorage(-8, -2, player_inventory)
        storage_hub.width = 4
        storage_hub.height = 4
        
        for dx in range(4):
            for dy in range(4):
                grid_x = -8 + dx
                grid_y = -2 + dy
                cx, cy = self._get_chunk(grid_x, grid_y)
                chunk = self.get_chunk(cx, cy, create_new=True)
                chunk.grid[(grid_x, grid_y)] = storage_hub
                chunk.is_modified = True
                
        storage_hub.connection.on_place(self)

        seller_hub = entities.Seller(4, -2, economy_manager)
        seller_hub.width = 4
        seller_hub.height = 4
        
        for dx in range(4):
            for dy in range(4):
                grid_x = 4 + dx
                grid_y = -2 + dy
                cx, cy = self._get_chunk(grid_x, grid_y)
                chunk = self.get_chunk(cx, cy, create_new=True)
                chunk.grid[(grid_x, grid_y)] = seller_hub
                chunk.is_modified = True
                
        seller_hub.connection.on_place(self)
    
    def place_block(self, block_object):
        x, y = block_object.position.get_coord()
        cx, cy = self._get_chunk(x, y)
        
        chunk = self.get_chunk(cx, cy, create_new=True)
         
        if (x, y) in chunk.grid:
            return False
        
        chunk.grid[(x, y)] = block_object
        chunk.is_modified = True

        if hasattr(block_object, 'connection'):
            block_object.connection.on_place(self)

        return True

    def remove_block(self, x_pos, y_pos):
        cx, cy = self._get_chunk(x_pos, y_pos)
        chunk = self.get_chunk(cx, cy)
        
        if not chunk:
            return False
            
        block_object = chunk.grid.get((x_pos, y_pos))
        if not block_object:
            return False
        
        if isinstance(block_object, (entities.CentralStorage, entities.Seller)):
            return False
            
        if hasattr(block_object, 'connection'):
            block_object.connection.on_break(self)

        chunk.grid.pop((x_pos, y_pos), None)
            
        if not chunk.grid:
            del self.chunks[(cx, cy)]
            
        return True
    
    def get_ore_at(self, x_pos, y_pos):
        return self.generator.get_ore_at(x_pos, y_pos)

class GameManager:
    def __init__(self, game_map, economy_manager, player_inventory):
        self.game_map = game_map
        self.economy = economy_manager
        self.inventory = player_inventory
        self.victory_achieved = False

        self.tick_counter = 0

    def update(self):
        for chunk in self.game_map.chunks.values():
            if not chunk.is_modified:
                continue
            for entity in chunk.grid.values():
                if hasattr(entity, 'process_tick'):
                    entity.process_tick()

        self.tick_counter += 1
        if self.tick_counter >= 60:
            current_money_rate = self.economy.total_earned - self.economy.last_total_earned
            self.economy.money_rate = getattr(self.economy, 'money_rate', 0.0) * 0.8 + current_money_rate * 0.2
            self.economy.last_total_earned = self.economy.total_earned

            for item, count in self.inventory.total_stored.items():
                current_item_rate = count - self.inventory.last_total_stored.get(item, 0)
                old_rate = self.inventory.item_rates.get(item, 0.0)
                
                self.inventory.item_rates[item] = old_rate * 0.8 + current_item_rate * 0.2
                self.inventory.last_total_stored[item] = count

            self.tick_counter = 0

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
        directory = os.path.dirname(filepath)
        
        if directory:
            os.makedirs(directory, exist_ok=True)
        save_data = {
            "money": self.economy.money,
            "inventory": self.inventory.to_dict(),
            "victory_achieved": getattr(self.game_manager, 'victory_achieved', False),
            "seed": self.game_map.generator.seed,
            "chunks": []
        }

        for (cx, cy), chunk in self.game_map.chunks.items():
            if not chunk.is_modified:
                continue
                
            chunk_data = {
                "cx": cx,
                "cy": cy,
                "entities": []
            }
            
            for pos, entity in chunk.grid.items():
                if hasattr(entity, "to_dict"):
                    data = entity.to_dict()
                    if data is not None:
                        chunk_data["entities"].append(data)
                    
            save_data["chunks"].append(chunk_data)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=4)

    def load_game(self, filepath="save.json"):
        self.game_map.chunks.clear()
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                save_data = json.load(f)
        except FileNotFoundError:
            return False

        self.economy.money = save_data.get("money", 0)
        self.game_manager.victory_achieved = save_data.get("victory_achieved", False)

        if "inventory" in save_data:
            self.inventory.from_dict(save_data["inventory"])
        
        saved_seed = save_data.get("seed")
        if saved_seed is not None:
            self.game_map.generator = MapGenerator(seed=saved_seed)

        self.game_map.spawn_fixed_hubs(self.inventory, self.economy)

        for chunk_data in save_data.get("chunks", []):
            for entity_data in chunk_data.get("entities", []):
                class_name = entity_data.get("class_name")
                block_class = getattr(entities, class_name, None)
                
                if block_class and hasattr(block_class, 'from_dict'):
                    new_block = block_class.from_dict(
                        entity_data, 
                        game_map=self.game_map,
                        economy_manager=self.economy,
                        player_inventory=self.inventory
                    )
                    if new_block:
                        self.game_map.place_block(new_block)

        return True