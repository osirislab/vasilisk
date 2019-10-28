#!/usr/bin/env/python3
from abc import ABC, abstractmethod

class BaseMutator:
    def __init__(self, coverage_profile):
        """ This mutator still needs to be integrated into the fuzzer class"""
        self.coverage = coverage_profile

    @abstractmethod
    def mutate(self, group):
        pass



