
# core
from collections import namedtuple
import json
import re


RE_VALIDNAME = re.compile('[^\w\d.-]')


Container = namedtuple('Container', 'id, name, running, addr')


def get(d, *keys):
    empty = {}
    return reduce(lambda d, k: d.get(k, empty), keys, d) or None


class DockerMonitor(object):

    '''
    Reads events from Docker and activates/deactivates container domain names
    '''

    def __init__(self, client, registry):
        self._docker = client
        self._registry = registry

    def run(self):
        # start the event poller, but don't read from the stream yet
        events = self._docker.events()

        # bootstrap by activating all running containers
        for container in self._docker.containers():
            rec = self._inspect(container['Id'])
            if rec.running:
                self._registry.activate(rec)    

        # read the docker event stream and update the name table
        for raw in events:
            evt = json.loads(raw)
            cid = evt.get('id')
            if cid is None:
                continue
            status = evt.get('status')
            if status in ('start', 'die'):
                try:
                    rec = self._inspect(cid)
                    if rec:
                        if status == 'start':
                            self._registry.activate(rec)
                        else:
                            self._registry.deactivate(rec)
                except Exception, e:
                    print str(e)

    def _inspect(self, cid):
        # get full details on this container from docker
        rec = self._docker.inspect_container(cid)

        # ensure name is valid, and append our domain
        name = get(rec, 'Name')
        if not name:
            return None
        name = RE_VALIDNAME.sub('', name).rstrip('.')
        return Container(
            get(rec, 'Id'),
            name,
            get(rec, 'State', 'Running'),
            get(rec, 'NetworkSettings', 'IPAddress')
        )

