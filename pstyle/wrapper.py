from .convert import Pstyle


class CursorWrapper:
    """wrapper of DB cursor object"""

    def __init__(self, cursor, orig_paramstyle: str, paramstyle: str):
        self._cursor = cursor
        self._orig_paramstyle = orig_paramstyle
        self._paramstyle = paramstyle

    def execute(self, operation, parameters=()):
        op, a = Pstyle.convert(self._paramstyle, self._orig_paramstyle, operation, parameters)
        return self._cursor.execute(op, a)

    def executemany(self, operation, seq_of_parameters=[]):
        op = None
        sop = []
        for p in seq_of_parameters:
            op1, p1 = Pstyle.convert(self._paramstyle, self._orig_paramstyle, operation, p)
            if op is None:
                op = op1
            assert op == op1
            sop.append(p1)
        if op is not None:
            return self._cursor.executemany(op, sop)

    def __getattr__(self, name):
        return getattr(self._cursor, name)


class DBWrapper:
    """wrapper of DB connection object"""

    def __init__(self, db, orig_paramstyle: str, paramstyle: str):
        self._db = db
        self.paramstyle = paramstyle
        self._orig_paramstyle = orig_paramstyle

    def cursor(self):
        return CursorWrapper(self._db.cursor(), self._orig_paramstyle, self.paramstyle)

    def execute(self, operation, parameters=()):
        return self.cursor().execute(operation, parameters)

    def executemany(self, operation, set_of_parameters=[]):
        return self.cursor().executemany(operation, set_of_parameters)

    def __getattr__(self, name):
        return getattr(self._db, name)
