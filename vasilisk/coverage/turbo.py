import json
import redis


class TurboCoverage(object):
    def __init__(self):
        self.redis = redis.Redis(host='localhost', port=6379, db=0,
                                 decode_responses=True)
        self.optimizations = self.redis.hgetall('optimizations')
        self.combinations = set(self.redis.smembers('combinations'))
        print(self.optimizations)
        print(self.combinations)
        self.misses = 0

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
        combination = []
        for node in nodes:
            if node['id'] in control_ids:
                title = str(node['title'])
                control.append(title)
                if title not in self.optimizations:
                    id = str(len(self.optimizations))
                    self.optimizations[title] = id
                    self.redis.hset('optimizations', title, id)

                combination.append(self.optimizations[title])

        combination = ','.join(combination)

        if combination not in self.combinations:
            self.combinations.add(combination)
            self.redis.sadd('combinations', combination)
            self.misses = 0
        else:
            self.misses += 1

        return control


if __name__ == '__main__':
    opt = TurboCoverage()
    print(opt.parse('turbo-f-0.json'))
