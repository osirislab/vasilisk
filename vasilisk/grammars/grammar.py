import copy
import itertools
import os
import logging
import random
import re
import time

from collections import Counter

from coverage.groups import handler

from .base import BaseGrammar


class Grammar(BaseGrammar):
    def __init__(self, repeat=4):
        self.logger = logging.getLogger(__name__)

        current_dir = os.path.dirname(os.path.realpath(__file__))
        templates = os.path.join(current_dir, 'templates')

        dependencies = os.path.join(templates, 'dependencies')
        grammar_deps = [
            os.path.join(dependencies, grammar)
            for grammar in os.listdir(os.path.join(dependencies))
        ]

        actions = os.path.join(templates, 'actions.dg')
        controls = os.path.join(templates, 'controls.dg')
        variables = os.path.join(templates, 'variables.dg')

        grammars = grammar_deps + [actions, controls, variables]

        self.xref_re = r'''(
            (?P<type>\+)(?P<xref>[a-zA-Z0-9:_]+)(?P=type)|
            %repeat%\(\s*(?P<repeat>.+?)\s*(,\s*['"](?P<separator>.*?)['"])?\s*(,\s*(?P<nodups>nodups))?\s*\)|
            %range%\((?P<start>.+?)-(?P<end>.+?)\)|
            %choice%\(\s*(?P<choices>.+?)\s*\)|
            %unique%\(\s*(?P<unique>.+?)\s*\)
        )'''

        self.corpus = {}
        self.repeat_max = repeat
        self.repeat_depth = 2
        self.max_group_size = 10

        self.interactions = ['+', '-', '/', '*']

        for grammar in grammars:
            grammar_name = os.path.basename(grammar).replace('.dg', '')
            self.corpus[grammar_name] = self.parse(grammar)

        self.unravel('actions')
        self.unravel('controls')
        self.unravel('variables')

        logging.info('FINISHED UNRAVELING')

        logging.debug('final actions:')
        logging.debug('\n'.join(self.corpus['actions']['regex']))

        logging.debug('final controls:')
        logging.debug('\n'.join(self.corpus['controls']['LanguageConstructs']))

        logging.debug('final variables:')
        logging.debug('\n'.join(self.corpus['variables']['regexptype']))

        self.action_depth = 5
        self.action_size = 5
        self.control_depth = 1
        self.control_size = 1

        self.actions = {}
        self.controls = {}
        self.variables = {}

        self.grammar_cache = {}

        self.actions_pool = []
        self.controls_pool = []
        self.variables_pool = []

        self.curr_action = None
        self.curr_control = None
        self.curr_variable = None

        self.mutate_set = []

        self.load_pools()
        self.load()
        self.coverage = handler.CoverageHandler()

        self.wrapper = ('function f(){{ {} }} %DebugPrint(f());'
                        '%OptimizeFunctionOnNextCall(f);%DebugPrint(f());')

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
            if m.group('type') == '+':
                out.append((m.start('xref'), m.end('xref')))
        return out

    def unresolved_xref(self, grammar, token):
        for match in re.finditer(r'''\+(?P<xref>[a-zA-Z0-9:_]+)\+''', token):
            if ':' not in match.group('xref'):
                rule_l = token[:match.start('xref')]
                rule_r = token[match.end('xref'):]
                token = rule_l + grammar + ':' + match.group('xref') + rule_r

        return token

    def parse_xrefs(self, grammar, subrule, common=False, history=None):
        self.logger.debug('process grammar: %s | %s', grammar, subrule)

        if history is None:
            history = []

        xrefs = self.xref(subrule)
        new_subrules = []

        self.logger.debug('history: %s', str(history))

        if subrule in history:
            self.logger.debug('found in history: %s', str(subrule))
            return []

        if not xrefs:
            return [self.unresolved_xref(grammar, subrule)]

        expanded_rules = []
        rule_parts = []
        prev_end = 0
        for xref_indices in xrefs:
            rule_parts.append(subrule[prev_end:xref_indices[0] - 1])
            rule_parts.append(0)

            xref = subrule[xref_indices[0]:xref_indices[1]]

            if ':' in xref:
                xref_grammar, xref_rule = xref.split(':')
            else:
                xref_grammar, xref_rule = grammar, xref

            xref_subrules = self.corpus[xref_grammar][xref_rule]
            self.logger.debug('xref_subrules: %s | %s',
                              xref_rule, xref_subrules)

            if not common and xref_grammar == 'common':
                parsed_subrules = ['+' + xref + '+']
            else:
                parsed_subrules = []
                for xref_subrule in xref_subrules:
                    parsed_subrules += self.parse_xrefs(
                        xref_grammar, xref_subrule, common, history + [subrule]
                    )

            self.logger.debug('parsed_subrules: %s', parsed_subrules)

            expanded_rules.append(parsed_subrules)

            prev_end = xref_indices[1] + 1

        rule_parts.append(subrule[xref_indices[1] + 1:])
        rule_fmt = ''
        for part in rule_parts:
            if part == 0:
                rule_fmt += '{}'
            else:
                if '{' in part:
                    part = part.replace('{', '{{')

                if '}' in part:
                    part = part.replace('}', '}}')

                rule_fmt += part

        self.logger.debug('expanded_rules: %s', expanded_rules)
        products = itertools.product(*expanded_rules)

        for product in products:
            new_rule = rule_fmt.format(*product)
            new_rule = self.unresolved_xref(grammar, new_rule)
            new_subrules.append(new_rule)

        self.logger.debug('result: %s | %s', grammar, new_subrules)
        return new_subrules

    def unravel(self, grammar):
        for rule, subrules in self.corpus[grammar].items():
            cumulative_subrules = []
            for subrule in subrules:
                new_subrules = self.parse_xrefs(grammar, subrule)
                # print(new_subrules)

                if new_subrules:
                    cumulative_subrules += new_subrules
                else:
                    cumulative_subrules.append(subrule)

            self.corpus[grammar][rule] = cumulative_subrules

    def parse_func(self, grammar, rule, history=None):
        if history is None:
            history = {}

        m = re.search(self.xref_re, rule, re.VERBOSE | re.DOTALL)

        if not m:
            return rule

        if m.group('repeat') is not None:
            repeat, separator, nodups = m.group('repeat', 'separator',
                                                'nodups')

            if separator is not None:
                end = m.end('separator') + 1
            elif nodups is not None:
                end = m.end('nodups')
            else:
                end = m.end('repeat')

            if separator is None:
                separator = ''

            xrefs = self.parse_xrefs(grammar, repeat, True)
            out = []
            repeat_power = random.randint(1, self.repeat_max)
            if repeat not in history:
                history[repeat] = 0
            history[repeat] += 1

            no_repeats = []
            for no_repeat, count in history.items():
                if count >= self.repeat_depth:
                    no_repeats.append(no_repeat)

            search_space = len(xrefs)
            for i in range(repeat_power):
                xref = random.choice(xrefs)

                invalid = True
                count = 0
                while invalid:
                    if count > search_space:
                        break

                    invalid = False
                    for no_repeat in no_repeats:
                        if no_repeat in xref:
                            invalid = True
                            xref = random.choice(xrefs)
                            count += 1
                            break

                out.append(xref)

            result = separator.join(out)

            rule_l = rule[:m.start('repeat') - 1 - len('%repeat%')]
            rule_r = rule[end + 1:]
            result = rule_l + result + rule_r

            return self.parse_func(grammar, result, history)

        if m.group('unique') is not None:
            unique = m.group('unique')
            xrefs = self.parse_xrefs(grammar, unique, True)
            size = random.randint(1, len(xrefs))
            possible = list(itertools.combinations(xrefs, r=size))
            rule_l = rule[:m.start('unique') - 1].replace('%unique%', '')
            rule_r = rule[m.end('unique') + 1:]
            result = rule_l + ''.join(random.choice(possible)) + rule_r

            return self.parse_func(grammar, result, history)

        if m.group('start') is not None and m.group('end') is not None:
            b_range = m.group('start')
            e_range = m.group('end')
            result = ''

            if b_range.isalpha():
                result = chr(random.randint(ord(b_range), ord(e_range)))
            else:
                result = str(random.randint(int(b_range), int(e_range)))

            rule_l = rule[:rule.index('%range%')]
            rule_r = rule[rule.index('%range%'):]
            rule_r = rule_r[rule_r.index(')') + 1:]
            result = rule_l + result + rule_r

            return self.parse_func(grammar, result, history)

        if m.group('type') == '+':
            xref = rule[m.start('xref') - 1:m.end('xref') + 1]
            if 'common' in xref:
                expanded = random.choice(
                    self.parse_xrefs(grammar, xref, True)
                )

                rule_l = rule[:m.start('xref') - 1]
                rule_r = rule[m.end('xref') + 1:]
                result = rule_l + expanded + rule_r

                return self.parse_func(grammar, result, history)

    def load_cache(self, grammar, rules):
        '''
        loads a list of grammars and checks regex to output code
        '''
        logging.debug('loading %s:%s into cache', grammar, rules)
        self.grammar_cache[grammar] = {}

        for rule in rules:
            rule_name, index = rule.split(':')
            subrule = self.corpus[grammar][rule_name][int(index)]

            self.grammar_cache[grammar][rule] = self.parse_func(grammar,
                                                                subrule)

    def load_pools(self):
        for rule, subrules in self.corpus['actions'].items():
            for i, subrule in enumerate(subrules):
                self.actions[f'{rule}:{i}'] = subrule
        for rule, subrules in self.corpus['controls'].items():
            for i, subrule in enumerate(subrules):
                self.controls[f'{rule}:{i}'] = subrule

    def find_variables(self, actions):
        variable_count = Counter()
        for action in actions:
            rule, index = action.split(':')
            token = self.corpus['actions'][rule][int(index)]
            variable_regex = r'''\!(?P<xref>[a-zA-Z0-9:_]+)\!'''

            for match in re.finditer(variable_regex, token):
                variable_count[match.group('xref')] += 1

        return variable_count

    def load_variables(self, actions):
        variable_count = self.find_variables(actions)

        variables = []
        for variable, count in variable_count.items():
            self.logger.debug('Variable %s with count %s', variable, count)
            pool = self.corpus['variables'][variable]
            count = min(count, len(pool))
            count = random.randint(1, count)
            selections = random.sample(range(len(pool)), count)
            for selection in selections:
                variables.append(variable + ':' + str(selection))

        return variables

    def load(self):
        self.actions_pool = random.sample(self.actions.keys(),
                                          self.action_size)
        self.controls_pool = random.sample(self.controls.keys(),
                                           self.control_size)
        self.variables_pool = self.load_variables(self.actions_pool)

        self.load_cache('actions', self.actions_pool)
        self.load_cache('controls', self.controls_pool)
        self.load_cache('variables', self.variables_pool)

        self.curr_actions = self.iterate_rules(self.action_depth,
                                               self.action_size)
        self.curr_controls = self.iterate_rules(self.control_depth,
                                                self.control_size)

        self.curr_action = next(self.curr_actions)
        self.curr_control = next(self.curr_controls)
        self.curr_variable = self.iterate_variables()

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

    def iterate_variables(self):
        if self.curr_action is None:
            return None

        actions = [self.actions_pool[i] for i in self.curr_action]
        variable_count = self.find_variables(actions)

        variables = {}
        for variable in self.variables_pool:
            name, _ = variable.split(':')
            if name not in variables:
                variables[name] = []
            variables[name].append(variable)

        result = []
        for variable, count in variable_count.items():
            count = random.randint(1, count)
            for _ in range(count):
                result.append(random.choice(variables[variable]))

        return result

    def mutate(self, group):
        return self.build_group(group)

    def mutate_interactions(self, interactions):
        rand_idx = random.randint(0, len(interactions) - 1)
        interactions[rand_idx] = random.choice(self.interactions)
        return interactions

    def mutate_actions(self, actions):
        # new_action = random.choice(self.actions.keys())
        pass

    def mutate_variables(self, variables):
        pass

    def build_group(self, group):
        actions, variables, controls, interactions = group.unpack()
        lines = []

        for name, variable in variables.items():
            lines.append(f'var {name}={variable}')

        for action, choice in actions:
            action_template = self.grammar_cache['actions'][action]
            variable_regex = r'''\!(?P<xref>[a-zA-Z0-9:_]+)\!'''
            m = re.search(variable_regex, action_template)
            if not m:
                logging.debug(action, action_template)
            rule = m.group('xref')
            lines.append(action_template.replace(f'!{rule}!', choice))

        equation = '{}'.join(variables.keys()).format(*interactions)
        lines.append('var result=' + equation)

        controls_fmt = []
        for control in controls:
            controls_fmt.append(control.replace('#actions#', '{}'))

        control_wrapper = '{}'
        for control in controls_fmt:
            control_wrapper = control_wrapper.format(control)

        control_wrapper = control_wrapper.format(';'.join(lines))

        result = self.wrapper.format(control_wrapper)
        return f"'{result}'"

    def generate(self):
        if self.mutate_set:
            return self.mutate(self.mutate_set.pop())
        # Generate new variables everytime we iterate actions
        # Run out of actions, do it again with next control
        # Run out of controls, reload
        if self.curr_action is None:
            self.curr_actions = self.iterate_rules(self.action_depth,
                                                   self.action_size)
            self.curr_action = next(self.curr_actions)
            self.curr_variable = self.iterate_variables()
            self.curr_control = next(self.curr_controls)
            if self.curr_control is None:
                self.logger.info('Finish Generation')
                while not self.coverage.up_to_date():
                    self.logger.debug(self.coverage.redis.get('processed'))
                    self.logger.debug(self.coverage.redis.get('generated'))
                    time.sleep(0.5)
                self.load()
                self.coverage.reset()
                self.logger.info('New Set')
                if self.coverage.get_num_interesting() == 10000:
                    self.mutate_set = self.coverage.get_most_interesting()

        actions = [self.actions_pool[i] for i in self.curr_action]
        controls = [self.grammar_cache['controls'][self.controls_pool[i]]
                    for i in self.curr_control]

        lines = []
        assigned_variables = {}
        resolved_variables = {}
        variable_list = []
        for i, variable in enumerate(self.curr_variable):
            rule = variable.split(':')[0]
            if rule not in assigned_variables:
                assigned_variables[rule] = []
            curr_var = f'var{i}'

            assigned_variables[rule].append(curr_var)
            variable_list.append(curr_var)
            resolved = self.grammar_cache['variables'][variable]
            resolved_variables[curr_var] = variable
            lines.append(f'var {curr_var}={resolved}')

        random.shuffle(actions)
        assigned_variables_copy = copy.deepcopy(assigned_variables)
        actions_to_variables = {}
        for action in actions:
            resolved = self.grammar_cache['actions'][action]
            variable_regex = r'''\!(?P<xref>[a-zA-Z0-9:_]+)\!'''
            m = re.search(variable_regex, resolved)
            if not m:
                self.logger.debug(action, resolved)
            rule = m.group('xref')
            if assigned_variables[rule]:
                choice = assigned_variables[rule].pop()
            else:
                choice = random.choice(assigned_variables_copy[rule])

            actions_to_variables[action] = choice
            lines.append(resolved.replace(f'!{rule}!', choice))

        equation = '{}'.join(variable_list)
        interactions = []
        for _ in range(len(variable_list) - 1):
            interactions.append(random.choice(self.interactions))
        equation = equation.format(*interactions)
        lines.append('var result=' + equation)

        controls_fmt = []
        for control in controls:
            controls_fmt.append(control.replace('#actions#', '{}'))

        control_wrapper = '{}'
        for control in controls_fmt:
            control_wrapper = control_wrapper.format(control)

        control_wrapper = control_wrapper.format(';'.join(lines))

        result = self.wrapper.format(control_wrapper)
        result = "'" + result + "'"

        id = ';'.join([':'.join(map(str, self.curr_action)),
                       ':'.join(map(str, self.curr_control))])
        final = len(self.curr_action) == self.action_depth
        self.coverage.store(id, actions_to_variables, resolved_variables,
                            controls, interactions, final)

        self.curr_action = next(self.curr_actions)
        self.curr_variable = self.iterate_variables()

        return (id, result)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    grammar = Grammar()
    start_time = time.time()
    for _ in range(100000):
        print(grammar.generate())

    print('took :{} seconds'.format(time.time() - start_time))
