import logging
import os
import random
import time

from operator import mul
from fractions import Fraction
from functools import reduce

from coverage.iterative import handler

from .dharma_grammar import DharmaGrammar


def nCk(n, k):
    return int(reduce(mul, (Fraction(n-i, i+1) for i in range(k)), 1))


class IterativeGrammar(DharmaGrammar):
    def __init__(self):
        self.logger = logging.getLogger(__name__)

        grammar_dir = os.path.join('/dev/shm', 'vasilisk_grammar')
        if not os.path.exists(grammar_dir):
            self.logger.info('creating coverage dir')
            os.makedirs(grammar_dir)

        self.grammar_path = os.path.join(grammar_dir, 'gen_grammar.dg')
        with open(self.grammar_path, 'w+'):
            pass

        current_dir = os.path.dirname(os.path.realpath(__file__))
        templates = os.path.join(current_dir, 'templates')

        with open(os.path.join(templates, 'actions.dg'), 'r') as f:
            self.all_actions = f.read()

        self.actions = self.parse(os.path.join(templates, 'actions.dg'))
        self.controls = self.parse(os.path.join(templates, 'controls.dg'))

        self.coverage = handler.CoverageHandler()

        self.action_depth = 5
        self.control_depth = 1

        self.action_size = 5
        self.control_size = 1

        self.total_possible = 0
        for i in range(self.action_size):
            self.total_possible += nCk(self.action_size, i)

        total_controls = 0
        for i in range(self.control_size):
            total_controls += nCk(self.control_size, i)

        self.total_possible *= total_controls

        self.curr_comb = 0
        self.curr_actions = []
        self.curr_controls = []
        self.curr_action_depth = 0
        self.curr_control_depth = 0

        self.grammars = [self.grammar_path]
        super().__init__(self.grammars)

    def parse(self, grammar_path):
        with open(grammar_path, 'r') as f:
            grammar_text = f.read()

        grammar_split = [rule.strip() for rule in grammar_text.split('\n\n')]
        rules = {}

        for rule in grammar_split:
            title, subrules = [r.strip() for r in rule.split(':=')]

            subrules = [subrule.strip() for subrule in subrules.split('\n')]
            for i, subrule in enumerate(subrules):
                rules[title + ':' + str(i)] = subrule

        return rules

    def load_rules(self):
        while True:
            self.actions_pool = random.sample(self.actions.keys(),
                                              self.action_size)
            self.controls_pool = random.sample(self.controls.keys(),
                                               self.control_size)

            if self.coverage.unique(self.actions_pool, self.controls_pool):
                break

    def generate(self):
        if self.curr_comb >= self.total_possible:
            while self.coverage.get_count() < self.total_possible:
                time.sleep(0.5)

            self.load_rules()
            self.coverage.reset(self.actions_pool, self.controls_pool)
            self.curr_comb = 0

        changes = True
        while changes:
            for i, action in enumerate(self.curr_actions):
                if action >= self.action_size:
                    for j in range(i):
                        self.curr_actions[j] = 0
                    if i == self.curr_action_depth:
                        self.curr_action_depth += 1
                        self.curr_actions.append(0)
                    else:
                        self.curr_actions[i + 1] += 1
                        break
            changes = False

        headers = [
            '%%% Generated Grammar',
            '%const% VARIANCE_MAX := 1',
            '%const% VARIANCE_TEMPLATE := "function f(){%s} %%DebugPrint(f());'
            '%%OptimizeFunctionOnNextCall(f); %%DebugPrint(f());"',
            '%const% MAX_REPEAT_POWER := 4'
        ]

        with open(self.grammar_path, 'w') as f:
            for header in headers:
                f.write(header + '\n')

            f.write('\n')

        actions = [self.actions[i] for i in self.curr_actions]

        with open(self.grammar_path, 'a') as f:
            f.write('%section% := action\n\n')
            f.write(self.all_actions)
            for i, action in enumerate(actions):
                f.write(f'\naction{i} :=\n\t{actions[action]}\n\n')

        control = list(self.controls.keys())[0]

        with open(self.grammar_path, 'a') as f:
            f.write('%section% := variance\n\n')
            f.write(f'variance :=\n\t{self.controls[control]}\n\n')

        self.create_dharma(self.grammars)

        self.curr_actions[0] += 1

        return ((action, control), super().generate())


if __name__ == '__main__':
    iterative = IterativeGrammar()
    print(iterative.load_rules())
