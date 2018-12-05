
# core
import json

# libs
from dnslib import A, DNSLabel
import falcon


class BaseApi(object):

    def __init__(self, registry):
        self.registry = registry

    def _ok(self, res, data, indent=0):
        res.status = falcon.HTTP_200
        if indent:
            res.body = json.dumps(data, indent=4, sort_keys=1)
        else:
            res.body = json.dumps(data)

    def _fail(self, msg):
        raise falcon.HTTPError(falcon.HTTP_500, 'Error', msg)

    def _parse(self, req):
        try:
            return json.loads(req.stream.read())
        except Exception as ex:
            raise falcon.HTTPError(falcon.HTTP_400, 'Error', ex.message)

    def _validate_type(self, key, val, *types):
        if not isinstance(val, types):
            self._fail('The %s must be of type %r, not %r' % \
                (key, types, type(val)))
    
    def _validate_domain(self, domain):
        self._validate_type('domain name', domain, (str))
        try:
            return DNSLabel(domain)
        except Exception as e:
            self._fail('Domain name parsing failed %s' % e)

    def _validate_ips(self, ips):
        if not isinstance(ips, list):
            self._fail('Missing an "ips" array')
        for ip in ips:
            try:
                ip = A(ip)
            except Exception as e:
                self._fail('Address parsing failed %s' % e)


class StaticApi(BaseApi):

    'Expose an API to create and manage static domain to ip mappings'

    def __init__(self, registry):
        BaseApi.__init__(self, registry)

    def on_get(self, req, res, domain):
        self._ok(res, {'code': 0})

    def on_put(self, req, res, domain):
        data = self._parse(req)
        domain, ips = self._validate(domain, data)
        for ip in ips:
            self.registry.activate_static(domain, ip)
        self._ok(res, {'code': 0})

    def on_delete(self, req, res, domain):
        domain = self._validate_domain(domain)
        self.registry.deactivate_static(domain)
        self._ok(res, {'code': 0})

    def _validate(self, domain, data):
        if not isinstance(data, dict):
            self._fail('Expected a dict, got %s' % type(data))
        ips = data.get('ips')
        self._validate_ips(ips)
        domain = self._validate_domain(domain)
        return domain, ips


class ContainerApi(BaseApi):

    'Expose an API to create and manage container name/id domain mappings'

    VALID = set(['id', 'name'])

    def __init__(self, registry):
        BaseApi.__init__(self, registry)

    def on_get(self, req, res, label, arg):
        key = self._key(label, arg)
        record = self.registry.get(key)
        self._ok(res, {'code': 0, 'record': record})

    def on_put(self, req, res, label, arg):
        data = self._parse(req)
        data = self._validate(data)
        key = self._key(label, arg)
        self.registry.add(key, data)
        self._ok(res, {'code': 0})

    def on_delete(self, req, res, label, arg):
        key = self._key(label, arg)
        self.registry.remove(key)
        self._ok(res, {'code': 0})

    def _key(self, label, arg):
        if label not in self.VALID:
            self._fail('Unsuppported label %r' % label)
        return label + ':/' + arg

    def _validate(self, data):
        'Ensure that the data being PUT is valid'
        if not isinstance(data, dict):
            self._fail('Expected a dict, not %r' % type(data))
        domains = data.get('domains')
        if not isinstance(domains, list):
            self._fail('Missing a "domains" array')
        res = []
        for name in domains:
            res.append(self._validate_domain(name))
        return res


class DebugApi(BaseApi):

    def __init__(self, registry):
        BaseApi.__init__(self, registry)

    def on_get(self, req, res):
        self._ok(res, self.registry._domains.to_dict(), indent=1)


