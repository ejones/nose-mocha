import unittest, os, re, collections, logging
from itertools import izip_longest
from functools import partial
from operator import eq
from nose import plugins
from nose.tools import assert_equal
import nose_mocha

localpath = partial(os.path.join, os.path.dirname(__file__))

def assert_contains_in_order(container, items, _END = lambda x: False):
    """
    Checks that the items in ``items`` occur in container in the order provided
    but not necessarily consecutively. Additionally, any check item that is
    callable will be called on each item to see if it "matches".
    """
    it = iter(items)
    def next_check():
        c = next(it, _END)
        if not isinstance(c, collections.Callable):
            c2 = partial(eq, c)
            c2.orig = c
            c = c2
        return c
    check = next_check()
    for item in container:
        if check(item):
            check = next_check()
    assert check is _END, 'Items not found by end of sequence: %r' % (
                            [getattr(check, 'orig', check)] + list(it))
        

class MochaTestCase(plugins.PluginTester, unittest.TestCase):
    activate = '--with-mocha'
    plugins = [nose_mocha.Mocha()]

    def check_line_patterns(self, patterns, lines = None):
        """ Takes a list of lines and a list of patterns and matches each line
        with the corresponding pattern. """
        if lines is None:
            lines = self.output
        for line, pat in izip_longest(lines, patterns):
            pat = '^' + pat + '\n$'
            assert line, 'Missing line for pattern %r' % pat
            assert pat, 'Unexpected line %r' % line
            assert re.search(pat, line), 'not re.search(%r, %r)' % (pat, line)

class TestEmpty(MochaTestCase):
    suitepath = localpath('empty_suite')

    def runTest(self):
        self.check_line_patterns([
            r'',
            r'-+',
            r'Ran 0 tests in [\d.]+s',
            r'',
            r'OK'])

class TestSimple(MochaTestCase):
    suitepath = localpath('simple_suite')

    output_line_checks = [
        'FAIL: runTest (nose_mocha.MochaTestProxy)\n',
        'AssertionError: Math should be inconsistent\n',
        '  AssertionError: 1 == 2\n',
        'FAIL: runTest (nose_mocha.MochaTestProxy)\n',
        'AssertionError: Something should do stuff that breaks\n',
        '  Error\n',
        lambda s: s.startswith('Ran 3 tests in '),
        'FAILED (failures=2)\n'
    ]

    def runTest(self):
        assert_contains_in_order(self.output, self.output_line_checks)

class Test__DummyForCoverage__(unittest.TestCase):
    """
    For some reason, we need to do this to get ``coverage`` to pick up on
    module-level code in this project.
    """
    def runTest(self):
        reload(nose_mocha)

class TestWrapperFunc(MochaTestCase):
    args = ['--mocha-wrapper-func', 'test:TestWrapperFunc.mocha_run_wrapper',
            '--debug', 'nose.plugins.mocha.test']
    suitepath = TestSimple.suitepath

    @classmethod
    def mocha_run_wrapper(cls, path, runner):
        log = logging.getLogger('nose.plugins.mocha.test')
        assert_equal(path, cls.suitepath)
        results = list(runner())
        assert_equal([res[:2] for res in results], [
            ('pass', 'Math should be consistent'),
            ('fail', 'Math should be inconsistent'),
            ('fail', 'Something should do stuff that breaks')
        ])
        return results

    def runTest(self):
        assert_contains_in_order(self.output, TestSimple.output_line_checks)

class TestRequire(MochaTestCase):
    args = ['--mocha-require', 'should']
    suitepath = localpath('suite_with_should')

    def runTest(self):
        assert_contains_in_order(self.output, [
            'FAIL: runTest (nose_mocha.MochaTestProxy)\n',
            'AssertionError: Math should be inconsistent\n',
            '  AssertionError: expected 1 to not equal 1\n',
            lambda s: s.startswith('Ran 2 tests in '),
            'FAILED (failures=1)\n'
        ])

class TestSetFromEnv(MochaTestCase):
    env = {'NOSE_MOCHA_REQUIRE': 'should',
           'NOSE_MOCHA_BAIL': '1'}
    suitepath = localpath('suite_with_should')

    def runTest(self):
        assert_contains_in_order(self.output, [
            'FAIL: runTest (nose_mocha.MochaTestProxy)\n',
            'AssertionError: Math should be inconsistent\n',
            '  AssertionError: expected 1 to not equal 1\n',
            lambda s: s.startswith('Ran 1 test in '),
            'FAILED (failures=1)\n'
        ])

class TestSingleFile(MochaTestCase):
    suitepath = localpath('single_file.js')
    def runTest(self):
        self.check_line_patterns([
            r'\.',
            r'-+',
            r'Ran 1 test in [\d.]+s',
            r'',
            r'OK'])

class TestFailureToRun(MochaTestCase):
    suitepath = localpath('fails_to_run.js')
    def runTest(self):
        assert_contains_in_order(self.output, [
            'ERROR: Failure: ValueError (Unable to load tests from file ' +
                os.path.abspath(self.suitepath) + ')\n',
            lambda s: s.startswith('Ran 1 test in '),
            'FAILED (errors=1)\n'])
