from .optimize import OptimizeFuzzer
from .probablistic import ProbablisticFuzzer
from .iterative import IterativeFuzzer
from .verify import VerifyFuzzer
from .group import GroupFuzzer

fuzzers = {'optimize': OptimizeFuzzer,
           'probabilistic': ProbablisticFuzzer,
           'iterative': IterativeFuzzer,
           'verify': VerifyFuzzer,
           'groups': GroupFuzzer}
