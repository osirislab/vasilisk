#!/usr/bin/env python3

import logging
import random

from .base import BaseMutator


class GroupMutator(BaseMutator):
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.interactions = ['+', '-', '/', '*']

    def mutate(self, group):
        actions, variables, controls, interactions = group.unpack()

    def mutate_interactions(self, interactions):
        rand_idx = random.randint(0, len(interactions) - 1)
        interactions[rand_idx] = random.choice(self.interactions)
        return interactions

    def mutate_actions(self, actions):
        pass
