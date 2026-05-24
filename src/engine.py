class GameMap:
    def __init__(self):
        self.grid = {} 
        self.ores = []

    def get_block_at(self, x_pos, y_pos):
        return self.grid.get((x_pos, y_pos))
    
    def place_block(self, block_object):
        pass

    def remove_block(self, x_pos, y_pos):
        pass

class GameManager:
    def __init__(self, game_map, economy_manager):
        self.game_map = game_map
        self.economy = economy_manager

    def update(self):
        for coordinate, entity in self.game_map.grid.items():
            if hasattr(entity, 'process_tick'):
                entity.process_tick()