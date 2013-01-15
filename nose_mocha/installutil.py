# NOTE: Called from BOTH setup.py and the library. No dependencies may be imported
#       here!
import os, subprocess, errno

def logcmd(log, cmd):
    log.info(' '.join(cmd))
    return cmd

def npm_install(log, dirpath, reqs):
    origdir = os.getcwd()
    os.chdir(dirpath)
    try:
        subprocess.check_call(logcmd(log, ['npm', 'install'] + reqs))
    except OSError as e:
        if e.errno == errno.ENOENT:
            raise RuntimeError('npm(1) not found. Please install Node.js')
        else:
            raise
    finally:
       os.chdir(origdir)
