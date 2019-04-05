import logging
import os
import random
import time

from coverage.iterative import handler

from .dharma_grammar import DharmaGrammar


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

        self.saved_req = 100

        self.curr_combs = 0

        self.curr_actions = self.get_actions()

        self.actions_pool = []
        self.controls_pool = []

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

    def get_actions(self):
        self.load_rules()
        actions = [0]

        while len(actions) <= self.action_depth:
            yield actions
            actions[0] += 1
            for i in range(len(actions) - 1):
                if actions[i] >= self.action_size:
                    actions[i] = 0
                    actions[i + 1] += 1
            self.curr_combs += 1

            if actions[-1] >= self.action_size:
                actions = [0 for _ in range(len(actions) + 1)]

        yield None

    def generate(self):
        actions = next(self.curr_actions)
        if actions is None:
            while self.coverage.get_count() < self.curr_combs:
                time.sleep(0.5)

            self.coverage.score(self.actions_pool, self.controls_pool,
                                self.action_depth, self.control_depth)
            self.coverage.reset(self.actions_pool, self.controls_pool)
            self.curr_combs = 0

            # if self.coverage.get_saved() > self.saved_req:

            self.curr_actions = self.get_actions()
            actions = next(self.curr_actions)

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

        actions = [self.actions_pool[i] for i in actions]

        with open(self.grammar_path, 'a') as f:
            f.write('%section% := value\n\n')
            f.write(self.all_actions + '\n')
            for i, action in enumerate(actions):
                f.write(f'action{i} :=\n\t{self.actions[action]}\n\n')

            f.write('value :=\n\t')

            for i in range(len(actions)):
                f.write(f'+action{i}+;')

            f.write('\n\n')

        control = list(self.controls.keys())[0]

        with open(self.grammar_path, 'a') as f:
            f.write('%section% := variance\n\n')
            f.write(f'variance :=\n\t{self.controls[control]}\n\n')

        self.create_dharma(self.grammars)

        return ((actions, [control]), super().generate())
