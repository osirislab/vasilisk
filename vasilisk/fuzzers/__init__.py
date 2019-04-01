from .optimize import OptimizeFuzzer
from .probablistic import ProbablisticFuzzer
from .iterative import IterativeFuzzer

fuzzers = {'optimize': OptimizeFuzzer,
           'probabilistic': ProbablisticFuzzer,
           'iterative': IterativeFuzzer}
