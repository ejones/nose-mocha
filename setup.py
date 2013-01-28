import setuptools
from setuptools.command import easy_install as _easy_install, develop as _develop
import os, subprocess, errno, sys, collections
from distutils import log

def main(args=None):

    # HACK: ensure NPM requirements are present for all commands.
    log.set_threshold(log.INFO)
    npm_install('./nose_mocha', ['mocha'])
    npm_install('.', ['should'])

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
        package_data={
            'nose_mocha': [
                os.path.join(dirpath, f)[len('nose_mocha/'):]
                for dirpath, dirnames, filenames in os.walk('nose_mocha/node_modules')
                for f in filenames],
        },
        zip_safe=False,
        setup_requires=['nose', 'coverage'],
        test_suite='nose.collector',
        entry_points="""\
        [nose.plugins.0.10]
        mocha = nose_mocha:Mocha
        """,
    )

    if args:
        settings['script_name'] = __file__
        settings['script_args'] = args

    setuptools.setup(**settings)

def wrap_exec(func, cmd, *args, **kwargs):
    log.info(' '.join(cmd))
    return func(cmd, *args, **kwargs)

def wrap_os(funcname, *args):
    log.info(funcname + ''.join(' ' + (str(x) if not isinstance(x, basestring) else x)
                                for x in args))
    return getattr(os, funcname)(*args)

def npm_install(dirpath, reqs):
    # ensure node_modules folder is present locally. If not, NPM may use the
    # node_modules dir off a parent dir.
    moddir = os.path.join(dirpath, 'node_modules')
    if not os.path.isdir(moddir):
        wrap_os('mkdir', moddir)

    # NPM only works in the current dir, so temporarily CD into the destination
    origdir = os.getcwd()
    wrap_os('chdir', dirpath)
    try:
        wrap_exec(subprocess.check_call, ['npm', 'install'] + reqs)
    except OSError as e:
        if e.errno == errno.ENOENT:
            log.error('npm(1) not found. Please install Node.js')
            return 1
        else:
            raise
    finally:
        wrap_os('chdir', origdir)

if __name__ == '__main__':
    sys.exit(main() or 0)
