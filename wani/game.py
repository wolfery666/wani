
import pygame
import random

from pygame.locals import (
    K_ESCAPE,
    KEYDOWN,
    QUIT,
    RLEACCEL,
    MOUSEBUTTONUP,
    MOUSEBUTTONDOWN,
    MOUSEMOTION,
)

from .wanis import (RegularWani,)
from .hole import (StoneWindow,)
from .levels import (LEVELS,)
from .general import (SCREEN_WIDTH,SCREEN_HEIGHT,HEADER_HEIGHT,FOOTER_HEIGHT,collidemask,loadasset,)

class ControlScreen():
    def __init__(self):
        self.next = None

    def activate(self):
        pass

    def update(self, window, mouse):
        pass

class LevelScreen(ControlScreen):
    def __init__(self, level):
        super().__init__()

        settings = LEVELS[level]

        lives_count = settings['lives']

        self.holes = pygame.sprite.Group()
        self.wanis = pygame.sprite.LayeredUpdates()

        self.wani_list = []
        self.show_wani = []
        for key, value in settings['map'].items():
            if key == 'stone_window':
                HoleClass = StoneWindow
            else:
                continue
            for position in value:
                self.holes.add(HoleClass(position))

        for key, value in settings['wani'].items():
            if key == 'regular':
                WaniClass = RegularWani
            else:
                continue
            for i in range(value):
                self.wani_list.append(WaniClass())

        #HUD
        self.background = pygame.sprite.Group()
        self.hud = pygame.sprite.Group()
        self.lives = []

        strlevel = str(level)

        self.background.add(Background("background_" + strlevel))
        self.background.add(Header("header_" + strlevel))
        self.background.add(Footer("footer_" + strlevel))

        for (index, wani) in enumerate(self.wani_list):
            icon = wani.icon
            icon.rect.center = (SCREEN_WIDTH - int(icon.rect.width*1.5)*(index + 1), SCREEN_HEIGHT - int(FOOTER_HEIGHT/2))
            self.hud.add(icon)

        for i in range(lives_count):
            life = pygame.sprite.Sprite()
            life.image = loadasset("life")
            life.rect = life.image.get_rect(center = (int(1.5*life.image.get_width())*(lives_count - i), int(HEADER_HEIGHT/2)))

            self.lives.append(life)
            self.hud.add(life)

    def activate(self):
        pygame.mouse.set_cursor((0,0), loadasset("cursor"))

    def update(self, window, mouse):
        self.process_state(mouse)

        self.background.draw(window)
        self.hud.draw(window)
        self.holes.draw(window)
        self.wanis.draw(window)

    def process_state(self, mouse):
        show_wani = []
        hole = None
        for active_wani in self.show_wani:
            wani = self.wani_list[active_wani]
            hole = wani.hole

            wani.process_state(self, mouse)

            if not wani.hide:
                show_wani.append(active_wani)
            elif wani.full:
                self.wani_list.remove(wani)
                wani.remove()

        self.show_wani = show_wani

        active_wani = self.activate_wani(hole)
        if active_wani is not None:
            self.show_wani.append(active_wani)

        self.wanis.empty()

        for active_wani in self.show_wani:
            wani = self.wani_list[active_wani]
            self.wanis.add(wani.update())

        if self.loss:
            self.next = 'loss_screen'
        elif self.win:
            self.next = 'win_screen'

    def activate_wani(self, hole):
        if len(self.show_wani) > 0 or len(self.wani_list) == 0:
            return None

        active_wani = random.randint(0, len(self.wani_list)-1)
        active_hole = self.select_hole(hole)
        wani = self.wani_list[active_wani]
        wani.activate(active_hole)
        return active_wani

    def select_hole(self, hole):
        new_hole = hole
        while new_hole == hole:
            num = random.randint(1, len(self.holes))
            new_hole = self.holes.sprites()[num-1]
        return new_hole

    def remove_life(self):
        life = self.lives.pop(0)
        life.kill()

    @property
    def win(self):
        return len(self.wani_list) == 0

    @property
    def loss(self):
        return len(self.lives) == 0

