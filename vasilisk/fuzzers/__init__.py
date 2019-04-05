from .optimize import OptimizeFuzzer
from .probablistic import ProbablisticFuzzer
from .iterative import IterativeFuzzer
from .verify import VerifyFuzzer

fuzzers = {'optimize': OptimizeFuzzer,
           'probabilistic': ProbablisticFuzzer,
           'iterative': IterativeFuzzer,
           'verify': VerifyFuzzer}
