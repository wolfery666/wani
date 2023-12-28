
from pathlib import Path
import pygame

HEADER_HEIGHT = 30
FOOTER_HEIGHT = 40

SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 512+HEADER_HEIGHT+FOOTER_HEIGHT

def collidemask(point, area):
    if point is None or not area.rect.collidepoint(point):
        return False

    return area.mask.get_at(tuple(map(lambda x,y: x-y, point, area.rect.topleft))) == 1

def loadasset(name):
    return pygame.image.load(Path("assets") / (name + ".png"))