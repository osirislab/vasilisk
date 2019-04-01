import redis


class CoverageRecorder:
    def __init__(self):
        self.redis = redis.Redis(host='localhost', port=6379, db=0,
                                 decode_responses=True)

    def comb_fmt(self, comb):
        comb_str = 'case:'
        comb_str += 'actions:'
        comb_str += ','.join(comb['actions'])
        comb_str += ';controls:'
        comb_str += ','.join(comb['controls'])
        return comb_str

    def record(self, case):
        self.redis.incr('count')
