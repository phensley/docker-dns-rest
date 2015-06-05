

# libs
from dnslib import A, DNSHeader, DNSLabel, DNSRecord, QTYPE, RR
from gevent import socket
from gevent.server import DatagramServer
from gevent.resolver_ares import Resolver


DNS_RESOLVER_TIMEOUT = 3.0


def contains(txt, *subs):
    return any(s in txt for s in subs)


class DnsServer(DatagramServer):

    '''
    Answers DNS queries against the registry, falling back to the recursive
    resolver (if present).
    '''

    def __init__(self, bindaddr, registry, dns_servers=None):
        DatagramServer.__init__(self, bindaddr)
        self._registry = registry
        self._resolver = None
        if dns_servers:
            self._resolver = Resolver(servers=dns_servers,
                timeout=DNS_RESOLVER_TIMEOUT, tries=1)

    def handle(self, data, peer):
        rec = DNSRecord.parse(data)
        addr = None
        if rec.q.qtype in (QTYPE.A, QTYPE.AAAA):
            addr = self._registry.resolve(rec.q.qname.idna())
            if not addr:
                addr = self._resolve('.'.join(rec.q.qname.label))
        self.socket.sendto(self._reply(rec, addr), peer)

    def _reply(self, rec, addrs=None):
        reply = DNSRecord(DNSHeader(id=rec.header.id, qr=1, aa=1, ra=1), q=rec.q)
        if addrs:
            if not isinstance(addrs, list):
                addrs = [addrs]
            for addr in addrs:
                reply.add_answer(RR(rec.q.qname, QTYPE.A, rdata=A(addr)))
        return reply.pack()

    def _resolve(self, name):
        if not self._resolver:
            return None
        try:
            return self._resolver.gethostbyname(name)
        except socket.gaierror, e:
            msg = str(e)
            if not contains(msg, 'ETIMEOUT', 'ENOTFOUND'):
                print msg

