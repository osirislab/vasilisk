from abc import ABC, abstractmethod


class BaseGrammar(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def generate(self):
        """Generates Test Case From Grammar"""
        pass
