nose-mocha
==========

This is a `Nose <http://nose.readthedocs.org/en/latest>`_ plugin that
integrates tests written for the `node.js <http://nodejs.org/>`_ test framework
`Mocha <http://visionmedia.github.com/mocha/>`_ with nosetests by running
``mocha(1)`` on test targets and presenting test results in the nosetests
report. Most Mocha options (based on Mocha 1.8.1 at time of writing) may be
passed as nosetests options with a prefix of "mocha-" and will be passed on to
``mocha(1)`` (see `Options`_). Some Mocha options, like "watch" and "reporter",
don't make sense in this context so are not supported.

Options
-------
::

  --with-mocha          Enable the plugin
  --mocha-globals=NAMES
                        allow the given comma-delimited global [names]
  --mocha-timeout=MS    set test-case timeout in milliseconds [2000]
  --mocha-wrapper-func=mypackage.mymodule:my_func
                         If specified, called whenever ``mocha(1)`` is to be
                        run, with two arguments: the path in question, and a
                        callable that when called invokes ``mocha(1)`` and
                        passes any kwargs to `subprocess.Popen`, and returns
                        an iterable of test results. This wrapper should pass
                        on these results, with optional filtering of course.
  --mocha-slow=MS       'slow' test threshold in milliseconds [75]
  --mocha-grep=PATTERN  only run tests matching <pattern>
  --mocha-ignore-leaks  ignore global variable leaks
  --mocha-invert        inverts --grep matches
  --mocha-compilers=<ext>:<module>,...
                        use the given module(s) to compile files
  --mocha-bail          bail after first test failure
  --mocha-recursive     include sub directories
  --mocha-ui=NAME       specify user-interface (bdd|tdd|exports)
  --mocha-require=NAME  require the given module

Tests
-----

To run the test suite::

    python setup.py nosetests

Notes
-----

- even when Nose is run with ``--collect-only``, ``mocha(1)`` is still invoked
  to get its test report.

----

Copyright (C) 2013 by Evan Jones. Licensed under the MIT License - see LICENSE.txt for details.
