
# core
import json
import unittest

# local
from nodez import Node


HOST1 = 'www.foo.com'
WILD1 = '*.foo.com'
ADDR1 = '1.2.3.4'
ADDR2 = '6.7.8.9'
TAG1 = 'name:/foo1'
TAG2 = 'name:/foo2'


def dump(n):
    print 'TREE:\n' + json.dumps(n.to_dict(), indent=4, sort_keys=1)


class NodeTest(unittest.TestCase):

    def test_tagging(self):
        n = Node()
        n.put(HOST1, ADDR1, TAG1)
        res = n.get(HOST1)
        self.assertEquals(res, [(ADDR1, TAG1)])

    def test_multiple_addresses(self):
        n = Node()

        # add a normal domain mapping for 2 nodes
        n.put(HOST1, ADDR1, TAG1)
        n.put(HOST1, ADDR2, TAG2)
        res = n.get(HOST1)
        self.assertEquals(res[0], (ADDR1, TAG1))
        self.assertEquals(res[1], (ADDR2, TAG2))

        # remove one tag
        n.remove(HOST1, TAG1)
        res = n.get(HOST1)
        self.assertEquals(res, [(ADDR2, TAG2)])

    def test_multiple_wildcards(self):
        n = Node()

        # add a wildcard mapping
        n.put(WILD1, ADDR1, TAG1)
        n.put(WILD1, ADDR2, TAG2)
        res = n.get('xyz.foo.com')
        self.assertEquals(res[0], (ADDR1, TAG1))
        self.assertEquals(res[1], (ADDR2, TAG2))

        # remove the wildcard mapping for one tagged node
        n.remove(WILD1, TAG2)
        res = n.get('abc.foo.com')
        self.assertEquals(res, [(ADDR1, TAG1)])

        # remove the remaining wildcard mapping
        n.remove(WILD1, TAG1)
        res = n.get('abc.foo.com')
        self.assertEquals(res, None)


if __name__ == '__main__':
    unittest.main()