class Background(pygame.sprite.Sprite):
    def __init__(self, name):
        super().__init__()

        #(SCREEN_WIDTH, SCREEN_HEIGHT - HEADER_HEIGHT - FOOTER_HEIGHT)
        self.image = loadasset(name).convert()
        self.rect = self.image.get_rect(topleft = (0, HEADER_HEIGHT))

        self._layer = 1

class Header(pygame.sprite.Sprite):
    def __init__(self, name):
        super().__init__()

        #(SCREEN_WIDTH, HEADER_HEIGHT)
        self.image = loadasset(name)
        self.rect = self.image.get_rect()

        self._layer = 1

class Footer(pygame.sprite.Sprite):
    def __init__(self, name):
        super().__init__()

        #(SCREEN_WIDTH, FOOTER_HEIGHT)
        self.image = loadasset(name)
        self.rect = self.image.get_rect(topleft = (0, SCREEN_HEIGHT - FOOTER_HEIGHT))

        self._layer = 1

class Button(pygame.sprite.Sprite):
    def __init__(self, name):
        super().__init__()

        #(200, 80)
        self.passive = loadasset(name + "_p")
        self.active = loadasset(name + "_a")

        self.image = self.passive
        self.rect = self.image.get_rect()

        self.mask = pygame.mask.from_surface(self.image)

        self.click = False

        self._layer = 2

    def update(self, mouse):
        self.image = self.active if collidemask(mouse['position'], self) else self.passive
        self.click = collidemask(mouse['up_click'], self)

class BackgroundScreen(ControlScreen):
    def __init__(self, background_name, header_name=None, footer_name=None):
        super().__init__()

        self.sprites = pygame.sprite.LayeredUpdates()
        self.sprites.add(Background(background_name))
        if header_name:
            self.sprites.add(Header(header_name))
        if footer_name:
            self.sprites.add(Footer(footer_name))

    def activate(self):
        pygame.mouse.set_cursor(pygame.cursors.Cursor())

    def update(self, window, mouse):
        self.sprites.update(mouse)
        self.sprites.draw(window)

class ButtonScreen(BackgroundScreen):
    def __init__(self, background_name, button_name):
        super().__init__(background_name)

        button = Button(button_name)

        #(512,435)
        button.rect.center = (int(SCREEN_WIDTH/2), int(0.85*(SCREEN_HEIGHT - HEADER_HEIGHT - FOOTER_HEIGHT)))

        self.sprites.add(button)

        self.button = button

    def update(self, window, mouse):
        super().update(window, mouse)

        if self.button.click:
            self.next = 'new_level'

class StartScreen(ButtonScreen):
    def __init__(self):
        super().__init__("title", "start")

class LossScreen(ButtonScreen):
    def __init__(self):
        super().__init__("loss", "retry")

class WinScreen(ButtonScreen):
    def __init__(self):
        super().__init__("win", "next")

class EndScreen(BackgroundScreen):
    def __init__(self):
        super().__init__("end", "header_0", "footer_0")

class GameState():
    def __init__(self):
        self.level = 1

    def play(self):
        pygame.init()

        window = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

        screen = StartScreen()

        clock = pygame.time.Clock()

        running = True
        while running:
            mouse = {'position': pygame.mouse.get_pos(), 'down_click': None, 'up_click': None}

            for event in pygame.event.get():
                if event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        running = False
                elif event.type == QUIT:
                    running = False
                elif event.type == MOUSEBUTTONDOWN:
                    if event.button == 1:
                        mouse['down_click'] = event.pos
                elif event.type == MOUSEBUTTONUP:
                    if event.button == 1:
                        mouse['up_click'] = event.pos

            if screen.next is not None:
                screen = getattr(self, screen.next)()
                screen.activate()

            screen.update(window, mouse)

            pygame.display.flip()

            clock.tick(60)

        pygame.mixer.music.stop()
        pygame.mixer.quit()

        pygame.quit()

    def new_level(self):
        return LevelScreen(self.level)

    def loss_screen(self):
        return LossScreen()

    def win_screen(self):
        if self.level == LEVELS['max']:
            return EndScreen()
        else:
            self.level += 1
            return WinScreen()
