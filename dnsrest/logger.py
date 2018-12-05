
# core
from datetime import datetime
import sys


class Logger(object):

    def __init__(self):
        self._process = sys.argv[0]
        self._quiet = 0
        self._verbose = 0

    def set_process_name(self, name):
        self._process = name

    def set_quiet(self, quiet):
        self._quiet = quiet

    def set_verbose(self, verbose):
        self._verbose = verbose

    def info(self, msg, *args):
        if not self._quiet:
            self._log(msg, *args)   

    def debug(self, msg, *args):
        if not self._quiet and self._verbose:
            self._log(msg, *args)

    def error(self, msg, *args):
        self._log(msg, *args)

    def _log(self, msg, *args):
            now = datetime.now().isoformat()
            line = '%s [%s] %s\n' % (now, self._process, msg % args)
            sys.stderr.buffer.write(line.encode('utf-8'))
            sys.stderr.flush()


def init_logger(process=None, quiet=0, verbose=0):
    if process:
        log.set_process_name(process)
    if quiet:
        log.set_quiet(quiet)
    if verbose:
        log.set_verbose(verbose)


log = Logger()

