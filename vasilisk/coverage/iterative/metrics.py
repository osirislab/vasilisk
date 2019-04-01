import redis


class CoverageMetrics(object):
    def __init__(self):
        self.redis = redis.Redis(host='localhost', port=6379, db=0,
                                 decode_responses=True)

    def print_records(self):
        pass


if __name__ == '__main__':
    opt = CoverageMetrics()
    opt.print_records()
