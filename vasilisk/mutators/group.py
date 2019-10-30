#!/usr/bin/env python3
import logging
from .base import BaseMutator
from coverage.groups import recorder
from coverage.groups.group import string_to_group, Group
from json import JSONDecodeError, loads
from grammar import 

class GroupMutator(BaseMutator):
    """ This mutator still needs to be integrated into the fuzzer class"""
    def __init__(self, coverage, logger, grammar):
        self.coverage = coverage
        self.logger = logger
        self.grammar = grammar

    def mutate_json_group_string(self, json_string):
        """ mutates a json stringified Group object """
        try:
            group = loads(json_string)
            return self.mutate(group)
        except (JSONDecodeError):
            logger.error("could not mutate group with invalid JSON input")
            return None
    
    def mutate(self, group, feedback):
        """ use feedback from fuzzer to choose an interaction, 
         variable, and action in a specific group"""
         # where is the code to generate concrete test cases from groups
         # do the groups contain grammars or JS

