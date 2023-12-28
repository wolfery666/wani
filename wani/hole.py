
import pygame
from .general import (SCREEN_WIDTH,loadasset,)

class Hole(pygame.sprite.Sprite):
    def __init__(self, name, position, baseline):
        super().__init__()

        self.image = loadasset(name)
        self.rect = self.image.get_rect(center = position)

        self.baseline = baseline

class StoneWindow(Hole):
    def __init__(self, position):
        super().__init__("stone_window", position, 125)