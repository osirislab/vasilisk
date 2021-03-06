import logging
import subprocess
import uuid

from datetime import datetime

from .base import BaseFuzzer


class OptimizeFuzzer(BaseFuzzer):
    def __init__(self, thread, d8, crashes, tests, debug):
        self.logger = logging.getLogger(__name__)

        self.d8 = d8
        self.crashes = crashes
        self.tests = tests
        self.debug = debug

    def execute(self, test_case):
        options = ['-e', '--allow-natives-syntax']

        try:
            return subprocess.check_output([self.d8] + options + [test_case])
        except subprocess.CalledProcessError as e:
            self.logger.error(e)
            return None

    def fuzz(self, test_case):
        unique_id = None

        if self.debug:
            curr_time = datetime.now().strftime('%Y.%m.%d-%H:%M:%S')
            unique_id = str(uuid.uuid4()) + '_' + curr_time
            self.create_test(test_case, unique_id)

        output = self.execute(test_case)

        if not self.validate(output):
            if unique_id is None:
                curr_time = datetime.now().strftime('%Y.%m.%d-%H:%M:%S')
                unique_id = str(uuid.uuid4()) + '_' + curr_time

            self.commit_test(test_case, unique_id)

    def validate(self, output):
        # values = output.split(b'optimized:\n')
        self.logger.debug(output)
        # return values[0] == values[1]
        return True
