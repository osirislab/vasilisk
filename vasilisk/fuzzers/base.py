import os
import sys

from abc import ABC, abstractmethod


class BaseFuzzer(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def validate(self, output):
        pass

    @abstractmethod
    def fuzz(self, test_case):
        pass

    def create_test(self, test_case, file_name):
        """Takes generated test case and writes to file"""
        with open(os.path.join(self.tests, file_name), 'w+') as f:
            f.write(test_case)

    def commit_test(self, test_case, file_name):
        """Test case valuable, save to logs"""
        self.logger.info('found fuzzing target')

        case_folder = os.path.join(self.crashes, file_name)

        if os.path.exists(case_folder):
            self.logger.error('duplicate case folder')
            sys.exit(1)

        os.mkdir(case_folder)

        dest = os.path.join(case_folder, 'input')
        with open(dest, 'w+') as f:
            f.write(test_case)
