#!/usr/bin/env python3
import logging
from base import BaseMutator
#from coverage.groups.group import string_to_group, Group
from json import JSONDecodeError, loads

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
        elements = []
        for gs in group.unpack():
            tests = []
            for g,c,r in gs:
                tests.append(g, self.grammar.parse_func(g,r), r)
            elements.append(tests)
        group.pack(elements)

                
