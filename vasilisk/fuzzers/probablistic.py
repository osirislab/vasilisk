import datetime
import logging
import os
import subprocess
import uuid

from coverage import turbo

from .base import BaseFuzzer


class ProbablisticFuzzer(BaseFuzzer):
    def __init__(self, thread, d8, crashes, tests, debug):
        self.logger = logging.getLogger(__name__)

        self.d8 = d8
        self.crashes = crashes
        self.tests = tests
        self.debug = debug

        coverage_dir = os.path.join('/dev/shm', 'vasilisk_coverage')
        if not os.path.exists(coverage_dir):
            self.logger.info('creating coverage dir')
            os.makedirs(coverage_dir)

        self.coverage_path = os.path.join(
            coverage_dir, 'thread-{}'.format(thread)
        )
        if not os.path.exists(self.coverage_path):
            self.logger.info('creating thread specific coverage dir')
            os.makedirs(self.coverage_path)

        self.coverage = turbo.TurboCoverage()

    def execute(self, test_case):
        options = ['-e', '--allow-natives-syntax', '--trace-turbo',
                   '--trace-turbo-path', self.coverage_path]

        try:
            return subprocess.check_output([self.d8] + options + [test_case])
        except subprocess.CalledProcessError as e:
            self.logger.error(e)
            return None

    def fuzz(self, test_case):
        unique_id = None
        grammar, test_case = test_case

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

        self.coverage.record(grammar)

    def validate(self, output):
        return True
