import os
import random
import struct

import dharma

from .base import BaseGrammar


class DharmaGrammar(BaseGrammar):
    def __init__(self, grammars):
        random.seed(struct.unpack('q', os.urandom(8))[0])

        settings = open(os.path.join(
            os.path.dirname(os.path.abspath(dharma.__file__)),
            'settings.py'
        ), 'r')

        grammars = [open(grammar, 'r') for grammar in grammars]

        self.dharma = dharma.DharmaMachine()
        self.dharma.process_settings(settings)
        self.dharma.process_grammars(grammars)

        settings.close()

    def generate(self):
        return self.dharma.generate_content()
