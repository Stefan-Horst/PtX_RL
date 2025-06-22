from abc import ABC, abstractmethod
from typing import Any
import gymnasium as gym


class Environment(ABC):
    """Abstract base class for all environments."""
    
    def __init__(self, 
                 observation_space_size: int, 
                 observation_space_spec: Any, 
                 action_space_size: int, 
                 action_space_spec: Any,
                 reward_spec: Any):
        """Create the environment with given specifications and sizes of the 
        observation and action spaces as well as specs of the reward."""
        self.observation_space_size = observation_space_size
        self.observation_space_spec = observation_space_spec
        self.action_space_size = action_space_size
        self.action_space_spec = action_space_spec
        self.reward_spec = reward_spec
        self.terminated = False
        self.seed = None
    
    @abstractmethod
    def initialize(self, seed: int | None = None) -> tuple[Any, dict[str, Any]]:
        """Initialize the environment after its creation and return the initial observation (and info)."""
        pass
    
    @abstractmethod
    def reset(self) -> tuple[Any, dict[str, Any]]:
        """Reset the environment and return the new initial observation (and info)."""
        pass
    
    @abstractmethod
    def act(self, action: Any) -> tuple[Any, float, bool, bool, dict[str, Any]]:
        """Take an action running one timestep and return the new observed state, 
        the reward, whether the environment has been terminated or truncated (and info)."""
        pass


class GymEnvironment(Environment):
    """Reference environment for gymnasium environments, acting as a wrapper. 
    The default environment is HalfCheetah-v5, as it is relatively simple and 
    has comparable action and observation spaces to the PtX environment."""
    
    def __init__(self, env="HalfCheetah-v5"):
        self.env = gym.make(env)
        super().__init__(self.env.observation_space.shape[0], 
                         self.env.observation_space, 
                         self.env.action_space.shape[0], 
                         self.env.action_space,
                         None)
    
    def initialize(self, seed=None):
        self.seed = seed
        observation, info = self.env.reset(seed=seed)
        return observation, info
    
    def reset(self):
        observation, info = self.env.reset()
        self.terminated = False
        return observation, info
    
    def act(self, action):
        observation, reward, terminated, truncated, info = self.env.step(action)
        self.terminated = terminated or truncated
        return observation, reward, terminated, truncated, info
