"""
Utilities used both by this package's setup.py and the library itself (if
dependencies aren't found by the time the plugin is loaded).
"""
# NOTE: Called from BOTH setup.py and the library. No dependencies may be imported
#       here!
import os, subprocess, errno

SP = dict((name, lambda log, cmd, *args, **kwargs:
            log.info(' '.join(cmd)) or
            getattr(subprocess, name)(cmd, *args, **kwargs))
          for name in ('Popen', 'check_call', 'check_output'))

def chdir(log, path):
    log.info('cd %s', path)
    os.chdir(path)

def npm_install(log, dirpath, reqs):
    """
    Calls the Node Package Manager (NPM) to install a package locally in
    ``dirpath``.
    """
    # if the node_modules directory doesn't exist, npm might use a
    # node_modules dir in a higher directory if it exists
    moddir = os.path.join(dirpath, 'node_modules')
    if not os.path.isdir(moddir):
        os.mkdir(moddir)
        
    origdir = os.getcwd()
    chdir(log, dirpath)
    try:
        SP['check_call'](log, ['npm', 'install'] + reqs)
    except OSError as e:
        if e.errno == errno.ENOENT:
            raise RuntimeError('npm(1) not found. Please install Node.js')
        else:
            raise
    finally:
       chdir(log, origdir)
