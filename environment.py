from abc import ABC, abstractmethod
from copy import copy
from typing import Any
import gymnasium as gym

from ptx.commodity import Commodity
from ptx.component import ConversionComponent, GenerationComponent, StorageComponent
from ptx.framework import PtxSystem
from ptx.weather import WeatherDataProvider
from logger import log, Level
from util import contains_only_unique_elements


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
# the numbers are the order of the actions in the order they are executed, starting from 0
# actions can be executed multiple times in different phases
COMMODITY_ACTIONS = [
    (Commodity.purchase_commodity, [2]), 
    (Commodity.sell_commodity, [4]), 
    (Commodity.emit_commodity, [6])
]
CONVERSION_ACTIONS = [
    (ConversionComponent.ramp_up_or_down, [3]) # conversion automatic and only control ramp
]
STORAGE_ACTIONS = [
    (StorageComponent.charge_or_discharge_quantity, [1, 5]) # discharge in 1, charge in 5
]
GENERATOR_ACTIONS = [
    (GenerationComponent.apply_or_strip_curtailment, [0]) # generation automatic depending on curtailment
]

class PtxEnvironment(Environment):
    """Environment simulating a PtX system. The environment is flexible regarding 
    the exact configuration of the system and allows for its attributes (i.e. observations) 
    and actions to be specified via the constructor."""
    
    def __init__(self, ptx_system: PtxSystem, weather_provider: WeatherDataProvider, 
                 weather_forecast_days=1, max_steps_per_episode=100000,
                 commodity_attributes=COMMODITY_ATTRIBUTES, conversion_attributes=CONVERSION_ATTRIBUTES, 
                 storage_attributes=STORAGE_ATTRIBUTES, generator_attributes=GENERATOR_ATTRIBUTES, 
                 commodity_actions=COMMODITY_ACTIONS, conversion_actions=CONVERSION_ACTIONS, 
                 storage_actions=STORAGE_ACTIONS, generator_actions=GENERATOR_ACTIONS):
        """Create environment with PtX sytem to use and optionally specify 
        relevant attributes and actions for the agent."""
        self.weather_provider = weather_provider
        self.weather_forecast_days = weather_forecast_days
        self.max_steps_per_episode = max_steps_per_episode
        self.commodity_attributes = commodity_attributes
        self.conversion_attributes = conversion_attributes
        self.storage_attributes = storage_attributes
        self.generator_attributes = generator_attributes
        self.commodity_actions = commodity_actions
        self.conversion_actions = conversion_actions
        self.storage_actions = storage_actions
        self.generator_actions = generator_actions
        
        ptx_system.weather_provider = weather_provider
        self._original_ptx_system = ptx_system
        self.ptx_system = copy(self._original_ptx_system)
        
        assert contains_only_unique_elements(
            self.ptx_system.get_all_commodity_names() + self.ptx_system.get_all_component_names()
        ), "All elements of the ptx system must have a unique name."
        
        self.seed = None
        self.iteration = 1
        self.step = 0
        self.terminated = False
        self.cumulative_reward = 0.
        self.current_iteration_reward = 0.
        observation_space_spec = self._get_observation_space_spec()
        observation_space_size = len(self._get_current_observation())
        action_space_spec = self._get_action_space_spec()
        self._action_space = self._get_action_space()
        action_space_size = len(self._action_space)
        reward_spec = {}
        super().__init__(observation_space_size, observation_space_spec, action_space_size, 
                         action_space_spec, reward_spec)
        log(f"Observation space: {observation_space_spec}")
        log(f"Action space: {action_space_spec}")
        
    def initialize(self, seed=None):
        self.seed = seed # currently not used
        self.iteration = 1
        self.cumulative_reward = 0.
        self._init_new_iteration("ENVIRONMENT INITIALIZED")
        observation = self._get_current_observation()
        info = {} # useful info might be implemented later
        return observation, info
    
    def reset(self):
        self.iteration += 1
        self._init_new_iteration(f"ENVIRONMENT RESET, ITERATION {self.iteration}")
        observation = self._get_current_observation()
        info = {} # useful info might be implemented later
        return observation, info
    
    def _init_new_iteration(self, msg):
        self.terminated = False
        self.step = 0
        self.current_iteration_reward = 0
        self.ptx_system = copy(self._original_ptx_system)
        log(msg)
        log(msg, loggername="status")
        log(msg, loggername="reward")
    
    def act(self, action):
        self.step += 1
        state_change_info, success = self._apply_action(action)
        
        balance_difference = self.ptx_system.next_step()
        reward = self._calculate_reward(balance_difference)
        self.cumulative_reward += reward
        self.current_iteration_reward += reward
        truncated = self.step >= self.max_steps_per_episode
        self.teminated = not success or truncated
        
        observation = self._get_current_observation()
        info = {item[0]: item[1] for item in state_change_info}
        info["step_revenue"] = balance_difference
        # logging below
        reward_msg = (f"Reward: {reward:.4f}, Current iteration reward: "
                      f"{self.current_iteration_reward:.4f}, "
                      f"Cumulative reward: {self.cumulative_reward:.4f}")
        log(str(self.ptx_system) + "\n\t" + reward_msg)
        log(f"Step {self.step}, Reward {reward:.4f} - {info}", loggername="status")
        log(reward_msg, loggername="reward")
        if self.terminated:
            if truncated:
                msg = "ENVIRONMENT TRUNCATED"
            else:
                msg = "ENVIRONMENT TERMINATED"
            log(msg, level=Level.WARNING)
            log(msg, level=Level.WARNING, loggername="status")
            log(msg, level=Level.WARNING, loggername="reward")
        return observation, reward, self.terminated, truncated, info
    
    def _calculate_reward(self, revenue):
        """Calculate the reward for the current step based on the increase of balance of 
        the ptx system since the last step and if any conversion has failed. Also take the 
        amount of time taken into account by reducing the reward in later steps."""
        # negative reward if system fails (i.e. conversion with set load is not possible)
        if self.terminated:
            return -100.
        
        # negative reward if any "loose" commodities are left in the system at the end of a step
        total_available_commodities = sum(
            [commodity.available_quantity for commodity in self.ptx_system.get_all_commodities()]
        )
        if total_available_commodities >= 0:
            return -10.
        
        # encourage more efficient and early reward maximization
        discount_factor = 1 - self.step / self.max_steps_per_episode
        reward = revenue * discount_factor
        return reward
    
    def _apply_action(self, action):
        """Call the specified action methods of the elements of the 
        ptx system with the provided values for the action space"""
        assert (all(isinstance(x, (int, float)) for x in action) and 
            len(action) == self.action_space_size), \
            "Action must have correct shape and values correct types."
        
        element_action_values = self._set_action_execution_order(action)
        
        pre_conversion_eavs, conversion_eavs, post_conversion_eavs = \
            self._create_action_execution_stages(element_action_values)
        
        # execute methods of elements with values and current state as parameters
        # handle the action methods of the three stages separately one after another
        state_change_infos = []
        total_success = True
        for element, action_method_tuple, value in pre_conversion_eavs:
            state_change_info, success, _ = self._execute_action(element, action_method_tuple, value)
            state_change_infos.append(state_change_info)
            total_success = total_success and success
        
        state_change_info, success = self._handle_conversion_action_method_execution(conversion_eavs)
        state_change_infos.extend(state_change_info)
        total_success = total_success and success
        
        for element, action_method_tuple, value in post_conversion_eavs:
            state_change_info, success, _ = self._execute_action(element, action_method_tuple, value)
            state_change_infos.append(state_change_info)
            total_success = total_success and success
        return state_change_infos, total_success

    def _handle_conversion_action_method_execution(self, conversion_eavs):
        """Execute the conversion action methods in the approximately best order. First, the action 
        methods that can be exactly completed as specified are executed. If any remain after that, 
        the action method that is closest to being exactly completed is executed. It is determined 
        by having the smallest deviation between the specified quantity (method parameter) and the 
        actually possible quantity. Then these steps are repeated from the first step until all 
        action methods have been executed. This ordering matters as the execution of one conversion 
        can make the execution of other conversions possible.
        """
        state_change_infos = []
        total_success = True
        while len(conversion_eavs) > 0:
            lowest_quantity_deviation = float("inf")
            lowest_quantity_deviation_item = None
            last_return_value = None
            # execute all conversions that can be exactly completed and return if all could be completed
            while True: # repeat until no more exact completions of conversions are possible
                progress_made = False
                for item in conversion_eavs:
                    element, action_method_tuple, value = item
                    action_method, _ = action_method_tuple
                    values, status, success, exact_completion = action_method(
                        element, value, self.ptx_system
                    )
                    if exact_completion: # directly execute conversion
                        element.apply_action_method(action_method, self.ptx_system, values)
                        state_change_info = (element.name, status)
                        state_change_infos.append(state_change_info)
                        total_success = total_success and success
                        conversion_eavs.remove(item)
                        progress_made = True
                    else:
                        # calculate deviation between specified quantity and actually possible 
                        # quantity and update the item with the lowest deviation
                        deviation = abs(values[0] - value)
                        if deviation < lowest_quantity_deviation:
                            lowest_quantity_deviation = deviation
                            lowest_quantity_deviation_item = item
                            last_return_value = (values, status, success)
                if not progress_made:
                    break
            if len(conversion_eavs) == 0:
                return state_change_infos, total_success
            
            # if not all conversions could be exactly completed, execute the conversion with 
            # the lowest deviation between specified quantity and actually possible quantity
            element, action_method_tuple, value = lowest_quantity_deviation_item
            action_method, _ = action_method_tuple
            values, status, success = last_return_value
            element.apply_action_method(action_method, self.ptx_system, values)
            state_change_info = (element.name, status)
            state_change_infos.append(state_change_info)
            total_success = total_success and success
            conversion_eavs.remove(lowest_quantity_deviation_item)
        return state_change_infos, total_success

    def _set_action_execution_order(self, action):
        """Set the order in which the action methods are executed based on the phase numbers 
        defined in the constants. For action methods with multiple possible phases defined, the 
        correct phase for this step is chosen based on the value of the action method's parameter."""
        element_action_values = []
        for element_action_method_tuple, value in zip(self._action_space, action):
            element, action_method_tuple = element_action_method_tuple
            # set phase in which the action is executed based on if 
            # the value is positive (charge) or negative (discharge)
            action_method = action_method_tuple[0]
            phase = action_method_tuple[1]
            if action_method == StorageComponent.charge_or_discharge_quantity:
                if value <= 0: # discharge
                    element_action_values.append((element, (action_method, phase[0]), value))
                else: # charge
                    element_action_values.append((element, (action_method, phase[1]), value))
            else:
                assert len(phase) == 1, "Each concrete action of a step may only occur in one phase."
                element_action_values.append(
                    (element, (action_method_tuple[0], action_method_tuple[1][0]), value)
                )
        # sort actions by phase
        element_action_values = sorted(element_action_values, key=lambda x: x[1][1])
        return element_action_values

    def _create_action_execution_stages(self, element_action_values):
        """Separate the action methods which are already ordered by phase into three stages based 
        on if they are executed before, during or after the conversion phase (ramp_up_or_down)."""
        pre_conversion_eavs = []
        conversion_eavs = []
        post_conversion_eavs = []
        stage = 0
        for item in element_action_values:
            action_method = item[1][0]
            if stage == 0:
                if action_method == ConversionComponent.ramp_up_or_down:
                    conversion_eavs.append(item)
                    stage = 1
                else:
                    pre_conversion_eavs.append(item)
            elif stage == 1:
                if action_method != ConversionComponent.ramp_up_or_down:
                    post_conversion_eavs.append(item)
                    stage = 2
                else:
                    conversion_eavs.append(item)
            else: # stage == 2
                post_conversion_eavs.append(item)
        return pre_conversion_eavs, conversion_eavs, post_conversion_eavs
    
    def _execute_action(self, element, action_method_tuple, value):
        """Execute a single action method of an element of the ptx 
        system with the provided value as that method's parameter."""
        action_method, _ = action_method_tuple
        values, status, success, exact_completion = action_method(element, value, self.ptx_system)
        element.apply_action_method(action_method, self.ptx_system, values)
        state_change_info = (element.name, status)
        return state_change_info, success, exact_completion
    
    def _get_current_observation(self):
        """Get the current observation by iterating over all elements of the ptx 
        system and adding the values of their attributes, as well as the current 
        step and weather data for each generator for the next specified steps."""
        observation_space = [self.step]
        element_categories = self._get_element_categories_with_attributes_and_actions()
        
        generators = element_categories[1][0]
        # append current weather and forecast weather
        for i in range(self.weather_forecast_days + 1):
            for generator in generators:
                observation_space.append(
                    self.weather_provider.get_weather_of_tick(self.step + i)[generator.name]
                )
        
        for category, attributes, _ in element_categories:
            for element in category:
                possible_attributes = element.get_possible_observation_attributes(attributes)
                for attribute in possible_attributes:
                    # add all values of attributes that are dictionaries
                    if attribute.startswith("[dict]"):
                        attribute = attribute[6:]
                        observation_space.extend(
                            list(getattr(element, attribute).values())
                        )
                    else:
                        observation_space.append(getattr(element, attribute))
        return observation_space
    
    def _get_action_space(self):
        """Create list with tuples of each element and its possible actions."""
        action_space = []
        element_categories = self._get_element_categories_with_attributes_and_actions()
        for category, _, action_tuples in element_categories:
            for element in category:
                possible_actions = element.get_possible_action_methods(action_tuples)
                for action in possible_actions:
                    action_space.append((element, action))
        return action_space
    
    def _get_observation_space_spec(self):
        """Create dict with each element of the ptx system (commodities, components) as key and 
        possible observations (attributes) as values, as well as environment data with data for 
        each step as values. Attributes that are dicts are added with their keys as list."""
        element_categories = self._get_element_categories_with_attributes_and_actions()
        
        environment_data = ["current_step"]
        generators = element_categories[1][0]
        for generator in generators:
                environment_data.append(f"current_{generator.name}")
        
        for i in range(self.weather_forecast_days):
            for generator in generators:
                environment_data.append(f"step{i+1}_{generator.name}")
        observation_space_spec = {"environment": environment_data}
        
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
    
    def _get_action_space_spec(self):
        """Create dict with each element of the ptx system (commodities, components) 
        as key and possible actions (methods) as values."""
        action_space_spec = {}
        element_categories = self._get_element_categories_with_attributes_and_actions()
        for category, _, action_tuples in element_categories:
            for element in category:
                element_actions = []
                possible_action_tuples = element.get_possible_action_methods(action_tuples)
                possible_actions = [action_tuple[0] for action_tuple in possible_action_tuples]
                for action in possible_actions:
                    element_actions.append(action.__name__)
                action_space_spec[element.name] = element_actions
        return action_space_spec

    def _get_element_categories_with_attributes_and_actions(self):
        commodities = self.ptx_system.get_all_commodities()
        generators = self.ptx_system.get_generator_components_objects()
        conversions = self.ptx_system.get_conversion_components_objects()
        storages = self.ptx_system.get_storage_components_objects()
        return [(commodities, self.commodity_attributes, self.commodity_actions), 
                (generators, self.generator_attributes, self.generator_actions), 
                (conversions, self.conversion_attributes, self.conversion_actions), 
                (storages, self.storage_attributes, self.storage_actions)]
