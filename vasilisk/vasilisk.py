#!/usr/bin/env python3
import logging
import os
import shutil
import subprocess
import sys

from datetime import datetime
from fuzzers.base import Fuzzer
from config import v8_out_path
from glob import glob

class Vasilisk:
    def __init__(self, debug=False):
        self._logger = logging.getLogger(__name__)
        self._input_folder = os.path.join(os.getcwd(), 'input_cases')
        self.d8_command = f"{v8_out_path}d8"
        self._fuzzer = Fuzzer(self._input_folder, self.d8_command)
        self.debug = debug
        
        self.commits = []
        self.deletions = []

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
        self._logger.info(" instrumenting ...  ")
        return self._fuzzer.instrument(test_case);

    def flush(self, cases, action):
        while(len(cases)):
            action(cases.pop()) 

    def destroy(self):
        self.flush(self.commits, self.commit_test)
        if self.debug:
            while(len(self.deletions)):
                shutil.copy(self.deletions.pop(), "/tmp")
        else:
            self.flush(self.deletions, self.delete_test)

    def fuzz(self):
        for case in glob(f"{self._input_folder}/*.js"):
            test_case = self.create_test(self._fuzzer.test(case))
            output = self.instrument(os.path.join(self._input_folder, test_case))

            if not self._fuzzer.validate(output, ""):
                self._logger.info('  found fuzzing target')
                self.commits.append(test_case)
            else:
                self.deletions.append(test_case)
            
            if len(self.commits) % 2**8 == 0:
                self.flush(self.commits, self.commit_test)

            if len(self.deletions) % 2**8 == 0:
                if self.debug:
                    while(len(self.deletions)):
                        shutil.copy(self.deletions.pop(), "/tmp")
                else:
                    self.flush(self.deletions, self.delete_test)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    driver = Vasilisk()
    driver.fuzz()
    driver.destroy()
