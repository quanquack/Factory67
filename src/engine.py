import random
import json
import os
from perlin_noise import PerlinNoise
from functools import lru_cache
from src.registry import machine_registry, item_registry, ore_registry
from src.components import BuildContext

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
            self.noise_layers[ore_name] = PerlinNoise(octaves=2.1, seed=ore_seed)

        self.get_ore_at = lru_cache(maxsize=65536)(self._get_ore_at)

    def _get_ore_at(self, x, y):
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
        
        if not block_object.removable:
            return False
            
        if hasattr(block_object, 'connection'):
            block_object.connection.on_break(self)

        chunk.grid.pop((x_pos, y_pos), None)
            
        if not chunk.grid:
            del self.chunks[(cx, cy)]
            
        return True
    
    def get_ore_at(self, x_pos, y_pos):
        return self.generator.get_ore_at(x_pos, y_pos)

class StatisticManager:
    def __init__(self):
        self.tick_counter = 0
        self.UPDATE_INTERVAL = 60
    def process_metrics(self, economy, inventory):
        self.tick_counter += 1
        
        if self.tick_counter >= self.UPDATE_INTERVAL:
            current_money_rate = economy.total_earned - economy.last_total_earned
            economy.money_rate = getattr(economy, 'money_rate', 0.0) * 0.8 + current_money_rate * 0.2
            economy.last_total_earned = economy.total_earned
            
            for item, count in inventory.total_stored.items():
                current_item_rate = count - inventory.last_total_stored.get(item, 0)
                old_rate = inventory.item_rates.get(item, 0.0)

                inventory.item_rates[item] = old_rate * 0.8 + current_item_rate * 0.2
                inventory.last_total_stored[item] = count
                
            self.tick_counter = 0

class GameManager:
    def __init__(self, game_map, economy_manager, player_inventory):
        self.game_map = game_map
        self.economy = economy_manager
        self.inventory = player_inventory
        self.victory_achieved = False

        self.stats_manager = StatisticManager()

    def load_scenario(self, filepath: str):
        """Đọc scenario khởi tạo từ file JSON và spawn các công trình mặc định"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                scenario_data = json.load(f)
        except FileNotFoundError:
            print(f"[Engine] NO Scenarios named {filepath} was found.")
            return

        for hub in scenario_data.get("starting_hubs", []):
            ctx = BuildContext(
                tool=hub["tool_id"],
                out_dir=hub.get("out_dir", "S"),
                in_dir=hub.get("in_dir", "N"),
                game_map=self.game_map,
                economy=self.economy,
                inventory=self.inventory,
                game_manager=self
            )
            
            block_class = machine_registry.get_class(hub["tool_id"])
            if not block_class:
                continue
                
            block = block_class.build(hub["x"], hub["y"], ctx)
            if block:
                block.width = hub.get("width", 1)
                block.height = hub.get("height", 1)
                
                for dx in range(block.width):
                    for dy in range(block.height):
                        grid_x = hub["x"] + dx
                        grid_y = hub["y"] + dy
                        cx, cy = self.game_map._get_chunk(grid_x, grid_y)
                        chunk = self.game_map.get_chunk(cx, cy, create_new=True)
                        
                        chunk.grid[(grid_x, grid_y)] = block
                        chunk.is_modified = True
                        
                if hasattr(block, 'connection'):
                    block.connection.on_place(self.game_map)

    def update(self):    
        for chunk in self.game_map.chunks.values():
            if not chunk.is_modified:
                continue
            for entity in chunk.grid.values():
                if hasattr(entity, 'buffer_comp'):
                    entity.buffer_comp.flush_pending()
                elif hasattr(entity, 'pending_items'):
                    if entity.pending_items:
                        entity.items.extend(entity.pending_items)
                        entity.pending_items.clear()

        for chunk in self.game_map.chunks.values():
            if not chunk.is_modified:
                continue
            for entity in chunk.grid.values():
                if hasattr(entity, 'process_tick'):
                    entity.process_tick()
      
        self.stats_manager.process_metrics(self.economy, self.inventory)

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

        self.game_manager.load_scenario("data/scenarios/default_start.json")

        for chunk_data in save_data.get("chunks", []):
            for entity_data in chunk_data.get("entities", []):
                class_name = entity_data.get("class_name")
                
                block_class = None
                for data in machine_registry.machine_data.values():
                    if data.get("metadata", {}).get("class_name") == class_name:
                        block_class = data.get("class")
                        break
                
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