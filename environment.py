from abc import ABC, abstractmethod


class Environment(ABC):
    
    def __init__(self, seed=None):
        self._seed = seed
        self.info = {"action_space_size": 0}
    
    @abstractmethod
    def initialize(self):
        pass
    
    @abstractmethod
    def act(self, action):
        pass
    