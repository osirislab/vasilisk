import redis


class CoverageHandler(object):
    def __init__(self, values, controls):
        self.redis = redis.Redis(host='localhost', port=6379, db=0,
                                 decode_responses=True)

        if not self.redis.exists('count'):
            self.redis.set('count', 0)

        if not self.redis.exists('total'):
            self.redis.set('total', 0)

        self.count = int(self.redis.get('count'))
        self.cumulative_total = self.redis.get('total')
        self.average = 0
        if self.count != 0:
            self.average = float(self.cumulative_total) / self.count

        for rule in values.keys():
            if not self.redis.exists('value:' + rule):
                self.redis.set('value:' + rule, 10)

        for rule in controls.keys():
            if not self.redis.exists('control:' + rule):
                self.redis.set('control:' + rule, 10)

    def get_values(self):
        values = self.redis.keys(pattern='value:*')
        probabilities = {}
        for value in values:
            rule = value.split('value:')[1]
            probabilities[rule] = int(self.redis.get(value))

        return probabilities

    def get_controls(self):
        controls = self.redis.keys(pattern='control:*')
        probabilities = {}
        for control in controls:
            rule = control.split('control:')[1]
            probabilities[rule] = int(self.redis.get(control))

        return probabilities


if __name__ == '__main__':
    opt = CoverageHandler()
    opt.print_records()
