from .optimize import OptimizeGrammar
from .probabilistic import ProbabilisticGrammar
from .iterative import IterativeGrammar
from .verify import VerifyGrammar

grammars = {'optimize': OptimizeGrammar,
            'probabilistic': ProbabilisticGrammar,
            'iterative': IterativeGrammar,
            'verify': VerifyGrammar}
