
# core
import json

# libs
from dnslib import A, DNSLabel
import falcon


class OperationsApi(object):

    'Expose an API to get, put and delete name/id domain mappings'

    VALID = set(['id', 'name'])

    def __init__(self, registry):
        self.registry = registry

    def on_get(self, req, res, label, arg):
        key = self._key(label, arg)
        record = self.registry.get(key)
        data = {'code': 0, 'record': record}
        self._ok(res, json.dumps(data))

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

    def _ok(self, res, data):
        res.status = falcon.HTTP_200
        res.body = json.dumps(data)

    def _fail(self, msg):
        raise falcon.HTTPError(falcon.HTTP_500, 'Error', msg)

    def _key(self, label, arg):
        if label not in self.VALID:
            self._fail('Unsuppported label %r' % label)
        return label + ':/' + arg

    def _parse(self, req):
        try:
            return json.loads(req.stream.read())
        except Exception, ex:
            raise falcon.HTTPError(falcon.HTTP_400, 'Error', ex.message)

    def _validate(self, data):
        'Ensure that the data being PUT is valid'
        if not isinstance(data, dict):
            self._fail('Expected a dict, not %r' % type(data))
        domains = data.get('domains')
        if not isinstance(domains, list):
            self._fail('Missing a "domains" key')
        res = []
        for name in domains:
            self._validate_type('domain name', name, (str, unicode))
            try:
                name = DNSLabel(name)
                res.append(name)
            except Exception, e:
                self._fail('Domain name parsing failed %s' % e)
    
        return res

    def _validate_type(self, key, val, *types):
        if not isinstance(val, types):
            self._fail('The %s must be of type %r, not %r' % \
                (key, type(val), types))

