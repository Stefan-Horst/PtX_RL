from abc import ABC, abstractmethod
from typing import Any


class Agent(ABC):
    
    @abstractmethod
    def act(self, observation: Any) -> Any:
        """Return an action determined by the agent's policy for the given observation."""
        pass
    
    @abstractmethod
    def update(self, observation: Any, action: Any, next_observation: Any, 
               reward: float, terminated: bool) -> None:
        """Update the agent's networks based on the given observation, action, 
        next observation, reward, and whether the itertaion is terminated."""
        pass
