from abc import ABC
from abc import abstractmethod

class AIProvider(ABC):
    """Abstract Base class for every AI provider
    Every provider (Gemini, OpenAI, OpenRouter, Claude) must implement this interface,
    and expose `name` and `model` class attributes identifying itself for persistence/logging.
    """

    name : str
    model : str

    @abstractmethod
    def generate(self, prompt : str) -> str:
        """Generate a response from the LLM
        Returns: 
            Raw text response
        """
        raise NotImplementedError