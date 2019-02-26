from .dharma import DharmaFuzzer


class OptimizeFuzzer(DharmaFuzzer):
    def __init__(self):
        super().__init__()

    def generate(self):
        """Expects only function named f"""
        input = super().generate()
        input += '\nprint(f());'
        input += '\n%OptimizeFunctionOnNextCall(f);'
        input += '\nprint("optimized output:");'
        input += '\nprint(f());'
        return input

    def validate(self, output):
        values = output.split(b'optimized output:\n')
        return values[0] == values[1]
