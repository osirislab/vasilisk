# import os
import random
import redis


class CoverageRecorder:
    def __init__(self):
        self.redis = redis.Redis(host='localhost', port=6379, db=0,
                                 decode_responses=True)

    def case_fmt(self, actions, controls):
        case_str = 'case:'
        case_str += 'actions:'
        case_str += ','.join(actions)
        case_str += ';controls:'
        case_str += ','.join(controls)
        return case_str

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

    def record(self, case, turbo_path):
        # turbo_json = os.path.join(turbo_path, 'turbo-f-0.json')
        # total = 0
        # for changes in self.metrics(turbo_json).values():
        #     total += sum(changes.values())
        total = random.randrange(30, 50)
        actions, controls = case

        for _ in range(len(actions)):
            total += random.randrange(0, 10)

        self.redis.set(self.case_fmt(actions, controls), total)
        self.redis.incr('count')
