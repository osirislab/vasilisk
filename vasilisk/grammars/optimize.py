import logging
import os

from .dharma_grammar import DharmaGrammar


class OptimizeGrammar(DharmaGrammar):
    def __init__(self):
        self.logger = logging.getLogger(__name__)

        grammar_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            '..', 'grammars', 'templates'
        )

        grammars = ['grammar.dg', 'semantics.dg']
        super().__init__([os.path.join(grammar_path, g) for g in grammars])
