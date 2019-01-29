
# libs
from dnslib import DNSLabel


class Node(object):

    'Stores a tree of domain names with wildcard support'

    def __init__(self):
        self._subs = {}
        self._wildcard = 0
        self._addr = []
        self._addr_index = 0

    def get(self, name):
        return self._get(self._label(name))

    def put(self, name, addr, tag=None):
        return self._put(self._label(name), addr, tag)

    def remove(self, name, tag=None):
        return self._remove(self._label(name), tag)

    def to_dict(self):
        r = {}
        r[':addr'] = self._addr
        r[':wild'] = self._wildcard
        for key, sub in self._subs.items():
            r[key] = sub.to_dict()
        return r

    def _label(self, name):
        return list(DNSLabel(name).label)

    def _get(self, label):
        if not label:
            self._addr_index += 1
            if len(self._addr) != 0:
                self._addr_index %= len(self._addr)
            return self._addr[self._addr_index:] + self._addr[:self._addr_index]
        part = label.pop()
        sub = self._subs.get(part)
        if sub:
            res = sub._get(label)
            if res:
                return res
        return self._addr if self._wildcard else None

    def _put(self, label, addr, tag=None):
        part = label.pop()

        if not label and part == b'*':
            self._wildcard = 1
            self._addr.append((addr, tag))
            return

        sub = self._subs.get(part)
        if sub is None:
            sub = Node()
            self._subs[part] = sub

        if not label:
            sub._addr.append((addr, tag))
            return

        sub._put(label, addr, tag)

    def _remove(self, label, tag=None):
        part = label.pop()
        sub = self._subs.get(part)
        if not label:
            if part == '*':
                tagged = self._tagged_addr(self._addr, tag)
                self._addr = [(a, t) for a, t in self._addr if a not in tagged]
                self._wildcard = 0 if not self._addr else 1
                return tagged
            elif sub:
                tagged = self._tagged_addr(sub._addr, tag)
                sub._addr = [(a, t) for a, t in sub._addr if a not in tagged]
                return tagged
        elif sub:
            sub._remove(label, tag)

        if sub and sub._is_empty():
            del self._subs[part]
        return []

    def _is_empty(self):
        return not self._subs and not self._addr

    def _tagged_addr(self, addr, tag):
        return set([a for a, t in addr if t == tag or tag is None])

