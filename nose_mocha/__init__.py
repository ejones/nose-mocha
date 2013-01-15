from itertools import imap, ifilter
from functools import partial
import logging
import unittest
import os
import json
import subprocess
import pkg_resources
import re
import sys
from traceback import print_exc
from nose import plugins, failure
from . import installutil

noop = lambda *args, **kwargs: None

# per nose doc, use a logger namespaced with "nose.plugins"
logger = logging.getLogger('nose.plugins.mocha')

mocha_script = pkg_resources.resource_filename('nose_mocha', 'node_modules/.bin/mocha')

class Mocha(plugins.Plugin):
    """
    Integrates tests written for the node.js test framework Mocha with
    nosetests by running ``mocha(1)`` during the tests and presenting test
    results in the nosetests report. Most Mocha options (based on Mocha 1.8.1
    at time of writing) may be passed as nosetests options with a prefix of
    "mocha-" and will be passed on to ``mocha(1)``. Some options, like "watch"
    and "reporter" don't make sense in this context so are not supported.

    Notes:
    - currently, even in "collect-only" mode, the JavaScript tests are still run
    """

    optdefs = {
        '--mocha-wrapper-func': {
            'metavar': 'mypackage.mymodule:my_func',
            'help': '''
If specified, called whenever ``mocha(1)`` is to be run, with two arguments:
the path in question, and a callable that when called invokes ``mocha(1)`` and
passes any kwargs to `subprocess.Popen`, and returns an iterable of test
results. This wrapper should pass on these results, with optional filtering of
course.
                '''
        },
        '--mocha-require': {
            'metavar': 'NAME',
            'action': 'append',
            'help': "require the given module"
        },
        '--mocha-ui': {
            'metavar': 'NAME',
            'help': "specify user-interface (bdd|tdd|exports)"
        },
        '--mocha-grep': {
            'metavar': 'PATTERN',
            'help': "only run tests matching <pattern>"
        },
        '--mocha-invert': {
            'action': 'store_true',
            'help': "inverts --grep matches"
        },
        '--mocha-timeout': {
            'metavar': 'MS',
            'help': "set test-case timeout in milliseconds [2000]"
        },
        '--mocha-slow': {
            'metavar': 'MS',
            'help': "'slow' test threshold in milliseconds [75]"
        },
        '--mocha-bail': {
            'action': 'store_true',
            'help': "bail after first test failure"
        },
        '--mocha-recursive': {
            'action': 'store_true',
            'help': "include sub directories"
        },
        '--mocha-globals': {
            'metavar': 'NAMES',
            'help': "allow the given comma-delimited global [names]"
        },
        '--mocha-ignore-leaks': {
            'action': 'store_true',
            'help': "ignore global variable leaks"
        },
        '--mocha-compilers': {
            'metavar': '<ext>:<module>,...',
            'help': "use the given module(s) to compile files"
        }
    }

    optdests = dict(
        (optname, kwargs.get('dest') or '_'.join(optname.lstrip('-').split('-')))
         for optname, kwargs in optdefs.iteritems())

    def options(self, parser, env):
        super(Mocha, self).options(parser, env)
        for optname, kwargs in self.optdefs.iteritems():
            kwargs = dict(kwargs, dest=self.optdests[optname])
            kwargs.setdefault('action', 'store')
            if 'default' not in kwargs:
                kwargs['default'] = env.get('NOSE_' + kwargs['dest'].upper())
                if kwargs['action'] == 'store_true':
                    kwargs['default'] = kwargs['default'] is not None
            parser.add_option(optname, **kwargs)

    def configure(self, options, config):
        super(Mocha, self).configure(options, config)
            
        # Last resort. Easy install, in a brilliant move, will not call
        # install, so mocha may not exist by this point.
        # do this in configure because in __init__ logging handlers haven't been
        # initialized
        if not os.path.isfile(mocha_script):
            logger.warn('Mocha not found in installation directory (%s)! Fetching from NPM.', mocha_script)
            installutil.npm_install(logger, os.path.dirname(__file__), ['mocha'])

        self.mocha_opts = dict(
            ('--' + '-'.join(dest[len('mocha_'):].split('_')), getattr(options, dest))
            for dest in self.optdests.itervalues()
            if dest != 'mocha_wrapper_func')

        # keep track of nosetest args. The first file we find in each
        # triggers Mocha to be run on it.
        self.remaining_targets = [os.path.abspath(f).rstrip(os.path.sep)
                                  for f in (config.testNames or ['.'])]
        self.is_default_test = not config.testNames

        if options.mocha_wrapper_func:
            epoint = pkg_resources.EntryPoint.parse('x = ' + options.mocha_wrapper_func)
            self.wrapper_func = epoint.load(require=False)
        else:
            self.wrapper_func = lambda path, runner: runner()

    def loadTestsFromDir(self, path):
        if path in self.remaining_targets:
            self.remaining_targets.remove(path)
            results = self.wrapper_func(path,
                        partial(self.run_mocha, path if not self.is_default_test else None))
            for result in results:
                yield MochaTestProxy(*result)
        
    def run_mocha(self, path=None,
                    _tap_result_start_re=re.compile('^((?:not )?ok)\s+(\S+)\s+(.+)'),
                    _tap_codes={'ok': 'pass', 'not ok': 'fail'},
                    **kwargs):
        """
        Invokes mocha on the given path and returns an iterable of tuples of
        ``(<status>, <title>, <body>)`` where status is "pass" or "fail" and
        body is a list of lines.
        """
        cmd = [mocha_script, '--reporter', 'tap']
        for optname, optval in self.mocha_opts.iteritems():
            if optval:
                cmd.append(optname)
                if optval is not True:
                    if not isinstance(optval, list):
                        optval = [optval]
                    for item in optval:
                        cmd.append(item)
        if path is not None:
            cmd.append(path)

        logger.info(' '.join(cmd))
        proc = subprocess.Popen(cmd, stdout = subprocess.PIPE, **kwargs)

        # parse the TAP
        # REVIEW!
        curtest = (None, None, [])
        for line in iter(proc.stdout.readline, ''):
            if line[:1].isspace():
                curtest[2].append(line)
            else:
                m = _tap_result_start_re.search(line)
                if m:
                    if curtest[0]:
                        yield curtest
                    curtest = (_tap_codes[m.group(1)], m.group(3), [])
        if curtest[0]:
            yield curtest
                
                
class MochaTestProxy(unittest.TestCase):
    def __init__(self, status, title, lines):
        self.status = status
        self.title = title
        self.lines = lines
        super(MochaTestProxy, self).__init__()

    def runTest(self):
        assert self.status == 'pass', self.title + '\n' + ''.join(self.lines)
