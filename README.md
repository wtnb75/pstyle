# Python DB-API paramstyle converter

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
result = cursor.fetchone()
```
