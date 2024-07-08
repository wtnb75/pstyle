import unittest
from pstyle.main import Pstyle
import itertools


class TestConvert(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    testdata_map = [[
        ("qmark", "SELECT * FROM tbl1 WHERE id=?", (10,)),
        ("format", "SELECT * FROM tbl1 WHERE id=%s", (10,)),
        ("pyformat", "SELECT * FROM tbl1 WHERE id=%(arg0)s", {"arg0": 10}),
        ("numeric", "SELECT * FROM tbl1 WHERE id=:1", (10,)),
        ("named", "SELECT * FROM tbl1 WHERE id=:arg0", {"arg0": 10}),
    ]]
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
    ]]

    def test_convert(self):
        pst = Pstyle()
        for data in self.testdata_map:
            for v1, v2 in itertools.permutations(data, 2):
                resop, resarg = pst.convert(v1[0], v2[0], v1[1], v1[2])
                self.assertEqual(v2[1], resop, f"sql {v1[0]} to {v2[0]}")
                self.assertEqual(v2[2], resarg, f"arg {v1[0]} to {v2[0]}")

    def test_convert2(self):
        pst = Pstyle()
        for data in self.testdata_map2:
            v1 = data[0]
            for v2 in data[1:]:
                resop, resarg = pst.convert(v1[0], v2[0], v1[1], v1[2])
                self.assertEqual(v2[1], resop, f"sql {v1[0]} to {v2[0]}")
                self.assertEqual(v2[2], resarg, f"arg {v1[0]} to {v2[0]}")
