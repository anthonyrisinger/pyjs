import os
from os import path


class CodePrimitive(object):

    _ts = None
    _sha1 = None
    _orig_src = None
    _code = None

    def __init__(self, p_code):
        with open(p_code, 'r') as code:
            self._code = code.read()

    def __hash__(self):
        return hash(self._sha1)


class LinkManager(object):

    _None = object()

    def __init__(self, p_los, p=None):
        p = path.abspath(p or '.') + os.sep
        self._p = p
        self._keys = set()
        self._cache = dict()
        for i, p_lo in enumerate(p_los):
            p_lo = path.relpath(path.abspath(p_lo), p)
            lo = LinkPrimitive(p_lo, p)
            qual = lo.qualname
            self._keys.add(qual)
            self._cache[qual] = lo
            self._cache.update(dict.fromkeys(lo.aliases, lo))
            if i == 0:
                self._cache['__main__'] = lo

    @property
    def main(self):
        return self['__main__']

    def __getitem__(self, key):
        return self._cache[key]

    def __setitem__(self, key, value):
        #XXX platform overrides (overloaded) ...
        # use code from LDAP lookup?
        raise NotImplemented

    def __delitem__(self, key):
        #XXX RE:__setitem__
        raise NotImplemented

    def __contains__(self, key):
        return key in self._cache

    def get(self, key, default=_None):
        try:
            return self[key]
        except KeyError:
            if default is self._None:
                raise
            else:
                return default

    def keys(self):
        return list(self)

    def __iter__(self):
        return iter(self._keys)


class LinkPrimitive(object):

    def __init__(self, p_code, p, code=None):
        self._p = p
        self._p_code = p_code
        self._code = code or CodePrimitive(path.join(p, p_code))

    def __str__(self):
        return self.abspath

    @property
    def abspath(self):
        return path.join(self._p, self._p_code)

    @property
    def qualname(self):
        return path.splitext(self._p_code)[0].replace(os.sep, '.')

    @property
    def aliases(self):
        return set([self.abspath, self._p_code, self._code])
