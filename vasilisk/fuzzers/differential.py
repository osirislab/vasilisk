from .base import BaseFuzzer

import uglipyjs


class DifferentialFuzzer(BaseFuzzer):
    def __init__(self):
        pass

    def generate(self):
        """Expects only function named f"""
        with open('test2.js', 'r') as f:
            input = f.read()

        minified = uglipyjs.compile(input)
        print(minified)
        input += '\nprint(f());'
        input += '\n%OptimizeFunctionOnNextCall(f);'
        input += '\nprint("optimized output:");'
        input += '\nprint(f());'
        return input

    def validate(self, output):
        values = output.split(b'optimized output:\n')
        return values[0] == values[1]
