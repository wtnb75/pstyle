import click
import functools
import sqlparse
from sqlparse.tokens import Token
from typing import Any, Union, Callable
import json
from logging import getLogger
from .version import VERSION

_log = getLogger(__name__)


@click.group(invoke_without_command=True)
@click.pass_context
@click.version_option(version=VERSION, prog_name="pstyle")
def cli(ctx):
    if ctx.invoked_subcommand is None:
        print(ctx.get_help())


def verbose_option(func):
    @click.option("--verbose/--quiet", default=None)
    @functools.wraps(func)
    def _(verbose, *args, **kwargs):
        from logging import basicConfig
        level = "INFO"
        if verbose:
            level = "DEBUG"
        elif verbose is False:
            level = "WARNING"
        basicConfig(level=level, format="%(asctime)s %(levelname)s %(message)s")
        return func(*args, **kwargs)
    return _


dictarg_styles = ["named", "pyformat"]
tuplearg_styles = ["qmark", "numeric", "format"]
styles = dictarg_styles + tuplearg_styles


class Pstyle:
    def __init__(self):
        pass

    def parse_flatten(self, operation) -> list[list[sqlparse.sql.Token]]:
        return [list(x.flatten()) for x in sqlparse.parse(operation)]

    def do1_numeric2qmark(self, token: sqlparse.sql.Token, from_args: tuple, to_args: list) -> str:
        if token.value.startswith(":"):
            idx = int(token.value[1:])
            to_args.append(from_args[idx-1])   # numeric is 1-origin
            return "?"
        return token.value

    def do1_qmark2numeric(self, token: sqlparse.sql.Token, from_args: tuple, to_args: list) -> str:
        if token.value == "?":
            to_args.append(from_args[len(to_args)])
            return f":{len(to_args)}"   # numeric is 1-origin
        return token.value

    def do1_named2qmark(self, token: sqlparse.sql.Token, from_args: dict, to_args: list) -> str:
        if token.value.startswith(":"):
            name = token.value[1:]
            to_args.append(from_args.get(name))
            return "?"
        return token.value

    def do1_qmark2named(self, token: sqlparse.sql.Token, from_args: tuple, to_args: dict) -> str:
        if token.value == "?":
            name = f"arg{len(to_args)}"
            to_args[name] = from_args[len(to_args)]
            return f":{name}"
        return token.value

    def do1_qmark2pyformat(self, token: sqlparse.sql.Token, from_args: tuple, to_args: dict) -> str:
        if token.value == "?":
            name = f"arg{len(to_args)}"
            to_args[name] = from_args[len(to_args)]
            return f"%({name})s"
        return token.value

    def do1_format2qmark(self, token: sqlparse.sql.Token, from_args: tuple, to_args: list) -> str:
        if token.value.startswith("%"):
            to_args.append(from_args[len(to_args)])
            return "?"
        return token.value

    def do1_qmark2format(self, token: sqlparse.sql.Token, from_args: tuple, to_args: list) -> str:
        if token.value == "?":
            to_args.append(from_args[len(to_args)])
            return "%s"
        return token.value

    def do1_pyformat2named(self, token: sqlparse.sql.Token, from_args: dict, to_args: dict) -> str:
        if token.value.startswith("%("):
            name = token.value[2:].split(")")[0]
            to_args[name] = from_args[name]
            return f":{name}"
        return token.value

    def do1_named2pyformat(self, token: sqlparse.sql.Token, from_args: dict, to_args: dict) -> str:
        if token.value.startswith(":"):
            name = token.value[1:]
            to_args[name] = from_args[name]
            return f"%({name})s"
        return token.value

    def do1_pyformat2qmark(self, token: sqlparse.sql.Token, from_args: dict, to_args: list) -> str:
        if token.value.startswith("%("):
            name = token.value[2:].split(")")[0]
            to_args.append(from_args[name])
            return "?"
        return token.value

    def do1_auto2qmark(self, token: sqlparse.sql.Token, from_args: Union[dict, tuple], to_args: list) -> str:
        if token.value.startswith("%("):  # pyformat
            name = token.value[2:].split(")")[0]
            to_args.append(from_args[name])
            return "?"
        if token.value.startswith(":"):
            try:
                idx = int(token.value[1:])   # numeric
                to_args.append(from_args[idx-1])   # numeric is 1-origin
                return "?"
            except ValueError:
                name = token.value[1:]   # named
                to_args.append(from_args.get(name))
                return "?"
        if token.value.startswith("%"):   # format
            to_args.append(from_args[len(to_args)])
            return "?"
        if token.value == "?":   # qmark
            to_args.append(from_args[len(to_args)])
            return "?"
        return token.value

    def do1_auto2named(self, token: sqlparse.sql.Token, from_args: Union[dict, tuple], to_args: dict) -> str:
        iname = f"arg{len(to_args)}"
        if token.value.startswith("%("):  # pyformat
            name = token.value[2:].split(")")[0]
            to_args[name] = from_args[name]
            return f":{name}"
        if token.value.startswith(":"):
            try:
                idx = int(token.value[1:])   # numeric
                to_args[iname] = from_args[idx-1]   # numeric is 1-origin
                return f":{iname}"
            except ValueError:
                name = token.value[1:]   # named
                to_args[name] = from_args[name]
                return f":{name}"
        if token.value.startswith("%"):   # format
            to_args[iname] = from_args[len(to_args)]
            return f":{iname}"
        if token.value == "?":   # qmark
            to_args[iname] = from_args[len(to_args)]
            return f":{iname}"
        return token.value

    def do_any2any(self, operation: str, fn1: Callable, args: Union[tuple, dict],
                   arg_initializer=dict, normalize: bool = True) -> tuple[str, Union[tuple, dict]]:
        resarg: Union[list, dict] = arg_initializer()
        resop = []
        for sql in self.parse_flatten(operation):
            for token in sql:
                _log.debug("token %s / %s", token.ttype, token.value)
                if token.ttype == Token.Name.Placeholder:
                    _log.debug("placeholder: %s", token.value)
                    resop.append(fn1(token, args, resarg))
                else:
                    if normalize:
                        resop.append(token.normalized)
                    else:
                        resop.append(token.value)
        if isinstance(resarg, list):
            resarg = tuple(resarg)
        return "".join(resop), resarg

    def convert(self, from_style: str, to_style: str, operation: str, args: Union[tuple, dict] = (),
                normalize: bool = True):
        if from_style == to_style:
            return operation, args
        if hasattr(self, f"do_{from_style}2{to_style}"):
            fn = getattr(self, f"do_{from_style}2{to_style}")
            if callable(fn):
                _log.debug("do: %s to %s", from_style, to_style)
                return fn(operation, args)
        elif hasattr(self, f"do1_{from_style}2{to_style}"):
            fn = getattr(self, f"do1_{from_style}2{to_style}")
            if callable(fn):
                if to_style in dictarg_styles:
                    _log.debug("do1(dict): %s to %s", from_style, to_style)
                    return self.do_any2any(operation, fn, args, dict, normalize)
                else:
                    _log.debug("do1(tuple): %s to %s", from_style, to_style)
                    return self.do_any2any(operation, fn, args, list, normalize)
        elif hasattr(self, f"do_{from_style}2qmark") and hasattr(self, f"do_qmark2{to_style}"):
            fn1 = getattr(self, f"do_{from_style}2qmark")
            fn2 = getattr(self, f"do_qmark2{to_style}")
            if callable(fn1) and callable(fn2):
                op, a = fn1(operation, args)
                _log.debug("qmark: op=%s, arg=%s", op, a)
                return fn2(op, a)
        elif hasattr(self, f"do1_{from_style}2qmark") and hasattr(self, f"do1_qmark2{to_style}"):
            fn1 = getattr(self, f"do1_{from_style}2qmark")
            fn2 = getattr(self, f"do1_qmark2{to_style}")
            if callable(fn1) and callable(fn2):
                op, a = self.do_any2any(operation, fn1, args, list, normalize)
                _log.debug("qmark1: op=%s, arg=%s", op, a)
                if to_style in dictarg_styles:
                    _log.debug("do1-q(dict): %s to %s", from_style, to_style)
                    return self.do_any2any(op, fn2, a, dict, normalize)
                else:
                    _log.debug("do1-q(tuple): %s to %s", from_style, to_style)
                    return self.do_any2any(op, fn2, a, list, normalize)
        raise NotImplementedError(f"not implemented: from={from_style}, to={to_style}")


