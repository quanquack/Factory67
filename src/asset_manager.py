import pygame
import os

class AssetManager:
    """
    Manages image assets for the game.

    Provides caching to reduce redundant disk I/O and automatically generates
    placeholder surfaces when asset files are missing.
    """
    def __init__(self, tile_size=16):
        """
        Initialize the asset manager.

        Args:
            tile_size (int, optional): Default size (in pixels) to scale all assets to. Defaults to 16.
        """
        self.tile_size = tile_size
        self.cache = {} 

    def _generate_consistent_color(self, name: str):

        """
        Generate a deterministic RGB color based on a string identifier.

        This is used for placeholder assets so that each missing asset type
        has a visually distinct and consistent color.

        Args:
            name (str): Identifier of the asset.

        Returns:
            Tuple[int, int, int]: Generated RGB color.
        """

        r = (sum(ord(c) for c in name) * 17) % 200 + 55
        g = (sum(ord(c) for c in name) * 31) % 200 + 55
        b = (sum(ord(c) for c in name) * 73) % 200 + 55
        return (r, g, b)

    def get_asset(self, name: str, filepath: str) -> pygame.Surface:
        """
        Retrieve an asset from cache or load it from disk.

        If the asset cannot be found or loaded, a placeholder surface is
        generated and returned instead.

        Args:
            name (str): Unique identifier for the asset (e.g., 'miner', 'conveyor').
            filepath (str): Relative path to the asset file.

        Returns:
            pygame.Surface: A surface scaled to the configured tile size and ready for rendering.
        """
        if name in self.cache:
            return self.cache[name]
        
        try:
            if not os.path.exists(filepath):
                raise FileNotFoundError(f"File {filepath} not exist")

            image = pygame.image.load(filepath).convert_alpha()
            
            image = pygame.transform.scale(image, (self.tile_size, self.tile_size))
            
            self.cache[name] = image
            return image
            
        except (FileNotFoundError, pygame.error) as e:
            print(f"[AssetManager] Missing '{name}'. Using fallback. ({e})")
            
            fallback_surface = pygame.Surface((self.tile_size, self.tile_size))
            
            color = self._generate_consistent_color(name)
            fallback_surface.fill(color)
            
            rect = fallback_surface.get_rect()
            pygame.draw.rect(fallback_surface, (255, 255, 255), rect, 1)
            
            self.cache[name] = fallback_surface
            return fallback_surface