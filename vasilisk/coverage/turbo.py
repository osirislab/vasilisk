import json
import os
import redis


class TurboCoverage(object):
    def __init__(self):
        self.redis = redis.Redis(host='localhost', port=6379, db=0,
                                 decode_responses=True)

        if not self.redis.exists('count'):
            self.redis.set('count', 0)

        if not self.redis.exists('average'):
            self.redis.set('average', 0)

        self.count = int(self.redis.get('count'))
        self.average = float(self.redis.get('average'))
        self.cumulative_total = float(self.average * self.count)

    def scan_values(self, grammar):
        for rule in grammar.keys():
            if not self.redis.exists('value:' + rule):
                self.redis.set('value:' + rule, 10)

    def scan_variances(self, grammar):
        for rule in grammar.keys():
            if not self.redis.exists('variance:' + rule):
                self.redis.set('variance:' + rule, 10)

    def get_values(self):
        values = self.redis.scan(match='value:*')[1]
        probabilities = {}
        for value in values:
            rule = value.split('value:')[1]
            probabilities[rule] = int(self.redis.get(value))

        return probabilities

    def get_variances(self):
        variances = self.redis.scan(match='variance:*')[1]
        probabilities = {}
        for variance in variances:
            rule = variance.split('variance:')[1]
            probabilities[rule] = int(self.redis.get(variance))

        return probabilities

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

    def record(self, grammar, turbo_path):
        turbo_json = os.path.join(turbo_path, 'turbo-f-0.json')
        total = 0
        for changes in self.metrics(turbo_json).values():
            total += sum(changes.values())

        case = 'case:' + ','.join(grammar)
        if not self.redis.exists(case):
            self.redis.set(case, total)
            self.redis.incr('count')
            self.count += 1
            self.cumulative_total += total
            self.redis.set('average', self.cumulative_total / self.count)

    def print_records(self):
        print(f'{self.redis.get("count")} cases processed')
        print(f'{self.redis.get("average")} average changes')

        print('-' * 80)
        print('processed cases:')
        cases = self.redis.keys(pattern='case:*')
        for case in cases:
            print(case.split('case:')[1].split(','), self.redis.get(case))

        print('-' * 80)
        print('scores for values:')
        values = self.redis.keys(pattern='value:*')
        for value in values:
            print(value.split('value:')[1], self.redis.get(value))

        print('-' * 80)
        print('scores for variances')
        variances = self.redis.keys(pattern='variance:*')
        for variance in variances:
            print(variance.split('variance:')[1], self.redis.get(variance))


if __name__ == '__main__':
    opt = TurboCoverage()
    opt.print_records()
