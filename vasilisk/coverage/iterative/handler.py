import itertools
import math
import redis


class CoverageHandler(object):
    def __init__(self):
        self.redis = redis.Redis(host='localhost', port=6379, db=0,
                                 decode_responses=True)

        if not self.redis.exists('total'):
            self.redis.set('total', 0)

        if not self.redis.exists('saved'):
            self.redis.set('saved', 0)

        self.redis.set('count', 0)

    def comb_fmt(self, actions, controls):
        comb_str = 'comb:'
        comb_str += 'actions:'
        comb_str += ','.join(actions)
        comb_str += ';controls:'
        comb_str += ','.join(controls)
        return comb_str

    def case_fmt(self, actions, controls):
        comb_str = 'case:'
        comb_str += 'actions:'
        comb_str += ','.join(actions)
        comb_str += ';controls:'
        comb_str += ','.join(controls)
        return comb_str

    def store_fmt(self, actions, controls):
        comb_str = 'store:'
        comb_str += 'actions:'
        comb_str += ','.join(actions)
        comb_str += ';controls:'
        comb_str += ','.join(controls)
        return comb_str

    def unique(self, actions, controls):
        curr_comb = self.comb_fmt(actions, controls)
        combs = self.redis.lrange('combinations', 0, -1)
        for comb in combs:
            if curr_comb == comb:
                return False

        return True

    def score(self, actions, controls, action_depth, control_depth):
        totals = {}
        for control in controls:
            for i in range(action_depth):
                for action in itertools.product(actions, repeat=i+1):
                    total = self.redis.get(self.case_fmt(action, [control]))
                    totals[','.join(action)] = int(total)

        scores = {}
        cumulative = 0.0

        for action in actions:
            cumulative += totals[action]
        average = cumulative / len(actions)

        for action in actions:
            scores[action] = math.sqrt(abs(totals[action] - average))

        for i in range(1, action_depth):
            for action in itertools.product(actions, repeat=i+1):
                action_key = ','.join(action)
                prev_action_key = ','.join(action[:-1])
                change = abs(totals[action_key] - totals[prev_action_key])
                scores[action_key] = (scores[prev_action_key] +
                                      math.sqrt(change))

        for action in itertools.product(actions, repeat=len(actions)):
            score = scores[','.join(action)]
            total = float(self.redis.get('total'))
            saved = float(self.redis.get('saved'))
            if saved == 0:
                average = 0
            else:
                average = total / saved
            if score - average >= -1:
                self.redis.set('total', str(total + score))
                self.redis.incr('saved')
                self.redis.set(self.store_fmt(action, controls), score)
                print(action, scores[','.join(action)])

    def reset(self, actions, controls):
        self.redis.rpush('combinations', self.comb_fmt(actions, controls))
        self.redis.set('count', 0)

        for case in self.redis.keys(pattern='case:*'):
            self.redis.delete(case)

    def get_count(self):
        return int(self.redis.get('count'))

    def get_saved(self):
        return int(self.redis.get('saved'))
