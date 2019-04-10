import os
import re

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

    def parse_xrefs(self):
        for rule, subrules in self.corpus['actions'].items():
            for subrule in subrules:
                xrefs = self.xref(subrule)
                for xref in xrefs:
                    xref_l = subrule[:xref[0]-1]
                    xref_r = subrule[xref[1]+1:]
                    xref = subrule[xref[0]:xref[1]]
                    replacements = []
                    if ':' in xref:
                        xref_grammar, xref_rule = xref.split(':')
                        xref_subrules = self.corpus[xref_grammar][xref_rule]
                        for xref_subrule in xref_subrules:
                            replacements.append(xref_l + xref_subrule + xref_r)

                    #print(replacements)

    def generate_test(self, grammar_list, name="regexp", path = None):
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
            
            test_case += f"{self.generate(self.corpus[name][rule][index], 'regexp')};"
            print(test_case)
            break

    def generate(self, rule,  grammar, cache = None, recurse_count = 0):
        out, end = [], 0
        if cache is None:
            cache = {}

        for k in cache.items():
            print(k)


        
        if recurse_count == self.max_recursions:
            return False
        
        if rule in cache:
            return cache[rule]

        token = rule.replace("\\n", "\n")
        for m in re.finditer(self.xref_re, token, re.VERBOSE | re.DOTALL):
            if m.start(0) > end:
                end = m.end(0)
            elif m.group("repeat") is not None:
                repeat, separator, nodups = m.group("repeat", "separator", "nodups")
                #print(repeat, separator, nodups)
                if separator is None:
                    separator = ""
                if nodups is None:
                    nodups = ""

                if ":" in separator:
                    grammar = separator.split(":")[0]
                
                for i in range(self.repeat_max):
                    res = self.generate(repeat, grammar, cache, recurse_count + 1)
                    if res:
                        out.append(res)
                    else:
                        # use Roy's code to use another grammar index instead of the
                        # one specified previously
                        pass

                cache[rule] = separator.join(out)
                return cache[rule]

            elif m.group("choices") is not None:
                choices = m.group("choices")
            else:
                if "+" in rule:
                    if ":" in rule:
                        grammar = rule.split(":")[0].strip("+")
                        gramm = rule.split(":")[1].strip("+")
                    else:
                        gramm = rule.strip("+")
                    print(grammar, gramm, self.corpus[grammar][gramm][7] )

                    gramm = self.generate(self.corpus[grammar][gramm][7], grammar, cache, recurse_count + 1)
                else:
                    gramm = rule
                    # have to use Roy's code that covers basic cases and sucessfully
                    # parse and make the grammar assuming it is a nonunique case that won't be passed back
                    pass

                if gramm:
                    cache[rule] = gramm
                    return cache[rule]
                else:
                    # same case as before pick another grammar index in a rule and try again
                    pass
                #startval, endval = m.group("start", "end")
        return out
        
if __name__ == '__main__':
    current_dir = os.path.dirname(os.path.realpath(__file__))
    templates = os.path.join(current_dir, 'templates')

    dependencies = os.path.join(templates, 'dependencies')
    grammar_deps = [
        os.path.join(dependencies, grammar)
        for grammar in os.listdir(os.path.join(dependencies))
    ]

    test_grammars = ["pattern:0"]
    
    actions = os.path.join(templates, 'actions.dg')
    controls = os.path.join(templates, 'controls.dg')
    variables = os.path.join(templates, 'variables.dg')

    grammar = Grammar(grammar_deps + [actions, controls, variables])
    grammar.parse_xrefs()
    
    grammar.generate_test(test_grammars)
