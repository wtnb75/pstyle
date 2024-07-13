# Python DB-API paramstyle converter

## Problem

The DB-API is one of the greatest feature in our python-world.
But paramstyle...

| module | paramstyle |
|---|---|
| sqlite3 | qmark |
| mysql-connector-python | pyformat |
| mysqlclient | format |
| mariadb | qmark |
| psycopg2 | pyformat |
| psycopg | pyformat |
| py-postgresql | pyformat |
| pyodbc | qmark |
| pymssql | pyformat |
| python-oracledb | named |
| duckdb | qmark |
| firebird-driver | qmark |
| pydrda | format |
| pymonetdb | pyformat |
| pyhive.hive/presto | pyformat |

- qmark: `?`, `?`
- pyformat: `%(name)s`, `%(arg)s`
- format: `%s`, `%s`
- named: `:name`, `:arg`
- numeric: `:1`, `:2`

## Install

- pip install pstyle

## test with CLI

```
# pstyle --help
Usage: pstyle [OPTIONS] COMMAND [ARGS]...

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  convert  convert SQL and params with specified paramstyle
# pstyle convert --args hello --args world --from-style qmark --to-style format "select * from tbl1 where `key`=? and `value`=?"
op: SELECT * FROM tbl1 WHERE `key`=%s AND `value`=%s
args: ('hello', 'world')
# pstyle convert --args world --args hello --from-style numeric --to-style qmark "select * from tbl1 where `key`=:2 and `value`=:1"
op: SELECT * FROM tbl1 WHERE `key`=? AND `value`=?
args: ('hello', 'world')
```

using docker

```
# docker run --rm ghcr.io/wtnb75/pstyle convert --help
Usage: pstyle convert [OPTIONS] OPERATION

  convert SQL and params with specified paramstyle

Options:
  --verbose / --quiet
  --from-style [named|pyformat|qmark|numeric|format|auto]
  --to-style [named|pyformat|qmark|numeric|format]
  --args TEXT
  --kwargs TEXT                   json
  --normalize / --original        [default: normalize]
  --help                          Show this message and exit.
```

## convert from str, args

```python
import sqlite3
from pstyle.convert import Pstyle

db = sqlite3.connect(":memory:")
print("paramstyle:", sqlite3.paramstyle)    # qmark
cursor = db.cursor()
cursor.execute(*Pstyle.convert("numeric", sqlite3.paramstyle, "select * from tbl1 where id=:2 and val=:1", ("val1", 1)))
# -> cursor.execute("SELECT * FROM tbl1 WHERE id=? AND val=?", (1, "val1"))
```

## wrap DB connection instance

```python
import sqlite3
from pstyle.wrapper import DBWrapper

db = sqlite3.connect(":memory:")
print("paramstyle:", sqlite3.paramstyle)    # qmark
db2 = DBWrapper(db, sqlite3.paramstyle, "numeric")
cursor = db2.cursor()
cursor.execute("select * from tbl1 where id=:2 and val=:1", ("val1", 1))
# -> SELECT * FROM tbl1 WHERE id=? AND val=?, (1, "val1")
result = cursor.fetchone()
```

## wrap cursor instance

```python
import sqlite3
from pstyle.wrapper import CursorWrapper

db = sqlite3.connect(":memory:")
print("paramstyle:", sqlite3.paramstyle)    # qmark
cursor = CursorWrapper(db.cursor(), sqlite3.paramstyle, "numeric")
cursor.execute("select * from tbl1 where id=:2 and val=:1", ("val1", 1))
# -> SELECT * FROM tbl1 WHERE id=? AND val=?, (1, "val1")
result = cursor.fetchone()
```

## try Python REPL with db connection

```
# pstyle try-db 'sqlite3://:memory:'
db(qmark): db.execute(...)
wrapped(auto): wrapped.execute(...)
Python 3.12.4 (main, Jun 20 2024, 00:32:08) [Clang 15.0.0 (clang-1500.3.9.4)]
Type 'copyright', 'credits' or 'license' for more information
IPython 8.21.0 -- An enhanced Interactive Python. Type '?' for help.

In [1]: wrapped.execute("create table tbl1 (id integer, val varchar)")
Out[1]: <sqlite3.Cursor at 0x10c519040>

In [2]: wrapped.execute("insert into tbl1 (id, val) values (%s, %s), (%s, %s)", (1, "val1", 2, "val2")).fetchall()
Out[2]: []

In [3]: wrapped.execute("select * from tbl1").fetchall()
Out[3]: [(1, 'val1'), (2, 'val2')]

In [4]: wrapped.execute("select * from tbl1 where id=:key1", dict(key1=1)).fetchall()
Out[4]: [(1, 'val1')]

In [5]: wrapped.execute("select * from tbl1 where id=:key1", dict(key1=2)).fetchall()
Out[5]: [(2, 'val2')]
```
