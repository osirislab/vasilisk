from .base import BaseFuzzer


class FileFuzzer(BaseFuzzer):
    def __init__(self):
        pass

    def generate(self):
        """ Generates Test Case From Grammar"""
        with open('test1.js', 'r') as f:
            return f.read()

    def validate(self, output):
        return output == b'Hello World\n'
