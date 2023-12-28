from .wani import (Wani, WaniStateController,)

WANI_RADIUS = 75

WANI_FLOW = {'main': (('PASSIVE', 10), ('AGRESSIVE', 30), ('LAZY', 20)),
             'actions': {'FEED': {'flow': (('PASSIVE', 10),), 'resume': False},
                         'BITE': {'flow': (('LAZY', 10),), 'resume': True},
                         'SLEEP': {'flow': (('PASSIVE', 10),), 'resume': False}}}

class RegularWani(Wani):
    def __init__(self):
        super().__init__("regular_wani", 2, WANI_RADIUS)

        self.state_controller = WaniStateController(WANI_FLOW)