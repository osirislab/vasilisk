#!/usr/bin/env python3
import logging
import os
import subprocess
import sys
import time
import uuid

import click

from datetime import datetime
from multiprocessing import Process, JoinableQueue

from coverage import turbo
import fuzzers


class Vasilisk:
    def __init__(self, fuzzer, d8, procs, count,
                 crashes, tests, debug, turbo_coverage):
        self.logger = logging.getLogger(__name__)
        self.crashes = crashes
        self.tests = tests
        self.d8 = d8

        self.fuzzer = fuzzers.fuzzers[fuzzer]()
        self.debug = debug

        self.coverage = None
        self.coverage_dir = os.path.join('/dev/shm', 'vasilisk_coverage')
        if not os.path.exists(self.coverage_dir):
            self.logger.info('creating coverage dir')
            os.makedirs(self.coverage_dir)

        if turbo_coverage:
            self.coverage = turbo.TurboCoverage()

        self.count = count
        self.queue = JoinableQueue(self.count)
        self.procs = procs
        self.threads = []

        if not os.path.exists(self.crashes):
            self.logger.error('crashes folder does not exist')
            sys.exit(1)

        if not os.path.exists(self.tests):
            os.makedirs(self.tests)

    def create_test(self, test_case, file_name):
        """Takes generated test case and writes to file"""
        with open(os.path.join(self.tests, file_name), 'w+') as f:
            f.write(test_case)

    def commit_test(self, test_case, unique_id=None):
        """Test case valuable, save to logs"""
        self.logger.info('found fuzzing target')

        if unique_id is None:
            unique_id = uuid.uuid4()

        curr_time = datetime.now().strftime('%Y.%m.%d-%H:%M:%S')
        file_name = str(unique_id) + curr_time

        case_folder = os.path.join(self.crashes, file_name)

        if os.path.exists(case_folder):
            self.logger.error('duplicate case folder')
            sys.exit(1)

        os.mkdir(case_folder)

        dest = os.path.join(case_folder, 'input')
        with open(dest, 'w+') as f:
            f.write(test_case)

    def execute(self, test_case, coverage_path=None, unique_id=None):
        options = ['-e', '--allow-natives-syntax']
        if self.coverage:
            options.append('--trace-turbo')
            options.append('--trace-turbo-path')
            options.append('{}'.format(coverage_path))

        try:
            output = subprocess.check_output(
                [self.d8] + options + [test_case]
            )
        except subprocess.CalledProcessError as e:
            self.commit_test(test_case, unique_id)
            self.logger.error(e)
            return None

        return output

    def fuzz(self, coverage_path=None):
        while True:
            test_case = self.queue.get()

            if test_case is None:
                break

            unique_id = None

            if self.debug:
                curr_time = datetime.now().strftime('%Y.%m.%d-%H:%M:%S')
                unique_id = str(uuid.uuid4()) + '_' + curr_time
                self.create_test(test_case, unique_id)

            output = self.execute(test_case.strip(), coverage_path, unique_id)

            if not self.fuzzer.validate(output):
                self.commit_test(test_case, unique_id)

            if self.coverage:
                turbo_json = os.path.join(coverage_path, 'turbo-f-0.json')
                self.logger.debug(self.coverage.parse(turbo_json))

            self.queue.task_done()

    def generate(self):
        while not self.queue.full():
            a = self.fuzzer.generate()
            self.logger.debug(a)
            self.logger.debug('-' * 50)
            self.queue.put(a)

    def start(self):
        self.logger.info('my pid is {}'.format(os.getpid()))
        start_time = time.time()

        for i in range(self.procs):
            args = ()

            if self.coverage:
                coverage_path = os.path.join(self.coverage_dir,
                                             'thread{}'.format(i))
                if not os.path.exists(coverage_path):
                    os.makedirs(coverage_path)

                args = (coverage_path,)

            t = Process(target=self.fuzz, args=args)
            t.daemon = True
            t.start()
            self.threads.append(t)

        self.generate()
        self.logger.info('generated all cases')

        self.queue.join()

        self.logger.info('processed all cases')

        for _ in range(self.procs):
            self.queue.put(None)

        for t in self.threads:
            t.join()

        end_time = time.time()

        self.logger.info('finished {} cases in {} seconds'.format(
                         self.count,
                         end_time - start_time))


@click.command()
@click.option('--fuzzer', required=True,
              type=click.Choice(fuzzers.fuzzers.keys()),
              help='which fuzzer to use. differences in README')
@click.option('--d8', envvar='D8_PATH',
              help='location of d8 executable. defaults to value stored \
              in D8_PATH environment variable')
@click.option('--procs', default=8, help='worker processes to create')
@click.option('--count', default=10, help='number of iterations')
@click.option('--crashes', default='./crashes',
              help='where to store crash findings')
@click.option('--tests', default='/tmp/vasilisk/tests',
              help='where to store inputs if debug mode on')
@click.option('--debug', is_flag=True, default=False,
              help='debug mode turns on more debug messages and stores all \
              test inputs to specified test folder')
@click.option('--turbo-coverage', is_flag=True, default=False,
              help='track coverage for turbo optimizations')
@click.option('--verbose', is_flag=True, default=False,
              help='print more stuff')
def main(fuzzer, d8, procs, count, crashes, tests, debug, turbo_coverage,
         verbose):
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    driver = Vasilisk(
        fuzzer, d8, procs, count, crashes, tests, debug, turbo_coverage
    )
    driver.start()


if __name__ == "__main__":
    main()
