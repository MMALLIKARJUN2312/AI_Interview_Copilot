from abc import ABC
from abc import abstractmethod

class AIProvider(ABC):
    """Abstract Base class for every AI provider
    Every provider (Gemini, OpenAI, OpenRouter, Claude) must implement this interface
    """
    
    @abstractmethod
    def generate(self, prompt : str) -> str:
        """Generate a response from the LLM
        Returns: 
            Raw text response
        """
        raise NotImplementedError