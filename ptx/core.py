from abc import ABC, abstractmethod
from collections.abc import Callable

from ptx.framework import PtxSystem

class Element(ABC):
    """Abstract base class for all classes (commodities, components) of the PtX system."""
    
    @abstractmethod
    def apply_action_method(self, method: Callable, ptx_system: PtxSystem, values: tuple) -> bool:
        """Apply the values returned by a specific action method to the element and the ptx system."""
        pass
    
    @abstractmethod
    def get_possible_observation_attributes(self, relevant_attributes: list[str]) -> list[str]:
        """Out of a given list, return all attributes that can be 
        applied to an object based on its specification."""
        pass
    
    @abstractmethod
    def get_possible_action_methods(self, relevant_methods: list[Callable]) -> list[Callable]:
        """Out of a given list, return all methods that can be 
        applied to an object based on its specified attributes."""
        pass
    