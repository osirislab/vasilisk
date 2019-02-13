from .file import FileFuzzer
from .optimize import OptimizeFuzzer
from .differential import DifferentialFuzzer
from .dharma import DharmaFuzzer

fuzzers = {'file': FileFuzzer,
           'optimize': OptimizeFuzzer,
           'differential': DifferentialFuzzer,
           'dharma': DharmaFuzzer}
