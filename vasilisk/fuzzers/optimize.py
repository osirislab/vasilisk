from .base import BaseFuzzer


class OptimizeFuzzer(BaseFuzzer):
    def __init__(self):
        pass

    def generate(self):
        """Expects only function named f"""
        with open('test2.js', 'r') as f:
            input = f.read()
        input += '\nconsole.log(f());'
        input += '\n%OptimizeFunctionOnNextCall(f);'
        input += '\nconsole.log("optimized output:");'
        input += '\nconsole.log(f());'
        return input

    def validate(self, output):
        values = output.split(b'optimized output:\n')
        return values[0] == values[1]
