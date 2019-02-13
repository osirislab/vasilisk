import os
import random
import struct

import dharma

from .base import BaseFuzzer


class DharmaFuzzer(BaseFuzzer):
    def __init__(self):
        random.seed(struct.unpack('q', os.urandom(8))[0])

        settings = open(os.path.join(
            os.path.dirname(os.path.abspath(dharma.__file__)), 'settings.py'
        ), 'r')
        grammars = [open(os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            '..', 'grammars', 'canvas2d.dg'
        ), 'r')]

        self.dharma = dharma.DharmaMachine()
        self.dharma.process_settings(settings)
        self.dharma.process_grammars(grammars)

        settings.close()

    def generate(self):
        """Expects only function named f"""
        return self.dharma.generate_content()

    def validate(self, output):
        return True
