import json
import math
import os
import redis


class CoverageRecorder:
    def __init__(self):
        self.redis = redis.Redis(host='localhost', port=6379, db=0,
                                 decode_responses=True)

    def parse(self, turbo_json):
        with open(turbo_json, 'r') as f:
            turbo = json.loads(f.read())

        skip = ['before register allocation', 'after register allocation',
                'schedule', 'effect linearization schedule',
                'select instructions', 'code generation', 'disassembly']

        filtered = {}
        for phase in turbo['phases']:
            name = phase['name']
            if name not in skip:
                filtered[name] = {}
                for node in phase['data']['nodes']:
                    filtered[name][str(node['id'])] = node['title']

        return filtered

    def metrics(self, turbo_json):
        turbo = self.parse(turbo_json)

        differences = {}
        prev = {}
        for phase, nodes in turbo.items():
            if prev:
                differences[phase] = {'changes': 0,
                                      'additions': 0,
                                      'deletions': 0}
                for id, title in nodes.items():
                    if id not in prev:
                        differences[phase]['additions'] += 1
                    elif title != prev[id]:
                        differences[phase]['changes'] += 1

                for id in prev.keys():
                    if id not in nodes:
                        differences[phase]['deletions'] += 1

            prev = nodes

        return differences

    def record(self, grammars, turbo_path):
        turbo_json = os.path.join(turbo_path, 'turbo-f-0.json')
        total = 0
        for changes in self.metrics(turbo_json).values():
            total += sum(changes.values())

        case = 'case:' + ','.join(grammars)
        self.redis.set(case, total)
        self.redis.incr('count')
        cumulative_total = int(self.redis.get('total'))
        self.redis.set('total', str(cumulative_total + total))
        count = int(self.redis.get('count'))
        average = float(cumulative_total) / count

        reward = math.floor(math.sqrt(abs(total - average)))

        value = f'value:{grammars[0]}'
        control = f'control:{grammars[1]}'

        self.redis.set(value, str(int(self.redis.get(value)) + reward))
        self.redis.set(control, str(int(self.redis.get(control)) + reward))
