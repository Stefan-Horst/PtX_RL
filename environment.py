from abc import ABC, abstractmethod
from copy import copy
import math
from typing import Any
import numpy as np
import gymnasium as gym

from ptx.commodity import Commodity
from ptx.component import ConversionComponent, GenerationComponent, StorageComponent
from ptx.framework import PtxSystem
from util import contains_only_unique_elements, flatten_list_or_dict


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
# there are not enough different system configurations to properly train on those attributes
# attributes which are not simple values are marked with their type in square brackets
COMMODITY_ATTRIBUTES =  ["purchased_quantity", "sold_quantity", "available_quantity", 
                         "emitted_quantity", "demanded_quantity", "charged_quantity", 
                         "discharged_quantity", "consumed_quantity", "produced_quantity", 
                         "generated_quantity", "selling_revenue", "total_storage_costs", 
                         "total_production_costs", "total_generation_costs"]
CONVERSION_ATTRIBUTES = ["variable_om", "total_variable_costs", 
                         "[dict]consumed_commodities", "[dict]produced_commodities"]
STORAGE_ATTRIBUTES =    ["variable_om", "total_variable_costs", 
                         "charged_quantity", "discharged_quantity"]
GENERATOR_ATTRIBUTES =  ["variable_om", "total_variable_costs", 
                         "generated_quantity", "total_costs", "curtailment"]
# actual possible actions of each element depend on what the configuration allows
# e.g. selling commodity is only possible if it's set to saleable
COMMODITY_ACTIONS = [Commodity.purchase_commodity, Commodity.sell_commodity, Commodity.emit_commodity]
CONVERSION_ACTIONS = [ConversionComponent.convert_commodities, ConversionComponent.ramp_up_or_down]
STORAGE_ACTIONS = [StorageComponent.charge_quantity, StorageComponent.discharge_quantity] # maybe discharge automatically if production too low
GENERATOR_ACTIONS = [GenerationComponent.apply_curtailment]

