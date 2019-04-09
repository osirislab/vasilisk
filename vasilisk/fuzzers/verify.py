import logging
import subprocess

from .base import BaseFuzzer


class VerifyFuzzer(BaseFuzzer):
    def __init__(self, threads, d8, crashes, tests, debug):
        self.logger = logging.getLogger(__name__)

        self.d8 = d8

    def execute(self, test_case):
        options = ['-e', '--allow-natives-syntax']

        try:
            return subprocess.check_output([self.d8] + options + [test_case])
        except subprocess.CalledProcessError as e:
            self.logger.error(e)
            return None

    def fuzz(self, test_case, thread):
        grammar, test_case = test_case

        output = self.execute(test_case)

        if not self.validate(output):
            self.logger.info(f'invalid rule: {grammar[0]}')
        else:
            self.logger.info(f'valid rule: {grammar[0]}')
            self.logger.info(test_case)

    def validate(self, output):
        if output is not None:
            return True
        return False
