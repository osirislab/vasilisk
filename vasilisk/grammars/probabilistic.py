import logging
import os
import random

from .dharma_grammar import DharmaGrammar


class ProbabilisticGrammar(DharmaGrammar):
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
        self.values = self.parse(os.path.join(templates, 'values.dg'))
        # self.variables = self.parse(os.path.join(templates, 'variables.dg'))
        self.variances = self.parse(os.path.join(templates, 'variances.dg'))

        self.values_probability = {}
        # self.variables_probability = {}
        self.variances_probability = {}

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

    def load_probabilities(self, values, variances):
        self.values_probability = values
        self.variances_probability = variances

    def choice(self, probabilities):
        choice = random.randint(0, sum(probabilities.values()))

        curr = 0
        for rule, probability in probabilities.items():
            curr += probability
            if curr >= choice:
                return rule

    def generate(self):
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

        value = self.choice(self.values_probability)

        with open(self.grammar_path, 'a') as f:
            f.write('%section% := value\n\n')
            f.write(f'value :=\n\t{self.values[value]}\n\n')

        variance = self.choice(self.variances_probability)

        with open(self.grammar_path, 'a') as f:
            f.write('%section% := variance\n\n')
            f.write(f'variance :=\n\t{self.variances[variance]}\n\n')

        # variable = self.choice(self.variables_probability)
        #
        # with open(self.gen_grammar_path, 'a') as f:
        #     f.write('%section := variable\n\n')
        #     f.write(f'{variable} :=\n\t{self.variables[variable]}\n\n')

        self.create_dharma(self.grammars)

        return ((value, variance), super().generate())
