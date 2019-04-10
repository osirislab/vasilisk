import os
import re

from base import BaseGrammar


class Grammar(BaseGrammar):
    def __init__(self, grammars):
        self.xref_re = r"""(
            (?P<type>\+|!|@)(?P<xref>[a-zA-Z0-9:_]+)(?P=type)|
            %repeat%\(\s*(?P<repeat>.+?)\s*(,\s*"(?P<separator>.*?)")?\s*(,\s*(?P<nodups>nodups))?\s*\)|
            %range%\((?P<start>.+?)-(?P<end>.+?)\)|
            %choice%\(\s*(?P<choices>.+?)\s*\)|
            %unique%\(\s*(?P<unique>.+?)\s*\)
        )"""

        self.corpus = {}

        for grammar in grammars:
            self.corpus[os.path.basename(grammar)] = self.parse(grammar)

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
            if m.group('type'):
                out.append(m.group('xref'))
        return out

    def parse_xrefs(self):
        for name, grammar in self.corpus.items():
            for rule, subrules in grammar.items():
                for subrule in subrules:
                    xrefs = self.xref(subrule)
                    for xref in xrefs:
                        if ':' in xref:
                            xref_grammar, xref_rule = xref.split(':')
                        else:
                            xref_rule = xref

    def generate_test(self, action_list, controls_list = None, variable_list=None):
        """ 
        loads a list of grammars and checks regex to output code
        """
        test_case = ""

        action_rules = self.parse("templates/actions.dg")
        control_rules = self.parse("templates/controls.dg")
        variable_rules = self.parse("templates/variables.dg")

        rules = (
            action_rules,
            control_rules,
            variable_rules
        )

        for action in action_list:
            rule, index = map(lambda x: int(x) if x.isnumeric() else x, 
                    action.split(":"))
            if index > len(action_rules[rule]):
                raise ValueError(f"grammar index is too high for {rule}")
            
            test_case += f"{self.generate(action_rules[rule][index], rules, 'action')}; "
            break


    def generate(self, rule, rules, grammar):
        action, control, variable = rules
        if grammar == "action":
            print(action["regex"])
            print(rule);
        elif grammar == "control":
            pass
        elif grammar == "variable":
            pass
        else:
            raise ValueError("Unknown grammar in generate function")
        
if __name__ == '__main__':
    current_dir = os.path.dirname(os.path.realpath(__file__))
    templates = os.path.join(current_dir, 'templates')

    dependencies = os.path.join(templates, 'dependencies')
    grammar_deps = [
        os.path.join(dependencies, grammar)
        for grammar in os.listdir(os.path.join(dependencies))
    ]

    test_grammars = ["regex:1", "regex:0", "regex:2", "regex:3", "regex:4"]
    grammar = Grammar(grammar_deps)
    grammar.parse_xrefs()
    grammar.generate_test(test_grammars)
