import os
import logging
logger = logging.getLogger(__name__)

from pprint import pformat


_jscript_defaults = {
    'window': 'window',
    'document': 'window.document',
    'logger': 'window.console',
    'loads': 'window.JSON.parse',
    'dumps': 'window.JSON.stringify',
    }


def jscript(name, pyargs={}):
    args = _jscript_defaults.copy()
    args.update(pyargs)
    path = os.path.join(os.path.abspath(__path__[0]), 'js', name)
    head = ','.join(args.keys() + ['None', 'undefined'])
    tail = ','.join(args.values() + ['None=(new String())'])
    with open(path, 'rb') as fd:
        code = unicode(fd.read())
    logger.debug('jscript:%s:\n%s', name, pformat(args.items()))
    return '(function(%s){%s}(%s));' % (head, code, tail)
