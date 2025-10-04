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
    def apply_action_method(self, method: Callable, ptx_system: PtxSystem, values: tuple) -> bool:
        """Apply the values returned by a specific action method to the element and the ptx system."""
        pass
    
    def update_tracked_attributes(self, attributes):
        """Track class attributes in a dict and set their values to the 
        difference between the current value and the last tracked value 
        or to the current value if the attribute has not been tracked yet."""
        for attribute in attributes:
            if attribute in self.tracked_attributes:
                # track dictionary value changes in a sub-dict
                if attribute.startswith("[dict]"):
                    attribute = attribute[6:]
                    for name, value in getattr(self, attribute).items():
                        self.tracked_attributes[attribute][name] = \
                            value - self.tracked_attributes[attribute][name]
                else:
                    self.tracked_attributes[attribute] = (getattr(self, attribute) 
                                                          - self.tracked_attributes[attribute])
            else: # start tracking new attribute with current value
                if attribute.startswith("[dict]"):
                    attribute = attribute[6:]
                self.tracked_attributes[attribute] = getattr(self, attribute)
    
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
                    if (isinstance(enabled_flag, bool) and enabled_flag or enabled_flag is None
                        or isinstance(enabled_flag, str) and getattr(self, enabled_flag) == True):
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
    