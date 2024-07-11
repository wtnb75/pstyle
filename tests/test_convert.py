import unittest
from pstyle.convert import Pstyle
import itertools


class TestConvert(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    # any to any
    testdata_map = [[
        ("qmark", "SELECT * FROM tbl1 WHERE id=?", (10,)),
        ("format", "SELECT * FROM tbl1 WHERE id=%s", (10,)),
        ("pyformat", "SELECT * FROM tbl1 WHERE id=%(arg0)s", {"arg0": 10}),
        ("numeric", "SELECT * FROM tbl1 WHERE id=:1", (10,)),
        ("named", "SELECT * FROM tbl1 WHERE id=:arg0", {"arg0": 10}),
    ], [
        ("qmark", "SELECT tleft.c1 FROM tleft RIGHT JOIN tright ON tleft.c1 = tright.c1 WHERE tright.c1 <> ?", (2,)),
        ("format", "SELECT tleft.c1 FROM tleft RIGHT JOIN tright ON tleft.c1 = tright.c1 WHERE tright.c1 <> %s", (2,)),
        ("pyformat", "SELECT tleft.c1 FROM tleft RIGHT JOIN tright ON tleft.c1 = tright.c1 WHERE tright.c1 <> %(arg0)s",
         {"arg0": 2}),
        ("numeric", "SELECT tleft.c1 FROM tleft RIGHT JOIN tright ON tleft.c1 = tright.c1 WHERE tright.c1 <> :1", (2,)),
        ("named", "SELECT tleft.c1 FROM tleft RIGHT JOIN tright ON tleft.c1 = tright.c1 WHERE tright.c1 <> :arg0",
         {"arg0": 2}),
    ], [  # no args
        ("qmark", "SELECT c1+c2 FROM T GROUP BY c1+c2", ()),
        ("format", "SELECT c1+c2 FROM T GROUP BY c1+c2", ()),
        ("pyformat", "SELECT c1+c2 FROM T GROUP BY c1+c2", {}),
        ("numeric", "SELECT c1+c2 FROM T GROUP BY c1+c2", ()),
        ("named", "SELECT c1+c2 FROM T GROUP BY c1+c2", {}),
    ], [  # multiple args
        ("qmark", "SELECT c1, SUM(c2) AS total FROM T GROUP BY c3 HAVING SUM(c2) > ? WHERE c1 LIKE ?",
         (100, '%abc')),
        ("format", "SELECT c1, SUM(c2) AS total FROM T GROUP BY c3 HAVING SUM(c2) > %s WHERE c1 LIKE %s",
         (100, '%abc')),
        ("numeric", "SELECT c1, SUM(c2) AS total FROM T GROUP BY c3 HAVING SUM(c2) > :1 WHERE c1 LIKE :2",
         (100, '%abc')),
        ("pyformat", "SELECT c1, SUM(c2) AS total FROM T GROUP BY c3 HAVING SUM(c2) > %(arg0)s WHERE c1 LIKE %(arg1)s",
         {"arg1": '%abc', "arg0": 100}),
        ("named", "SELECT c1, SUM(c2) AS total FROM T GROUP BY c3 HAVING SUM(c2) > :arg0 WHERE c1 LIKE :arg1",
         {"arg1": '%abc', "arg0": 100}),
    ], [  # with comment
        ("qmark", "SELECT * FROM t WHERE `k1`<?; -- select foo\n", (10,)),
        ("format", "SELECT * FROM t WHERE `k1`<%s; -- select foo\n", (10,)),
        ("numeric", "SELECT * FROM t WHERE `k1`<:1; -- select foo\n", (10,)),
        ("named", "SELECT * FROM t WHERE `k1`<:arg0; -- select foo\n", {"arg0": 10}),
        ("pyformat", "SELECT * FROM t WHERE `k1`<%(arg0)s; -- select foo\n", {"arg0": 10}),
    ]]
    # [0] -> [1:]
    testdata_map2 = [[
        ("pyformat", "SELECT * FROM tbl1 WHERE id=%(name)s", {"name": "hello"}),
        ("named", "SELECT * FROM tbl1 WHERE id=:name", {"name": "hello"}),
        ("qmark", "SELECT * FROM tbl1 WHERE id=?", ("hello",)),
        ("format", "SELECT * FROM tbl1 WHERE id=%s", ("hello",)),
        ("numeric", "SELECT * FROM tbl1 WHERE id=:1", ("hello",)),
    ], [
        ("named", "SELECT * FROM tbl1 WHERE id=:name", {"name": "hello"}),
        ("pyformat", "SELECT * FROM tbl1 WHERE id=%(name)s", {"name": "hello"}),
        ("qmark", "SELECT * FROM tbl1 WHERE id=?", ("hello",)),
        ("format", "SELECT * FROM tbl1 WHERE id=%s", ("hello",)),
        ("numeric", "SELECT * FROM tbl1 WHERE id=:1", ("hello",)),
    ], [
        ("auto", "SELECT * FROM tbl1 WHERE id=? and val=%s", (10, "hello")),
        ("qmark", "SELECT * FROM tbl1 WHERE id=? AND val=?", (10, "hello")),
        ("format", "SELECT * FROM tbl1 WHERE id=%s AND val=%s", (10, "hello")),
        ("pyformat", "SELECT * FROM tbl1 WHERE id=%(arg0)s AND val=%(arg1)s", {"arg0": 10, "arg1": "hello"}),
        ("numeric", "SELECT * FROM tbl1 WHERE id=:1 AND val=:2", (10, "hello")),
        ("named", "SELECT * FROM tbl1 WHERE id=:arg0 AND val=:arg1", {"arg0": 10, "arg1": "hello"}),
    ], [
        ("named", "SELECT * FROM tbl1 WHERE id=:1", ("hello",)),
        ("pyformat", "SELECT * FROM tbl1 WHERE id=%(arg0)s", {"arg0": "hello"}),
        ("qmark", "SELECT * FROM tbl1 WHERE id=?", ("hello",)),
        ("format", "SELECT * FROM tbl1 WHERE id=%s", ("hello",)),
        ("numeric", "SELECT * FROM tbl1 WHERE id=:1", ("hello",)),
    ], [
        ("pyformat", "SELECT * FROM tbl1 WHERE id=%s", ("hello",)),
        ("qmark", "SELECT * FROM tbl1 WHERE id=?", ("hello",)),
        ("format", "SELECT * FROM tbl1 WHERE id=%s", ("hello",)),
        ("numeric", "SELECT * FROM tbl1 WHERE id=:1", ("hello",)),
        ("named", "SELECT * FROM tbl1 WHERE id=:arg0", {"arg0": "hello"}),
    ],]

    def test_convert(self):
        for data in self.testdata_map:
            for v1, v2 in itertools.permutations(data, 2):
                resop, resarg = Pstyle.convert(v1[0], v2[0], v1[1], v1[2])
                self.assertEqual(v2[1], resop, f"sql {v1[0]} to {v2[0]}")
                self.assertEqual(v2[2], resarg, f"arg {v1[0]} to {v2[0]}")

    def test_convert2(self):
        for data in self.testdata_map2:
            v1 = data[0]
            for v2 in data[1:]:
                resop, resarg = Pstyle.convert(v1[0], v2[0], v1[1], v1[2])
                self.assertEqual(v2[1], resop, f"sql {v1[0]} to {v2[0]}")
                self.assertEqual(v2[2], resarg, f"arg {v1[0]} to {v2[0]}")

    def test_convert_notimpl(self):
        with self.assertRaises(NotImplementedError):
            Pstyle.convert("qmark", "auto", "SELECT * from t WHERE val=?", ("hello",))
