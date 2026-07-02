from abc import ABC, abstractmethod

class BasePrompt(ABC):
    """Base class for every AI prompt"""
    
    @abstractmethod
    def build(self, **kwargs) -> str:
        """Build the final prompt string"""
        raise NotImplementedError