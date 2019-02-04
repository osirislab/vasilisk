import os


class Fuzzer(object):
    def __init__(self, input_folder):
        self._input_folder = input_folder

    def generate(self):
        with open(os.path.join(self._input_folder, 'test1.js'), 'r') as f:
            return f.read()

    def validate(self, output):
        if 'hello world' in output:
            return True

        return False
