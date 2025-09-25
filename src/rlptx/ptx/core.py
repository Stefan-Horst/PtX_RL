from abc import ABC, abstractmethod
from collections.abc import Callable

from rlptx.ptx.framework import PtxSystem

class Element(ABC):
    """Base class for all classes (commodities, components) of the PtX system."""
    
    @abstractmethod
    def apply_action_method(self, method: Callable, ptx_system: PtxSystem, values: tuple) -> bool:
        """Apply the values returned by a specific action method to the element and the ptx system."""
        pass
    
    def get_possible_observation_attributes(self, relevant_attributes):
        """Out of a given list return all strings whose corresponding attributes 
        of the class specified in the observation spec are true."""
        if self.observation_spec == {}:
            return relevant_attributes
        possible_attributes = []
        for attribute in relevant_attributes:
            for k, v in self.observation_spec.items():
                if attribute == k:
                    enabled_flag = v[0]
                    if enabled_flag is None or getattr(self, enabled_flag) == True:
                        possible_attributes.append(attribute)
        return possible_attributes
    
    def get_possible_action_methods(self, relevant_method_tuples):
        """Out of a given list return all methods whose corresponding attributes 
        of the class specified in the observation spec are true."""
        if self.action_spec == {}:
            return relevant_method_tuples
        possible_methods = []
        for method_tuple in relevant_method_tuples:
            for k, v in self.action_spec.items():
                if method_tuple[0] == k:
                    enabled_flag = v[0]
                    if enabled_flag is None or getattr(self, enabled_flag) == True:
                        possible_methods.append(method_tuple)
        return possible_methods
    
    def assert_specs_match_class(self):
        """Assert that the attributes and methods specified in the 
        observation and action specs actually exist in the class."""
        assert self._check_observation_spec_matches_class_attributes(), \
               "Observation spec does not match class attributes."
        assert self._check_action_spec_matches_class_methods_and_attributes(), \
               "Action spec does not match class attributes."
    
    def _check_observation_spec_matches_class_attributes(self):
        match = True
        for attr in [x[0] for x in self.observation_spec.values()] + list(self.observation_spec.keys()):
            if attr is not None and attr not in self.__dict__.keys():
                match = False
                break
        return match
    
    def _check_action_spec_matches_class_methods_and_attributes(self):
        match = True
        for attr in [x[0] for x in self.action_spec.values()]:
            if attr is not None and attr not in self.__dict__.keys():
                match = False
                break
        return match
    