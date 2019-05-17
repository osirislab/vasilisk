from .optimize import OptimizeGrammar
from .probabilistic import ProbabilisticGrammar
from .iterative import IterativeGrammar
from .verify import VerifyGrammar
from .grammar import Grammar

grammars = {'optimize': OptimizeGrammar,
            'probabilistic': ProbabilisticGrammar,
            'iterative': IterativeGrammar,
            'verify': VerifyGrammar,
            'groups': Grammar}
