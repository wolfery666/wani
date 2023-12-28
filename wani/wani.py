import pygame
import random
from enum import Enum
from .general import (SCREEN_WIDTH,SCREEN_HEIGHT,collidemask,loadasset,)

class WaniStateEnum(Enum):
    PASSIVE = 0
    AGRESSIVE = 1
    LAZY = 2

class WaniActionEnum(Enum):
    FEED = 0
    BITE = 1
    SLEEP = 2

ATTACK_ACTIONS = {WaniActionEnum.BITE}

class WaniState():
    def __init__(self, value, period, resume=False, replace=False):
        self.value = WaniStateEnum[value]
        self.period = period
        self.time = 0
        self.next = None

    @property
    def actions(self):
        if self.value == WaniStateEnum.LAZY:
            actions = {WaniActionEnum.SLEEP, WaniActionEnum.FEED}
        elif self.value == WaniStateEnum.AGRESSIVE:
            actions = {WaniActionEnum.SLEEP, WaniActionEnum.FEED, WaniActionEnum.BITE}
        else:
            actions = set()
        return actions

class WaniStateFlow():
    def __init__(self, flow):
        head = None
        next_state = None
        total_period = 0
        for (value, period) in reversed(flow):
            head = WaniState(value, period)
            head.next = next_state
            next_state = head
            total_period += period

        self.head = head
        self.period = total_period
        self.state = head

    @property
    def actions(self):
        if self.state is None:
            return set()
        return self.state.actions

    def reset(self):
        self.state = self.head
        state = self.head
        while state is not None:
            state.time = 0
            state = state.next

    def next_state(self, state):
        if state.time < state.period:
            return state

        next_state = state.next
        if next_state is None:
            return None

        next_state.time += (state.time - state.period)
        return self.next_state(next_state)

    def calculate(self):
        if self.state is not None:
            self.state.time += 1
            self.state = self.next_state(self.state)

        return self.state

class WaniStateController():
    def __init__(self, flow_settings):
        self.normal_flow = WaniStateFlow(flow_settings['main'])
        self.action_flows = {}
        for key, value in flow_settings['actions'].items():
            self.action_flows[WaniActionEnum[key]] = {'flow': WaniStateFlow(value['flow']), 'resume': value['resume']}

        self.flow_stack = [self.normal_flow]

    @property
    def flow(self):
        return self.flow_stack[0]

    @property
    def actions(self):
        return self.flow.actions

    @property
    def state(self):
        return self.flow.state

    def new_flow(self, flow, resume):
        if not resume:
            self.flow_stack.clear()
        elif len(self.flow_stack) > 0:
            self.flow.state.time += flow.period
        self.flow_stack.insert(0, flow)

    def reset(self):
        self.normal_flow.reset()
        self.flow_stack = [self.normal_flow]

    def calculate(self):
        while self.flow.calculate() is None and len(self.flow_stack) > 1:
            self.flow_stack.pop(0)

    def process_action(self, action):
        action_flow = self.action_flows[action]
        action_flow['flow'].reset()
        self.new_flow(action_flow['flow'], action_flow['resume'])

class WaniSprite(pygame.sprite.Sprite):
    def __init__(self, name, levels):
        super().__init__()

        self.images = []
        for i in range(levels+1):
            self.images.append(loadasset(name + "_" + str(i)))

        self.image = self.images.pop(0)
        self.rect = self.image.get_rect()

        self.mask = pygame.mask.from_surface(self.image, 0)

        self._layer = 2

    def update(self):
        image = self.images.pop(0)
        self.image.blit(image, image.get_rect())

    def flip(self):
        self.image = pygame.transform.flip(self.image, True, False)
        for i in range(len(self.images)):
            self.images[i] = pygame.transform.flip(self.images[i], True, False)

class WaniAttackArea(pygame.sprite.Sprite):
    def __init__(self, radius):
        super().__init__()

        self.radius_min = radius
        self.radius = radius

        self.image = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self.rect = self.image.get_rect()

        self.mask = None

        self._layer = 1

    def update(self, main):
        self.image.fill((0,0,0,0))
        pygame.draw.circle(self.image, (200,0,0,100), main.rect.center, self.radius)
        self.mask = pygame.mask.from_surface(self.image, 0)

    def increase_radius(self, value):
        if self.radius > SCREEN_WIDTH*2:
            return

        self.radius += value

    def restore_radius(self):
        self.radius = self.radius_min

class Wani():
    def __init__(self, name, hunger, radius):
        self.state_controller = None
        self.hunger = hunger

        self.hole = None

        self.main = WaniSprite(name, hunger)
        self.icon = WaniSprite(name + "_icon", hunger+1)

        self.attack_area = WaniAttackArea(radius)

    def activate(self, hole):
        self.hole = hole
        self.state_controller.reset()
        self.main.rect.midbottom = (hole.rect.centerx, hole.rect.top + hole.baseline)
        if bool(random.getrandbits(1)):
            self.main.flip()
        self.attack_area.update(self.main)
        self.attack_area.increase_radius(10)

    def update(self):
        if len(self.state_controller.actions) == 0:
            self.main.image.set_alpha(100)
        else:
            self.main.image.set_alpha(255)

        sprites = [self.main]
        if self.attack:
            sprites.append(self.attack_area)

        return sprites

    @property
    def full(self):
        return self.hunger == 0

    @property
    def hide(self):
        return self.state_controller.state is None

    @property
    def attack(self):
        return len(self.state_controller.actions & ATTACK_ACTIONS) != 0

    def process_state(self, field, mouse):
        for action in self.state_controller.actions:
            field_action = lambda: None
            is_break = False
            if action == WaniActionEnum.SLEEP:
                is_action = self.full
                is_break = is_action
            elif action == WaniActionEnum.BITE:
                is_action = collidemask(mouse['position'], self.attack_area)
                field_action = getattr(field, 'remove_life')
            elif action == WaniActionEnum.FEED:
                is_action = collidemask(mouse['down_click'], self.main)
            else:
                is_action = False
            if is_action:
                self.state_controller.process_action(action)
                self.feed()
                field_action()
            if is_break:
                break

        self.state_controller.calculate()

    def feed(self):
        if self.hunger == 0:
            return
        self.hunger -= 1
        self.main.update()
        self.icon.update()
        self.attack_area.restore_radius()
        self.attack_area.update(self.main)

    def remove(self):
        self.main.kill()
        self.attack_area.kill()
        self.icon.update()