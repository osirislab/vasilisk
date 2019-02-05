import os
import subprocess

class Fuzzer:
    def __init__(self, input_folder, d8_command):
        self._input_folder = input_folder
        self.d8 = d8_command

    def generate(self):
        """ Generates Test Case From Grammar"""
        pass

    def test(self, file_name=None):
        if file_name:
            with open(file_name, 'r') as f:
                return f.read()
        else:
            return self.generate()

    def validate(self, output, preopt_output):
        return output == preopt_output

    def instrument(self, test_case):
        out = subprocess.check_output([self.d8, "--print-code",
            test_case]) 
        print(out.decode())
        return "hello world"