class PtxEnvironment(Environment):
    """Environment simulating a PtX system. The environment is flexible regarding 
    the exact configuration of the system and allows for its attributes (i.e. observations) 
    and actions to be specified via the constructor."""
    
    def __init__(self, ptx_system: PtxSystem, 
                 commodity_attributes=COMMODITY_ATTRIBUTES, conversion_attributes=CONVERSION_ATTRIBUTES, 
                 storage_attributes=STORAGE_ATTRIBUTES, generator_attributes=GENERATOR_ATTRIBUTES, 
                 commodity_actions=COMMODITY_ACTIONS, conversion_actions=CONVERSION_ACTIONS, 
                 storage_actions=STORAGE_ACTIONS, generator_actions=GENERATOR_ACTIONS):
        """Create environment with PtX sytem to use and optionally specify 
        relevant attributes and actions for the agent."""
        self.commodity_attributes = commodity_attributes
        self.conversion_attributes = conversion_attributes
        self.storage_attributes = storage_attributes
        self.generator_attributes = generator_attributes
        self.commodity_actions = commodity_actions
        self.conversion_actions = conversion_actions
        self.storage_actions = storage_actions
        self.generator_actions = generator_actions
        self._original_ptx_system = ptx_system
        self.ptx_system = copy(self._original_ptx_system)
        
        observation_space_size = len(self._get_current_observation())
        # high, low, and dtype might change in the future and with different configurations
        observation_space_spec = {"low": 0, 
                                  "high": math.inf, 
                                  "shape": (observation_space_size,), 
                                  "dtype": np.float64}
        action_space_spec = self._get_action_space_spec()
        action_space_size = len(flatten_list_or_dict(action_space_spec))
        reward_spec = {}
        super().__init__(observation_space_size, observation_space_spec, action_space_size, 
                         action_space_spec, reward_spec)
        self._action_space = self._get_action_space()
        
    def initialize(self, seed=None):
        self.seed = seed
        observation, info = self.reset()
        return observation, info
    
    def reset(self):
        self.terminated = False
        observation = self._get_current_observation()
        info = {} # useful info might be implemented later
        return observation, info
    
    def act(self, action):
        self._apply_action(action)
        
        reward = self._calculate_reward()
        return None, reward, False, False, None
    
    def _get_observation_space_spec(self):
        """Create dict with each element of the ptx system (commodities, components) 
        as key and possible observations (attributes) as values. Attributes that are 
        dicts are added with their keys as list."""
        observation_space_spec = {}
        element_categories = self._get_element_categories_with_attributes_and_actions()
        for category, attributes, _ in element_categories:
            for element in category:
                element_attributes = []
                possible_attributes = element.get_possible_observation_attributes(attributes)
                for attribute in possible_attributes:
                    # add all keys of attributes that are dictionaries as 
                    # new dict with name as key and keys as values
                    if attribute.startswith("[dict]"):
                        attribute = attribute[6:]
                        element_attributes.append(
                            {attribute: list(getattr(element, attribute).keys())}
                        )
                    else:
                        element_attributes.append(attribute)
                observation_space_spec[element.name] = element_attributes
        return observation_space_spec
    
    def _get_current_observation(self):
        """Get the current observation by iterating over all elements of the 
        ptx system and adding their attributes as specified in the constants."""
        observation_space = []
        commodities = self.ptx_system.get_all_commodities()
        for commodity in commodities:
            possible_attributes = commodity.get_possible_observation_attributes(
                self.commodity_attributes
            )
            for attribute in possible_attributes:
                observation_space.append(getattr(commodity, attribute))
        
        generators = self.ptx_system.get_generator_components_objects()
        for generator in generators:
            possible_attributes = generator.get_possible_observation_attributes(
                self.generator_attributes
            )
            for attribute in possible_attributes:
                observation_space.append(getattr(generator, attribute))
        
        conversions = self.ptx_system.get_conversion_components_objects()
        for conversion in conversions:
            possible_attributes = conversion.get_possible_observation_attributes(
                self.conversion_attributes
            )
            for attribute in possible_attributes:
                # add all values of attributes that are dictionaries
                if attribute.startswith("[dict]"):
                    for value in getattr(conversion, attribute[6:]).values():
                        observation_space.append(value)
                else:
                    observation_space.append(getattr(conversion, attribute))
        
        storages = self.ptx_system.get_storage_components_objects()
        for storage in storages:
            for attribute in self.storage_attributes:
                observation_space.append(getattr(storage, attribute))
        return observation_space
    
    def _get_action_space_spec(self):
        """Create dict with each element of the ptx system (commodities, components) 
        as key and possible actions (methods) as values."""
        assert contains_only_unique_elements(
            self.ptx_system.get_all_commodity_names() + self.ptx_system.get_all_component_names()
        ), "All elements of the ptx system must have a unique name."
        
        action_space_spec = {}
        element_categories = self._get_element_categories_with_attributes_and_actions()
        for category, _, actions in element_categories:
            for element in category:
                element_actions = []
                possible_actions = element.get_possible_action_methods(actions)
                for action in possible_actions:
                    element_actions.append(action.__name__)
                action_space_spec[element.name] = element_actions
        return action_space_spec

    def _get_action_space(self):
        """Create list with tuples of each element and its possible actions."""
        action_space = []
        element_categories = self._get_element_categories_with_attributes_and_actions()
        for category, _, actions in element_categories:
            for element in category:
                possible_actions = element.get_possible_action_methods(actions)
                for action in possible_actions:
                    action_space.append((element, action))
        return action_space
    
    def _get_element_categories_with_attributes_and_actions(self):
        commodities = self.ptx_system.get_all_commodities()
        generators = self.ptx_system.get_generator_components_objects()
        conversions = self.ptx_system.get_conversion_components_objects()
        storages = self.ptx_system.get_storage_components_objects()
        return [(commodities, self.commodity_attributes, self.commodity_actions), 
                (generators, self.generator_attributes, self.generator_actions), 
                (conversions, self.conversion_attributes, self.conversion_actions), 
                (storages, self.storage_attributes, self.storage_actions)]

    def _apply_action(self, action):
        return
    
    def _calculate_reward(self):
        return
