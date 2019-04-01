from .optimize import OptimizeGrammar
from .probabilistic import ProbabilisticGrammar
from .iterative import IterativeGrammar

grammars = {'optimize': OptimizeGrammar,
            'probabilistic': ProbabilisticGrammar,
            'iterative': IterativeGrammar}
