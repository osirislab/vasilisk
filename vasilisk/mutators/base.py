#!/usr/bin/env/python3
from abc import ABC, abstractmethod


class BaseMutator(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def mutate(self, group):
        pass
