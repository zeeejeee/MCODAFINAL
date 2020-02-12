import random

class Function_Block:
    def __init__(self, name, fb_type):
        self.name = name
        self.type = fb_type
        self.coupling = list()
        self.hardware = list()
        self.memory = random.randint(1, 3)
        self.wcet = 0
        self.SIL = 0
        self.num_of_copies = 1
        self.sensitive = False
        self.devices = list()

class Connection:
    def __init__(self):
        self.source = ''
        self.destination = ''
        self.intensity = 0

class Device:
    def __init__(self, name):
        self.name = name
        self.cost = 0
        self.energy = 0
        self.skills = list()
        self.RTE_lib = list()
        self.memory = 0
        self.SIL = 0
        self.open = True
        self.max_num_of_function_blocks = 4
        self.resources = list()
        self.function_blocks = list()
        self.network = set()

    def print_mapping(self):
        for fb in self.function_blocks:
            print(self.name, "<-", fb.name)

    def used(self):
        if not self.function_blocks:
            return False
        else:
            return True

class Link:
    def __init__(self):
        self.device = ''
        self.segment = ''

class Event:
    def __init__(self, name):
        self.name = name
        self.function_block = ''
        self.application = ''

class EventPair:
    def __init__(self):
        self.source = ''
        self.destination = ''

class EventPath:
    def __init__(self):
        self.application = ''
        self.deadline = 100000
        self.events = list()
        self.pairs = list()
