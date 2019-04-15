import itertools
import os
import random
import re
import time

# from coverage.iterative import handler

from base import BaseGrammar


class Grammar(BaseGrammar):
    def __init__(self, grammars, repeat=4):
        self.xref_re = r"""(
            (?P<type>\+|!|@)(?P<xref>[a-zA-Z0-9:_]+)(?P=type)|
            %repeat%\(\s*(?P<repeat>.+?)\s*(,\s*"(?P<separator>.*?)")?\s*(,\s*(?P<nodups>nodups))?\s*\)|
            %range%\((?P<start>.+?)-(?P<end>.+?)\)|
            %choice%\(\s*(?P<choices>.+?)\s*\)|
            %unique%\(\s*(?P<unique>.+?)\s*\)
        )"""

        self.corpus = {}
        self.repeat_max = repeat
        self.max_recursions = 100000

        for grammar in grammars:
            grammar_name = os.path.basename(grammar).replace('.dg', '')
            self.corpus[grammar_name] = self.parse(grammar)

        self.action_depth = 5
        self.action_size = 5
        self.control_depth = 1
        self.control_size = 1
        self.variable_depth = 1
        self.variable_size = 1

        self.actions = {}
        self.controls = {}
        self.variables = {}

        self.grammar_cache = {}

        self.actions_pool = []
        self.controls_pool = []
        self.variables_pool = []

        self.load_pools()
        self.load()

        # self.coverage = handler.CoverageHandler()

        self.wrapper = ('function f(){{ {} }} %%DebugPrint(f());'
                        '%%OptimizeFunctionOnNextCall(f);%%DebugPrint(f());"')

    def parse(self, grammar):
        with open(grammar, 'r') as f:
            grammar_text = f.read()

        grammar_split = [rule.strip() for rule in grammar_text.split('\n\n')]
        rules = {}

        for rule in grammar_split:
            if ':=' not in rule:
                continue

            title, subrules = [r.strip() for r in rule.split(':=')]

            rules[title] = []
            subrules = [subrule.strip() for subrule in subrules.split('\n')]
            for subrule in subrules:
                rules[title].append(subrule)

        return rules

    def xref(self, token):
        out = []
        for m in re.finditer(self.xref_re, token, re.VERBOSE | re.DOTALL):
            if m.group('type') and m.group('type') != '!':
                out.append((m.start('xref'), m.end('xref')))
        return out

    def parse_xref(self, grammar, xref, common=False):
        #print(grammar, xref)
        if ':' in xref:
            xref_grammar, xref_rule = xref.split(':')
            if not common and xref_grammar == 'common':
                return [xref]
        else:
            xref_grammar, xref_rule = grammar, xref

        xref_subrules = self.corpus[xref_grammar][xref_rule]
        #print('i found these subrules', xref_subrules)
        new_subrules = []
        for xref in xref_subrules:
            inner_xrefs = self.xref(xref)
            if not inner_xrefs:
                new_subrules.append(xref)

            for inner_xref in inner_xrefs:
                inner_xref = xref[inner_xref[0]:inner_xref[1]]
                new_subrules += self.parse_xref(xref_grammar, inner_xref, common)

        return new_subrules

    def parse_xrefs(self, grammar, subrule):
        xrefs = self.xref(subrule)
        new_subrules = []

        if not xrefs:
            return [subrule]

        expanded_rules = []
        rule_parts = []
        prev_end = 0
        for xref in xrefs:
            rule_parts.append(subrule[prev_end:xref[0]-1])
            rule_parts.append('{}')

            xref_str = subrule[xref[0]:xref[1]]
            expanded_rules.append(self.parse_xref(grammar, xref_str))

            prev_end = xref[1] + 1

        rule_parts.append(subrule[xref[1] + 1:])

        products = itertools.product(*expanded_rules)

        for product in products:
            new_subrules.append(''.join(rule_parts).format(*product))

        return new_subrules

    def unravel(self):
        for rule, subrules in self.corpus['actions'].items():
            cumulative_subrules = []
            for subrule in subrules:
                new_subrules = self.parse_xrefs('actions', subrule)

                if new_subrules:
                    cumulative_subrules += new_subrules
                else:
                    cumulative_subrules.append(subrule)

            self.corpus['actions'][rule] = cumulative_subrules

        with open('/tmp/test.dg', 'w+') as f:
            for rule, subrules in self.corpus['actions'].items():
                f.write(f'{rule} :=\n')
                for subrule in subrules:
                    f.write(f'\t{subrule}\n')
                f.write('\n')

    def generate_test(self, grammar_list, name="regexp", path=None):
        """
        loads a list of grammars and checks regex to output code
        """
        if name not in self.corpus:
            self.corpus[name] = self.parse(path)

        test_case = ""

        for grammar in grammar_list:
            rule, index = map(lambda x: int(x) if x.isnumeric() else x,
                              grammar.split(":"))
            if index > len(self.corpus[name][rule]):
                raise ValueError(f"grammar index is too high for {rule}")

            self.grammar_cache[rule] = self.parse_func(name, self.corpus[name][rule][index])
            print(self.grammar_cache[rule])
            break

    def parse_func(self, grammar, rule, recurse_count=0):
        if recurse_count == self.max_recursions:
            return False

        for m in re.finditer(self.xref_re, rule, re.VERBOSE | re.DOTALL):
            if m.group("repeat") is not None:
                repeat, separator, nodups = m.group("repeat", "separator", "nodups")
                if separator is None:
                    separator = ""
                if nodups is None:
                    nodups = ""

                repeat = repeat[1:-1]
                xrefs = self.parse_xref(grammar, repeat, common=True)
                out = []
                repeat_power = random.randint(1, self.repeat_max)
                for i in range(repeat_power): 
                    out.append(self.parse_func(grammar, random.choice(xrefs), recurse_count + 1))
                        # use Roy's code to use another grammar index instead of the
                        # one specified previously

                return separator.join(out)

            elif m.group("choices") is not None:
                choices = m.group("choices")
                # None of our grammars should hit this case yet

            elif m.group("unique") is not None:
                unique = m.group("unique").strip("+")
                xrefs = self.parse_xref(grammar, unique, common=True)
                return xrefs[0];

            elif m.group("start") is not None and m.group("end") is not None:
                b_range = m.group("start")
                e_range = m.group("end")
                if b_range.isalpha():
                    return chr(random.randint(ord(b_range), ord(e_range)))
                return str(random.randint(int(b_range), int(e_range)))

        return rule

    def load_pools(self):
        for rule, subrules in self.corpus['actions'].items():
            for i, subrule in enumerate(subrules):
                self.actions[f'{rule}:{i}'] = subrule
        for rule, subrules in self.corpus['controls'].items():
            for i, subrule in enumerate(subrules):
                self.controls[f'{rule}:{i}'] = subrule
        for rule, subrules in self.corpus['variables'].items():
            for i, subrule in enumerate(subrules):
                self.variables[f'{rule}:{i}'] = subrule

    def load(self):
        while True:
            self.actions_pool = random.sample(self.actions.keys(),
                                              self.action_size)
            self.controls_pool = random.sample(self.controls.keys(),
                                               self.control_size)
            self.variables_pool = random.sample(self.variables.keys(),
                                                self.variable_size)
            # if self.coverage.unique(self.actions_pool, self.controls_pool):
            #     break
            break

        self.curr_actions = self.iterate_rules(self.action_depth,
                                               self.action_size)
        self.curr_controls = self.iterate_rules(self.control_depth,
                                                self.control_size)
        self.curr_variables = self.iterate_rules(self.variable_depth,
                                                 self.variable_size)

        self.curr_action = next(self.curr_actions)
        self.curr_control = next(self.curr_controls)
        self.curr_variable = next(self.curr_variables)

    def iterate_rules(self, depth, size):
        rules = [0]

        while len(rules) <= depth:
            yield rules
            rules[0] += 1
            for i in range(len(rules) - 1):
                if rules[i] >= size:
                    rules[i] = 0
                    rules[i + 1] += 1

            if rules[-1] >= size:
                rules = [0 for _ in range(len(rules) + 1)]

        yield None

    def generate(self):
        if self.curr_action is None:
            self.curr_actions = self.iterate_rules(self.action_depth,
                                                   self.action_size)
            self.curr_action = next(self.curr_actions)
            self.curr_control = next(self.curr_controls)
            if self.curr_control is None:
                self.curr_controls = self.iterate_rules(self.control_depth,
                                                        self.control_size)
                self.curr_control = next(self.curr_controls)
                self.curr_variable = next(self.curr_variables)
                if self.curr_variable is None:
                    # while self.coverage.get_count() < self.curr_combs:
                    #     time.sleep(0.5)
                    #
                    # self.coverage.score(self.actions_pool, self.controls_pool,
                    #                     self.action_depth, self.control_depth)
                    # self.coverage.reset(self.actions_pool, self.controls_pool)
                    self.curr_combs = 0
                    self.load()

        actions = [self.actions[self.actions_pool[i]]
                   for i in self.curr_action]
        controls = [self.controls[self.controls_pool[i]]
                    for i in self.curr_control]
        variables = [self.variables[self.variables_pool[i]]
                     for i in self.curr_variable]

        lines = []
        for i, variable in enumerate(variables):
            lines.append(f'var var{i} = {variable}')
        lines += actions
        for control in controls:
            lines.append(control)

        self.curr_action = next(self.curr_actions)

        return self.wrapper.format(';'.join(lines) + ';')


if __name__ == '__main__':
    current_dir = os.path.dirname(os.path.realpath(__file__))
    templates = os.path.join(current_dir, 'templates')

    dependencies = os.path.join(templates, 'dependencies')
    grammar_deps = [
        os.path.join(dependencies, grammar)
        for grammar in os.listdir(os.path.join(dependencies))
    ]

    test_grammars = ["flags:0"]

    actions = os.path.join(templates, 'actions.dg')
    controls = os.path.join(templates, 'controls.dg')
    variables = os.path.join(templates, 'variables.dg')

    grammar = Grammar(grammar_deps + [actions, controls, variables])
    print(grammar.generate_test(test_grammars))
    # grammar.unravel()
    #print(grammar.generate())
