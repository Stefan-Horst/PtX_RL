from abc import ABC, abstractmethod
from collections.abc import Callable

from rlptx.ptx.framework import PtxSystem

class Element(ABC):
    """Base class for all classes (commodities, components) of the PtX system."""
    
    def __init__(self):
        self.observation_spec = {}
        self.action_spec = {}
        self.tracked_attributes = {}
    
    @abstractmethod
    def update_spec(self) -> None:
        """Set or update the observation and action specs for this element."""
        pass
    
    @abstractmethod
    def apply_action_method(self, method: Callable, ptx_system: PtxSystem, values: tuple) -> bool:
        """Apply the values returned by a specific action method to the element and the ptx system."""
        pass
    
    def update_tracked_attributes(self, attributes):
        """Track class attributes in a dict and set their values to a tuple with the 
        current value and the difference between the current value and the last tracked 
        value or also to the current value if the attribute has not been tracked yet. 
        Format: {attribute: (current_value, difference_to_last_value)}."""
        for attribute in attributes:
            if attribute in self.tracked_attributes:
                # track dictionary value changes in a sub-dict
                if attribute.startswith("[dict]"):
                    attribute = attribute[6:]
                    for name, value in getattr(self, attribute).items():
                        difference = value - self.tracked_attributes[attribute][name][0]
                        self.tracked_attributes[attribute][name] = (value, difference) 
                else:
                    difference = getattr(self, attribute) - self.tracked_attributes[attribute][0]
                    self.tracked_attributes[attribute] = (getattr(self, attribute), difference)
            else: # start tracking new attribute with current value
                if attribute.startswith("[dict]"):
                    attribute = attribute[6:]
                    self.tracked_attributes[attribute] = {
                        k: (v, 0) for k, v in getattr(self, attribute).items()
                    }
                else:
                    self.tracked_attributes[attribute] = (getattr(self, attribute), 0)
    
    def get_possible_observation_attributes(self, relevant_attributes):
        """Out of a given list return all strings whose corresponding attributes of the class 
        specified in the observation spec are true or which are not included but exist in the class."""
        possible_attributes = []
        for attribute_name in relevant_attributes:
            attribute = attribute_name.split("]")[-1] # remove prefixes
            handled = False
            for k, v in self.observation_spec.items():
                if attribute == k:
                    enabled_flag = v[0]
                    if self._is_enabled(enabled_flag):
                        possible_attributes.append(attribute_name)
                    handled = True
            if not handled and hasattr(self, attribute):
                possible_attributes.append(attribute_name)
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
                    if self._is_enabled(enabled_flag):
                        possible_methods.append(method_tuple)
        return possible_methods
    
    def _is_enabled(self, enabled_flag):
        """Check if an attribute's or method's enabled flag is enabled."""
        if (
            isinstance(enabled_flag, bool) and enabled_flag 
            or isinstance(enabled_flag, str) and getattr(self, enabled_flag) == True
        ):
            return True
        return False
    
    def assert_specs_match_class(self):
        """Assert that the attributes and methods specified in the 
        observation and action specs actually exist in the class."""
        self._check_observation_spec_matches_class_attributes()
        self._check_action_spec_matches_class_methods_and_attributes()
    
    def _check_observation_spec_matches_class_attributes(self):
        for attr in self.observation_spec.keys():
            assert attr in self.__dict__.keys(), f"Observation '{attr}' does not exist in class."
        for attr in self.observation_spec.values():
            if isinstance(attr[0], str):
                assert attr[0] in self.__dict__.keys(), \
                    f"Observation enabled flag '{attr[0]}' does not exist in class."
            if len(attr) > 1: # if lower and upper bounds exist
                if isinstance(attr[1], list): # handle value lists for dicts
                    for bounds in attr[1]:
                        assert bounds[0] <= bounds[1], \
                            f"Observation spec range of '{attr[0]}' is invalid, lower value must be smaller than upper value."
                else:
                    assert attr[1] <= attr[2], \
                        f"Observation spec range of '{attr[0]}' is invalid, lower value must be smaller than upper value."
    
    def _check_action_spec_matches_class_methods_and_attributes(self):
        for attr in self.action_spec.values():
            if isinstance(attr[0], str):
                assert attr[0] in self.__dict__.keys(), \
                    f"Action enabled flag '{attr[0]}' does not exist in class."
            assert attr[1] <= attr[2], \
                f"Action spec range of '{attr[0]}' is invalid, lower value must be smaller than upper value."
    