class CursorWrapper:
    def __init__(self, cursor, orig_paramstyle: str, paramstyle: str):
        self._cursor = cursor
        self._orig_paramstyle = orig_paramstyle
        self._paramstyle = paramstyle
        self._pstyle = Pstyle()

    def execute(self, operation, parameters=()):
        op, a = self._pstyle.convert(self._paramstyle, self._orig_paramstyle, operation, parameters)
        return self._cursor.execute(op, a)

    def executemany(self, operation, seq_of_parameters=[]):
        op = None
        sop = []
        for p in seq_of_parameters:
            op1, p1 = self._pstyle.convert(self._paramstyle, self._orig_paramstyle, operation, p)
            if op is None:
                op = op1
            assert op == op1
            sop.append(p1)
        if op is not None:
            return self._cursor.executemany(op, sop)

    def __getattr__(self, name, defval=None):
        return getattr(self._cursor, name, defval)


class DBWrapper:
    def __init__(self, db, orig_paramstyle: str, paramstyle: str):
        self._db = db
        self.paramstyle = paramstyle
        self._orig_paramstyle = orig_paramstyle

    def cursor(self):
        return CursorWrapper(self._db.cursor(), self._orig_paramstyle, self.paramstyle)

    def __getattr__(self, name, defval=None):
        return getattr(self._db, name, defval)


@cli.command()
@verbose_option
@click.option("--from-style", type=click.Choice(styles+["auto"]))
@click.option("--to-style", type=click.Choice(styles))
@click.option("--args", multiple=True)
@click.option("--kwargs", type=str, help="json")
@click.option("--normalize/--original", default=True, show_default=True)
@click.argument("operation")
def conv(operation, args, kwargs, from_style, to_style, normalize):
    if kwargs:
        conv_arg: dict[str, Any] = json.loads(kwargs)
    else:
        conv_arg: tuple[str] = tuple(args)
    result_op, result_args = Pstyle().convert(from_style, to_style, operation, conv_arg, normalize)
    click.echo(f"op: {result_op}")
    click.echo(f"args: {result_args}")


if __name__ == "__main__":
    cli()
