import unittest
import sqlite3
from pstyle.main import DBWrapper


class TestWrapper(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        cur = self.db.cursor()
        cur.execute("create table tbl1 (id integer, val varchar)")
        cur.execute("insert into tbl1 (id, val) values (?, ?), (?, ?)", (0, "val1", 1, "val2"))
        cur.close()

    def tearDown(self):
        self.db.close()

    def test_wrap_named(self):
        named = DBWrapper(self.db, sqlite3.paramstyle, "named")
        cur = named.cursor()
        cur.execute("select * from tbl1 where id=:id", {"id": 1})
        descr = cur.description
        data = cur.fetchone()
        keys = [x[0] for x in descr]
        res = dict(zip(keys, data))
        self.assertEqual({"id": 1, "val": "val2"}, res)

    def test_wrap_no_named(self):
        named = DBWrapper(self.db, sqlite3.paramstyle, "named")
        cur = named.cursor()
        cur.execute("select * from tbl1")
        descr = cur.description
        keys = [x[0] for x in descr]
        data = cur.fetchall()
        res = [dict(zip(keys, x)) for x in data]
        self.assertEqual([{"id": 0, "val": "val1"}, {"id": 1, "val": "val2"}], res)
