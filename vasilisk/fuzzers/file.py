class Fuzzer:
    def __init__(self, input_folder):
        self._input_folder = input_folder

    def generate(self):
        """ Generates Test Case From Grammar"""
        with open('test1.js', 'r') as f:
            return f.read()

    def validate(self, output):
        return output == 'Hello World\n'
