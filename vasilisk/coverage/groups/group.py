import json
import os
import uuid


def string_to_group(json_string):
    store_obj = json.loads(json_string)
    return Group(store_obj['action_vars'], store_obj['vars'],
                 store_obj['controls'], store_obj['interactions'])


class Group(object):
    def __init__(self, actions_to_variables, resolved_variables,
                 controls, interactions):
        self.actions_to_variables = actions_to_variables
        self.variables = resolved_variables
        self.controls = controls
        self.interactions = interactions
        self.store_dir = os.path.join(
            os.path.abspath(os.path.dirname(__file__)), 'groups'
        )
        if not os.path.exists(self.store_dir):
            os.makedirs(self.store_dir)

    def to_string(self):
        store_obj = {
            'action_vars': self.actions_to_variables,
            'vars': self.variables,
            'controls': self.controls,
            'interactions': self.interactions
        }

        return json.dumps(store_obj)

    def store(self):
        identifier = str(uuid.uuid4())
        with open(os.path.join(self.store_dir, identifier), 'w+') as f:
            f.write(self.to_string())

        return identifier