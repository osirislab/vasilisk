#!/usr/bin/env python3
import logging
import os
import subprocess
import sys
import threading
import uuid

from Queue import Queue

from datetime import datetime
from fuzzers.file import Fuzzer
from config import v8_out_path

exitapp = False


class Vasilisk:
    def __init__(self, debug=False):
        self.logger = logging.getLogger(__name__)
        self.crashes = os.path.join(os.getcwd(), 'crashes')
        self.tests = os.path.join(os.getcwd(), 'tests')
        self.d8 = os.path.join(v8_out_path, 'd8')
        self.fuzzer = Fuzzer(os.getcwd())
        self.debug = debug

        self.iterations = 10000
        self.queue = Queue(self.iterations)
        self.procs = 8
        self.threads = []

    def create_test(self, test_case, file_name):
        """Takes generated test case and writes to file"""
        with open(os.path.join(self.tests, file_name), 'w+') as f:
            f.write(test_case)

    def commit_test(self, test_case, file_name):
        """Test case valuable, save to logs"""
        case_folder = os.path.join(self.crashes, file_name)

        if os.path.exists(case_folder):
            self._logger.error('duplicate case folder')
            sys.exit(1)

        os.mkdir(case_folder)

        dest = os.path.join(case_folder, 'input')
        with open(dest, 'w+') as f:
            f.write(test_case)

    def execute(self, test_case):
        return subprocess.check_output(
            [self.d8, '-e', '--allow-natives-syntax', test_case]
        )

    def fuzz(self):
        while not exitapp:
            test_case = self.queue.get()

            if test_case is None:
                break

            file_name = ''

            if self.debug:
                curr_time = datetime.now().strftime('%Y.%m.%d-%H:%M:%S')
                file_name = str(uuid.uuid4()) + '_' + curr_time
                self.create_test(test_case, file_name)

            output = self.execute(test_case)

            if not self.fuzzer.validate(output):
                self.logger.info('found fuzzing target')

                if not file_name:
                    curr_time = datetime.now().strftime('%Y.%m.%d-%H:%M:%S')
                    file_name = str(uuid.uuid4()) + curr_time

                self.commit_test(test_case, curr_time)

            self.queue.task_done()

    def generate(self):
        while not self.queue.full():
            self.queue.put(self.fuzzer.generate())

    def start(self):
        for _ in range(self.procs):
            t = threading.Thread(target=self.fuzz)
            t.daemon = True
            t.start()
            self.threads.append(t)

        self.generate()
        self.logger.info('generated all cases')

        self.queue.join()

        for _ in range(self.procs):
            self.queue.put(None)

        for t in self.threads:
            t.join()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    driver = Vasilisk()
    driver.start()
