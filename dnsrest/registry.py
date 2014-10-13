
# core
import json

# local
from logger import log

# libs
from dnslib import DNSLabel
from gevent import threading


class Registry(object):

    ''''
    Maps a container by id/name to a list of domain names and addresses.
    When the container is started, the list of domain names can be activated,
    and when the container is stopped the list of domain names can be
    deactivated.
    '''

    def __init__(self):
        self._mappings = {}
        self._active = {}
        self._domains = Node()
        self._lock = threading.Lock()

    def add(self, key, names):
        ''''
        Adds a mapping from the given key to a list of names. The names
        will be registered when the container is activated (running) and
        unregistered when the container is deactivated (stopped).
        '''
        with self._lock:
            # first, remove the old names, if any
            old_names = self._mappings.get(key, ())
            for name in old_names:
                self._domains.remove(name)

            # persist the mappings
            self._mappings[key] = names

            # check if these pertain to any already-active containers and
            # activate the domain names
            activate = []
            for container in self._active.itervalues():
                if key in ('name:/' + container.name, 'id:/' + container.id):
                    desc = self._desc(container)
                    self._activate(desc, names, container.addr)

    def get(self, key):
        with self._lock:
            return [n.idna().rstrip('.') for n in self._mappings.get(key, ())]

    def remove(self, key):
        with self._lock:
            old_names = self._mappings.get(key, ())
            if old_names:
                self._deactivate(old_names)
                del self._mappings[key]

    def activate(self, container):
        'Activate all rules associated with this container'
        desc = self._desc(container)
        with self._lock:
            self._active[container.id] = container
            names = self._get_records(container)
            if names:
                log.info('setting %s as active' % desc)
                self._activate(desc, names, container.addr)

    def deactivate(self, container):
        'Deactivate all rules associated with this container'
        with self._lock:
            old_container = self._active.get(container.id)
            if old_container is None:
                return
            del self._active[container.id]

            # since this container is active, get the old address so we can log
            # exactly which names/addresses are being deactivated
            desc = self._desc(container)
            names = self._get_records(container)
            if names:
                log.info('setting %s as inactive' % desc)
                self._deactivate(names)

    def resolve(self, name):
        'Resolves the address for this name, if any'
        with self._lock:
            res = self._domains.get(name)
            if res:
                log.debug('resolved %s -> %s' % (name, res))
                return res
            else:
                log.debug('no mapping for %s' % name)

    def dump(self):
        return json.dumps(self._domains.to_dict(), indent=4, sort_keys=1)

    def _activate(self, desc, names, addr):
        for name in names:
            self._domains.put(name, addr)
            log.info('added %s -> %s', name.idna(), addr)
        #log.debug('tree %s' % self.dump())

    def _deactivate(self, names):
        for name in names:
            addr = self._domains.get(name)
            if addr:
                self._domains.remove(name)
                log.info('removed %s -> %s', name.idna(), addr)
        #log.debug('tree %s', self.dump())

    def _get_records(self, container):
        names = self._mappings.get('name:/' + container.name)
        if names is None:
            names = self._mappings.get('id:/' + container.id)
        return names if names else ()

    def _desc(self, container):
        return '%s (%s)' % (container.name, container.id[:10])



class Node(object):

    'Stores a tree of domain names with wildcard support'

    def __init__(self):
        self._subs = {}
        self._wildcard = 0
        self._addr = None

    def get(self, name):
        return self._get(self._label(name))

    def put(self, name, addr):
        return self._put(self._label(name), addr)

    def remove(self, name):
        return self._remove(self._label(name))

    def to_dict(self):
        r = {}
        r[':addr'] = self._addr
        r[':wild'] = self._wildcard
        for key, sub in self._subs.iteritems():
            r[key] = sub.to_dict()
        return r

    def _label(self, name):
        return list(DNSLabel(name).label)

    def _get(self, label):
        if not label:
            return self._addr
        part = label.pop()
        sub = self._subs.get(part)
        if sub:
            res = sub._get(label)
            if res:
                return res
        return self._addr if self._wildcard else None

    def _put(self, label, addr):
        part = label.pop()

        if not label and part == '*':
            self._wildcard = 1
            self._addr = addr
            return

        sub = self._subs.get(part)
        if sub is None:
            sub = Node()
            self._subs[part] = sub

        if not label:
            sub._addr = addr
            return

        sub._put(label, addr)

    def _remove(self, label):
        part = label.pop()
        sub = self._subs.get(part)
        if not label:
            if part == '*':
                self._wildcard = 0
                self._addr = None
            elif sub:
                sub._addr = None
        elif sub:
            sub._remove(label)

        if sub and sub._is_empty():
            del self._subs[part]

    def _is_empty(self):
        return not self._subs and not self._addr


