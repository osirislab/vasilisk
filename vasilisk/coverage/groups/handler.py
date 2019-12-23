import os
import redis
import subprocess

from collections import Counter

from .group import Group
from .group import string_to_group


class CoverageHandler(object):
    def __init__(self):
        self.redis = redis.Redis(host='localhost', port=6379, db=0,
                                 decode_responses=True)

        self.redis.set('generated', 0)
        self.redis.set('processed', 0)

    def reset(self):
        self.redis.set('generated', 0)
        self.redis.set('processed', 0)

        scores = Counter()
        for id in self.redis.lrange('finals', 0, -1):
            scores[id] = self.redis.get(f'score:{id}')

        for id, score in scores.most_common(100):
            self.redis.set(f'i_group:{id}', self.redis.get(f'group:{id}'))
            self.redis.set(f'i_score:{id}', self.redis.get(f'score:{id}'))
            self.redis.lpush('interesting', id)

        while True:
            id = self.redis.lpop('finals')
            if not id:
                break
            self.redis.delete(f'group:{id}')
            self.redis.delete(f'score:{id}')

        self.condense_profraw()

    def up_to_date(self):
        if self.redis.get('generated') == self.redis.get('processed'):
            return True
        return False

    def store(self, id, actions, resolved_variables,
              controls, interactions, final=False):
        self.redis.incr('generated')
        if final:
            group = Group(actions, resolved_variables,
                          controls, interactions)
            self.redis.lpush('finals', id)
            self.redis.set(f'group:{id}', group.to_string())

    def store_group(self, group):
        self.redis.incr('generated')
        self.redis.lpush('mutate', group.to_string())

    def get_most_interesting(self):
        scores = Counter()
        for id in self.redis.lrange('interesting', 0, -1):
            scores[id] = self.redis.get(f'i_score:{id}')

        interesting = []
        for id, score in scores.most_common(100):
            interesting.append(
                string_to_group(self.redis.get(f'i_group:{id}')))

        while True:
            id = self.redis.lpop('interesting')
            if not id:
                break
            self.redis.delete(f'i_group:{id}')
            self.redis.delete(f'i_score:{id}')

        return interesting

    def get_num_interesting(self):
        return self.redis.llen('interesting')

    def condense_profraw(self):
        coverage_folder = os.path.join(os.getcwd(), 'coverage_data')
        for file in os.listdir(coverage_folder):
            if not os.isfile(os.path.join(coverage_folder, file)):
                continue
            if file == 'vasilisk.profdata':
                continue
            cmd = ['llvm-profdata', 'merge', 'vasilisk.profdata']
            cmd.append(file)
            cmd += ['-o', 'vasilisk.profdata']
            try:
                subprocess.call(cmd)
            except Exception:
                pass
            os.remove(os.path.join(coverage_folder, file))
