import redis


class CoverageMetrics(object):
    def __init__(self):
        self.redis = redis.Redis(host='localhost', port=6379, db=0,
                                 decode_responses=True)

        self.count = int(self.redis.get('count'))
        self.cumulative_total = self.redis.get('total')
        self.average = float(self.cumulative_total) / self.count

    def print_records(self):
        print(f'{self.count} cases processed')
        print(f'{self.average} average changes')

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
        print('scores for controls')
        controls = self.redis.keys(pattern='control:*')
        for control in controls:
            print(control.split('control:')[1], self.redis.get(control))


if __name__ == '__main__':
    opt = CoverageMetrics()
    opt.print_records()
