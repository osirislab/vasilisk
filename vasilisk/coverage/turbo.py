import json
import redis


class TurboCoverage(object):
    def __init__(self):
        self.redis = redis.Redis(host='localhost', port=6379, db=0,
                                 decode_responses=True)
        self.optimizations = self.redis.hgetall('optimizations')
        self.combinations = set(self.redis.smembers('combinations'))

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

    def record(self, grammar):
        print(grammar)


if __name__ == '__main__':
    opt = TurboCoverage()
    print(opt.metrics('/dev/shm/vasilisk_coverage/thread1/turbo-f-0.json'))
