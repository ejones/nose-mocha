import setuptools
from setuptools.command import easy_install as _easy_install, develop as _develop
import os, subprocess, errno, sys, collections
from distutils import log

# fixes a setuptools problem with nosetests
import multiprocessing, logging

# specially designed without dependencies
from nose_mocha import installutil

def main(args=None):

    settings = dict(
        name='nose-mocha',
        version='0.0.1',
        description='Integrates the Node.js testing framework Mocha with nosetests',
        long_description=open('README.rst').read(),
        author='Evan Jones',
        author_email='evan.q.jones@gmail.com',
        url='http://github.com/ejones/nose-mocha',
        keywords='test nose nosetest automatic discovery mocha nodejs js javascript',
        classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Testing'
        ],
        license='MIT',
        packages=['nose_mocha'],
        include_package_data=True,
        zip_safe=False,
        setup_requires=['nose', 'coverage'],
        test_suite='nose.collector',
        entry_points="""\
        [nose.plugins.0.10]
        mocha = nose_mocha:Mocha
        """,
        cmdclass=CmdClass()
    )

    if args:
        settings['script_name'] = __file__
        settings['script_args'] = args

    setuptools.setup(**settings)

class develop(_develop.develop):
    def install_for_development(self):
        _develop.develop.install_for_development(self)
        installutil.npm_install(log, './nose_mocha', ['mocha'])

class easy_install(_easy_install.easy_install):
    def install_egg(self, egg_path, tmpdir):
        ret = _easy_install.easy_install.install_egg(self, egg_path, tmpdir)
        eggname = os.path.basename(egg_path)
        if eggname.startswith('nose_mocha-'):
            destination = os.path.join(self.install_dir, eggname)
            installutil.npm_install(log, os.path.join(destination, 'nose_mocha'), ['mocha'])
        return ret

_nosetests = None
def mk_nosetests_cmd():
    global _nosetests
    if _nosetests is None:
        from nose.commands import nosetests as base
        class _nosetests(base):
            def run(self):
                installutil.npm_install(log, './nose_mocha', ['mocha'])
                installutil.npm_install(log, '.', ['should'])
                base.run(self)
    return _nosetests

class CmdClass(collections.MutableMapping):
    """
    Write cmdclass this way to lazily load the nosetests command, which will
    only be avaialable after nosetests is installed by setup_requires.
    """
    _items = {
        'develop': lambda: develop,
        'easy_install': lambda: easy_install,
        'nosetests': mk_nosetests_cmd
    }

    def __init__(self):
        self._items = dict(self._items)

    def __getitem__(self, key):
        return self._items[key]()

    def __iter__(self):
        return iter(self._items)

    def __len__(self):
        return len(self._items)

    def __setitem__(self, key, val):
        self._items[key] = lambda: val

    def __delitem__(self, key):
        del self._items[key]

if __name__ == '__main__':
    sys.exit(main() or 0)
