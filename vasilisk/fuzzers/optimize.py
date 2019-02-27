import logging

from .dharma import DharmaFuzzer


class OptimizeFuzzer(DharmaFuzzer):
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        super().__init__()

    def generate(self):
        """Expects only function named f"""
        input = super().generate()
        return input

    def validate(self, output):
        # values = output.split(b'optimized:\n')
        self.logger.debug(output)
        # return values[0] == values[1]
        return True
