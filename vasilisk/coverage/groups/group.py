import json
import os
import uuid


def string_to_group(json_string):
    store_obj = json.loads(json_string)
    return Group(store_obj['a'], store_obj['v'],
                 store_obj['c'], store_obj['i'])


class Group(object):
    """ Expects a list of tuples in the format (grammar,
    concrete test case, rule)"""
    def __init__(self, actions_to_variables, resolved_variables,
                 controls, interactions):
        self.actions = actions_to_variables
        self.variables = resolved_variables
        self.controls = controls
        self.interactions = interactions
        self.store_dir = os.path.join(
            os.path.abspath(os.path.dirname(__file__)), 'groups'
        )
        if not os.path.exists(self.store_dir):
            os.makedirs(self.store_dir)

    def unpack(self):
        return [self.actions,
                self.variables,
                self.controls,
                self.interactions]

    def pack(self, elements):
        a, v, c, i = elements
        self.actions = a
        self.variables = v
        self.controls = c
        self.interactions = i

    def to_string(self):
        store_obj = {
            'a': self.actions,
            'v': self.variables,
            'c': self.controls,
            'i': self.interactions
        }

        return json.dumps(store_obj)

    def store(self):
        identifier = str(uuid.uuid4())
        with open(os.path.join(self.store_dir, identifier), 'w+') as f:
            f.write(self.to_string())

        return identifier
