#!/usr/bin/env python3
import logging
import os
import shutil
import subprocess
import sys

from datetime import datetime

from fuzzers import test


class Vasilisk:
    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self._input_folder = os.path.join(os.getcwd(), 'input_cases')
        self._fuzzer = test.Fuzzer(self._input_folder)

    def create_test(self, case_string):
        """Takes generated test case and writes to file"""
        current_time = datetime.now().strftime("%Y%m%d-%H%M%S")
        test_case = 'case_' + current_time
        with open(os.path.join(self._input_folder, test_case), 'w+') as f:
            f.write(case_string)

        return test_case

    def commit_test(self, test_case):
        """Test case valuable, save to logs"""
        base_folder = os.path.normpath(os.getcwd() + os.sep + os.pardir)
        logs_folder = os.path.join(base_folder, 'logs')

        if not os.path.exists(logs_folder):
            os.mkdir(logs_folder)

        case_folder = os.path.join(logs_folder, test_case)

        if os.path.exists(case_folder):
            self._logger.error('duplicate case folder')
            sys.exit(1)

        os.mkdir(case_folder)

        src = os.path.join(self._input_folder, test_case)
        dest = os.path.join(case_folder, 'test_case')
        shutil.copyfile(src, dest)

    def delete_test(self, test_case):
        os.remove(os.path.join(self._input_folder, test_case))

    def instrument(self, test_case):
        return subprocess.check_output(["d8", "--print-code", test_case])

    def fuzz(self):
        test_case = self.create_test(self._fuzzer.generate())
        output = self.instrument(os.path.join(self._input_folder, test_case))

        if not self._fuzzer.validate(output):
            self._logger.info('found fuzzing target')
            self.commit_test(test_case)

        self.delete_test(test_case)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    fuzzer = Vasilisk()
    fuzzer.fuzz()
