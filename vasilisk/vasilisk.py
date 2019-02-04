#!/usr/bin/env python3
from config import v8_out_path
import subprocess
from glob import glob

class Driver:
    def __init__(self):
        self.v8_path = v8_out_path
        self.d8_command = f"{v8_out_path}d8"

    def instrument(self, test_case):
        subprocess.check_output([self.d8_command, "--print-code", test_case])

    def fuzz(self):
        for case in glob("input_cases/*.js"):
            self.instrument(case)


if __name__ == "__main__":
    fuzzer = Driver()
    fuzzer.fuzz()
