import logging
import os
import sys

from .dharma_grammar import DharmaGrammar


class VerifyGrammar(DharmaGrammar):
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

        self.curr_action = 0

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

    def generate(self):
        if self.curr_action >= len(self.actions.keys()):
            self.logger.info('finished verifying all actions')
            sys.exit(1)

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

        action = list(self.actions.keys())[self.curr_action]

        with open(self.grammar_path, 'a') as f:
            f.write('%section% := value\n\n')
            f.write(self.all_actions)
            f.write(f'\nvalue :=\n\t{self.actions[action]}\n\n')

        control = list(self.controls.keys())[0]

        with open(self.grammar_path, 'a') as f:
            f.write('%section% := variance\n\n')
            f.write(f'variance :=\n\t{self.controls[control]}\n\n')

        self.create_dharma(self.grammars)
        self.curr_action += 1

        return ((action, control), super().generate())
