#!/usr/bin/env python3
import logging
import os
import time

import click

from multiprocessing import Process, JoinableQueue

import fuzzers
import grammars


class Vasilisk:
    def __init__(self, fuzzer, d8, procs, count,
                 crashes, tests, debug):
        self.logger = logging.getLogger(__name__)

        self.procs = procs
        self.count = count
        self.rate_limit = min(1000 * self.procs, self.count)

        if count < 0:
            self.rate_limit = 1000 * self.procs

        self.generated = 0

        self.grammar = grammars.grammars[fuzzer]()
        self.fuzzer = fuzzers.fuzzers[fuzzer](
            procs, d8, crashes, tests, debug
        )

        self.queue = JoinableQueue(self.rate_limit)

        self.threads = []

        if not os.path.exists(crashes):
            self.logger.info('creating crashes folder')
            os.makedirs(crashes)

        if not os.path.exists(tests):
            self.logger.info('creating tests folder')
            os.makedirs(tests)

    def generate(self):
        while self.generated < self.count or self.count < 0:
            grammar = self.grammar.generate()
            self.queue.put(grammar)
            self.generated += 1

            self.logger.debug(grammar)
            self.logger.debug('-' * 50)

    def fuzz(self, thread):
        while True:
            test_case = self.queue.get()

            if test_case is None:
                break

            self.fuzzer.fuzz(test_case, thread)

            self.queue.task_done()

    def start(self):
        self.logger.info('my pid is {}'.format(os.getpid()))
        start_time = time.time()

        for thread in range(self.procs):
            args = (thread,)
            t = Process(target=self.fuzz, args=args)
            t.daemon = True
            t.start()
            self.threads.append(t)

        self.generate()

        self.queue.join()

        for _ in range(self.procs):
            self.queue.put(None)

        for t in self.threads:
            t.join()

        end_time = time.time()

        self.logger.info('finished {} cases in {} seconds'.format(
                         self.count, end_time - start_time))


@click.command()
@click.option('--fuzzer', required=True,
              type=click.Choice(fuzzers.fuzzers.keys()),
              default='probabilistic',
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
@click.option('--verbose', is_flag=True, default=False,
              help='print more stuff')
def main(fuzzer, d8, procs, count, crashes, tests, debug, verbose):
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    driver = Vasilisk(
        fuzzer, d8, procs, count, crashes, tests, debug
    )
    driver.start()


if __name__ == "__main__":
    main()
