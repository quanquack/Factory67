import pygame
import os
from src.registry import item_registry, theme_registry

def _load_and_colorize_texture(filepath, color):
    """
    Load a grayscale image and apply a color tint while preserving transparency.
    
    Args:
        filepath (str): Path to the grayscale image template.
        color (tuple): RGB or RGBA color tuple defined in the config (e.g., (224, 115, 51)).
        
    Returns:
        pygame.Surface: The colorized image ready to be rendered.
    """
    original_image = pygame.image.load(filepath).convert_alpha()
    colorized_image = original_image.copy()
    
    brightness_boost = 1.4
    
    r = min(255, int(color[0] * brightness_boost))
    g = min(255, int(color[1] * brightness_boost))
    b = min(255, int(color[2] * brightness_boost))
    
    boosted_color = (r, g, b)
    
    colorized_image.fill(boosted_color, special_flags=pygame.BLEND_RGBA_MULT)
    
    ambient_light = 20
    colorized_image.fill((ambient_light, ambient_light, ambient_light), special_flags=pygame.BLEND_RGB_ADD)
    
    return colorized_image

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
    
    def _generate_fallback(self, name: str) -> pygame.Surface:
        """
        Build a tile-sized placeholder surface for a missing asset, with a
        deterministic color and a red indicator (used to verify rotation).
        """
        print(f"[AssetManager] Missing '{name}'. Using fallback.")
        fallback_surface = pygame.Surface((self.tile_size, self.tile_size))
        color = self._generate_consistent_color(name)
        fallback_surface.fill(color)
        rect = fallback_surface.get_rect()
        pygame.draw.rect(fallback_surface, (255, 255, 255), rect, 1)

        pygame.draw.rect(fallback_surface, (255, 50, 50), (self.tile_size // 2 - 2, 0, 4, 4))
        return fallback_surface

    def _load_from_paths(self, paths):
        for path in paths:
            if os.path.exists(path):
                try:
                    return pygame.image.load(path).convert_alpha()
                except pygame.error:
                    continue
        return None

    def _load_colorized_item(self, name: str):
        try:
            item_data = item_registry.item_data.get(name)
        except ImportError:
            return None
 
        if not item_data or "metadata" not in item_data:
            return None
 
        metadata = item_data["metadata"]
        if "color" not in metadata:
            return None
 
        template_name = metadata.get("template")
        template_path = f"assets/item/template/{template_name}.png"
        if os.path.exists(template_path):
            return _load_and_colorize_texture(template_path, metadata["color"])
        return None
    
    def _get_base_image(self, base_key: str, name: str, candidate_paths, allow_colorize: bool = False) -> pygame.Surface:
        if base_key in self.cache:
            return self.cache[base_key]
 
        image = None
        if allow_colorize:
            image = self._load_colorized_item(name)
 
        if image is None:
            image = self._load_from_paths(candidate_paths)
 
        if image:
            image = pygame.transform.scale(image, (self.tile_size, self.tile_size))
        else:
            image = self._generate_fallback(name)
 
        self.cache[base_key] = image
        return image
    
    def get_machine_asset(self, name: str, angle: int = 0, filepath: str = None) -> pygame.Surface:
        cache_key = f"{name}_{angle}"
        if cache_key in self.cache:
            return self.cache[cache_key]
 
        base_key = f"{name}_0"
        candidate_paths = [f"assets/machine/{name}.png", f"assets/conveyors/{name}.png"]
        if filepath and filepath not in candidate_paths:
            candidate_paths.append(filepath)
 
        base_image = self._get_base_image(base_key, name, candidate_paths)
 
        if angle != 0:
            rotated_image = pygame.transform.rotate(base_image, angle)
            self.cache[cache_key] = rotated_image
            return rotated_image
 
        return base_image

    def get_item_asset(self, name: str, filepath: str = None) -> pygame.Surface:
        base_key = f"item_{name}"
        candidate_paths = [f"assets/item/{name}.png"]
        if filepath and filepath not in candidate_paths:
            candidate_paths.append(filepath)
 
        return self._get_base_image(base_key, name, candidate_paths, allow_colorize=True)

    def get_tier_background(self, level, width: int, height: int) -> pygame.Surface:
        cache_key = f"tier_bg_{level}_{width}x{height}"
        if cache_key in self.cache:
            return self.cache[cache_key]
 
        bg_color = theme_registry.get_level_color(level)
        surface = pygame.Surface((width, height))
        surface.fill(bg_color)
        self.cache[cache_key] = surface
        return surface
 
    def get_asset(self, name: str, filepath: str, angle: int = 0) -> pygame.Surface:
        """
        Deprecated: retained for backward compatibility with any callers not
        yet migrated. New code should call get_machine_asset() for rotatable
        blocks or get_item_asset() for items.
        """
        return self.get_machine_asset(name, filepath=filepath, angle=angle)