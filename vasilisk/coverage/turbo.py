import json


class TurboCoverage(object):
    def __init__(self):
        pass

    def parse(self, turbo_json):
        with open(turbo_json, 'r') as f:
            turbo = json.loads(f.read())

        bytecode = turbo['phases'][0]['data']
        nodes = bytecode['nodes']
        edges = bytecode['edges']

        control_ids = set([])

        for edge in edges:
            if edge['type'] == 'control':
                control_ids.add(edge['source'])
                control_ids.add(edge['target'])

        control = []
        for node in nodes:
            if node['id'] in control_ids:
                control.append(str(node['title']))

        return control


if __name__ == '__main__':
    opt = TurboCoverage()
    print(opt.parse())
