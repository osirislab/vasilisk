class Fuzzer:
    def __init__(self, input_folder):
        self._input_folder = input_folder

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
