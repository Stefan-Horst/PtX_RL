from abc import ABC, abstractmethod
from typing import Any


class Environment(ABC):
    
    def __init__(self, 
                 observation_space_size: int, 
                 observation_space_spec: Any, 
                 action_space_size: int, 
                 action_space_spec: Any,
                 reward_spec: Any):
        self.observation_space_size = observation_space_size
        self.observation_space_spec = observation_space_spec
        self.action_space_size = action_space_size
        self.action_space_spec = action_space_spec
        self.reward_spec = reward_spec
        self.terminated = False
        self.seed = None
    
    @abstractmethod
    def initialize(self, seed: int | None = None) -> tuple[Any, dict[str, Any]]:
        pass
    
    @abstractmethod
    def reset(self) -> tuple[Any, dict[str, Any]]:
        pass
    
    @abstractmethod
    def act(self, action: Any) -> tuple[Any, float, bool, bool, dict[str, Any]]:
        pass
