from .optimize import OptimizeFuzzer
from .probablistic import ProbablisticFuzzer

fuzzers = {'optimize': OptimizeFuzzer,
           'probabilistic': ProbablisticFuzzer}
