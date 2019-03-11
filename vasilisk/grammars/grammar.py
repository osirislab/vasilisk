#!/usr/bin/env python3
import logging
import os
import random
import sys


class Grammar():
    def __init__(self):
        self.logger = logging.getLogger(__name__)

        current_dir = os.path.dirname(os.path.realpath(__file__))
        templates = os.path.join(current_dir, 'templates')
        self.gen_grammar_path = os.path.join(current_dir, 'gen_grammar.dg')
        self.values = self.parse(os.path.join(templates, 'values.dg'))
        # self.variables = self.parse(os.path.join(templates, 'variables.dg'))
        self.variances = self.parse(os.path.join(templates, 'variances.dg'))

    def parse(self, grammar_path):
        with open(grammar_path, 'r') as f:
            grammar_text = f.read()

        grammar_split = [rule.strip() for rule in grammar_text.split('\n\n')]
        rules = {}

        for rule in grammar_split:
            rule = [r.strip() for r in rule.split(':=')]

            values = [value.strip() for value in rule[1].split('\n')]
            rules[rule[0]] = values

        return rules

    def choice(self, probabilities):
        sum = 0
        for probability in probabilities.values():
            sum += probability

        if sum != 100:
            self.logger.error('invalid probabilties')
            sys.exit(1)

        choice = random.randint(0, 100)

        curr = 0
        for rule, probability in probabilities.items():
            curr += probability
            if curr >= choice:
                return rule

    def generate(self, values, variables, variances):
        headers = [
            '%%% Generated Grammar',
            '%const% VARIANCE_MAX := 1',
            '%const% VARIANCE_TEMPLATE := "function f(){%s} %%DebugPrint(f()); %%OptimizeFunctionOnNextCall(f); %%DebugPrint(f());"',
            '%const% MAX_REPEAT_POWER := 4'
        ]

        with open(self.gen_grammar_path, 'w') as f:
            for header in headers:
                f.write(header + '\n')

            f.write('\n')

        value = self.choice(values)
        index = 0
        if ':' in value:
            split = value.split(':')
            value = split[0]
            index = int(split[1])

        with open(self.gen_grammar_path, 'a') as f:
            f.write('%section% := value\n\n')
            f.write(f'value :=\n\t{self.values[value][index]}\n\n')

        # variable = self.choice(variables)
        #
        # with open(self.gen_grammar_path, 'a') as f:
        #     f.write('%section := variable\n\n')
        #     f.write(f'{variable} :=\n\t{self.variables[variable]}\n\n')

        variance = self.choice(variances)

        with open(self.gen_grammar_path, 'a') as f:
            f.write('%section% := variance\n\n')
            f.write(f'variance :=\n\t{self.variances[variance][0]}\n\n')


if __name__ == '__main__':
    g = Grammar()
    values = {
        'builtinMath:0': 10,
        'builtinMath:1': 10,
        'builtinMath:2': 10,
        'string': 10,
        'math:0': 10,
        'math:1': 10,
        'math:2': 10,
        'math:3': 10,
        'negative_number': 10,
        'intArgs': 10
    }
    variances = {
        'LanguageConstructs': 100
    }
    g.generate(values, None, variances)
