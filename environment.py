from abc import ABC, abstractmethod
from copy import copy
from typing import Any
import gymnasium as gym

from ptx.framework import ParameterObject


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


# only include attributes which are variable during the simulation
COMMODITY_ATTRIBUTES = []
CONVERSION_ATTRIBUTES = []
STORAGE_ATTRIBUTES = []
GENERATOR_ATTRIBUTES = []

class PtxEnvironment(Environment):
    
    def __init__(self, ptx_system: ParameterObject, 
                 commodity_attributes=COMMODITY_ATTRIBUTES, conversion_attributes=CONVERSION_ATTRIBUTES, 
                 storage_attributes=STORAGE_ATTRIBUTES, generator_attributes=GENERATOR_ATTRIBUTES):
        """Create environment with PtX sytem to use and optionally specify relevant attributes for the agent"""
        self.commodity_attributes = commodity_attributes
        self.conversion_attributes = conversion_attributes
        self.storage_attributes = storage_attributes
        self.generator_attributes = generator_attributes
        self._original_ptx_system = ptx_system
        super().__init__(None, None, None, None, None)
        
    def initialize(self, seed=None):
        self.seed = seed
        self.ptx_system = copy(self._original_ptx_system)
        return None, None
    
    def reset(self):
        self.ptx_system = copy(self._original_ptx_system)
        self.terminated = False
        return None, None
    
    def act(self, action):
        self._apply_action(action)
        
        reward = self._calculate_reward()
        return None, reward, False, False, None
    
    def _get_observation_space(self):
        return
    
    def _get_action_space(self):
        return
    
    def _apply_action(self, action):
        return
    
    def _calculate_reward(self):
        return
