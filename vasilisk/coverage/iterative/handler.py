import redis


class CoverageHandler(object):
    def __init__(self):
        self.redis = redis.Redis(host='localhost', port=6379, db=0,
                                 decode_responses=True)

        if not self.redis.exists('count'):
            self.redis.set('count', 0)

        self.count = int(self.redis.get('count'))

    def comb_fmt(self, actions, controls):
        comb_str = 'comb:'
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

    def reset(self, actions, controls):
        self.redis.set('count', 0)
        self.redis.rpush('combinations', self.comb_fmt(actions, controls))


if __name__ == '__main__':
    opt = CoverageHandler()
    opt.print_records()
