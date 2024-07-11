import sqlparse
from sqlparse.tokens import Token
from typing import Union, Callable
from logging import getLogger

_log = getLogger(__name__)

dictarg_styles = ["named", "pyformat"]
tuplearg_styles = ["qmark", "numeric", "format"]
styles = dictarg_styles + tuplearg_styles


class Pstyle:
    @classmethod
    def _parse_flatten(cls, operation) -> list[list[sqlparse.sql.Token]]:
        return [list(x.flatten()) for x in sqlparse.parse(operation)]

    @classmethod
    def _do1_numeric2qmark(cls, token: sqlparse.sql.Token, from_args: tuple, to_args: list) -> str:
        if token.value.startswith(":"):
            idx = int(token.value[1:])
            to_args.append(from_args[idx-1])   # numeric is 1-origin
            return "?"
        return token.value

    @classmethod
    def _do1_qmark2numeric(cls, token: sqlparse.sql.Token, from_args: tuple, to_args: list) -> str:
        if token.value == "?":
            to_args.append(from_args[len(to_args)])
            return f":{len(to_args)}"   # numeric is 1-origin
        return token.value

    @classmethod
    def _do1_named2qmark(cls, token: sqlparse.sql.Token, from_args: Union[tuple, dict], to_args: list) -> str:
        if token.value.startswith(":"):
            if isinstance(from_args, dict):
                name = token.value[1:]
                to_args.append(from_args.get(name))
                return "?"
            else:
                idx = int(token.value[1:])
                to_args.append(from_args[idx-1])
                return "?"
        return token.value

    @classmethod
    def _do1_qmark2named(cls, token: sqlparse.sql.Token, from_args: tuple, to_args: dict) -> str:
        if token.value == "?":
            name = f"arg{len(to_args)}"
            to_args[name] = from_args[len(to_args)]
            return f":{name}"
        return token.value

    @classmethod
    def _do1_qmark2pyformat(cls, token: sqlparse.sql.Token, from_args: tuple, to_args: dict) -> str:
        if token.value == "?":
            name = f"arg{len(to_args)}"
            to_args[name] = from_args[len(to_args)]
            return f"%({name})s"
        return token.value

    @classmethod
    def _do1_format2qmark(cls, token: sqlparse.sql.Token, from_args: tuple, to_args: list) -> str:
        if token.value.startswith("%"):
            to_args.append(from_args[len(to_args)])
            return "?"
        return token.value

    @classmethod
    def _do1_qmark2format(cls, token: sqlparse.sql.Token, from_args: tuple, to_args: list) -> str:
        if token.value == "?":
            to_args.append(from_args[len(to_args)])
            return "%s"
        return token.value

    @classmethod
    def _do1_pyformat2named(cls, token: sqlparse.sql.Token, from_args: Union[tuple, dict], to_args: dict) -> str:
        if isinstance(from_args, dict) and token.value.startswith("%("):
            name = token.value[2:].split(")")[0]
            to_args[name] = from_args[name]
            return f":{name}"
        elif token.value.startswith("%"):
            idx = len(to_args)
            name = f"arg{len(to_args)}"
            to_args[name] = from_args[idx]
            return f":{name}"
        return token.value

    @classmethod
    def _do1_named2pyformat(cls, token: sqlparse.sql.Token, from_args: Union[tuple, dict], to_args: dict) -> str:
        if token.value.startswith(":"):
            if isinstance(from_args, dict):
                name = token.value[1:]
                to_args[name] = from_args[name]
                return f"%({name})s"
            else:
                idx = int(token.value[1:])
                name = f"arg{len(to_args)}"
                to_args[name] = from_args[idx-1]  # 1-origin
                return f"%({name})s"
        return token.value

    @classmethod
    def _do1_pyformat2qmark(cls, token: sqlparse.sql.Token, from_args: Union[tuple, dict], to_args: list) -> str:
        if token.value.startswith("%("):
            name = token.value[2:].split(")")[0]
            to_args.append(from_args[name])
            return "?"
        elif token.value.startswith("%"):
            idx = len(to_args)
            to_args.append(from_args[idx])
            return "?"
        return token.value

    @classmethod
    def _do1_auto2qmark(cls, token: sqlparse.sql.Token, from_args: Union[dict, tuple], to_args: list) -> str:
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

    @classmethod
    def _do1_auto2named(cls, token: sqlparse.sql.Token, from_args: Union[dict, tuple], to_args: dict) -> str:
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

    @classmethod
    def _do_any2any(cls, operation: str, fn1: Callable, args: Union[tuple, dict],
                    arg_initializer=dict, normalize: bool = True) -> tuple[str, Union[tuple, dict]]:
        resarg: Union[list, dict] = arg_initializer()
        resop = []
        for sql in cls._parse_flatten(operation):
            for token in sql:
                if token.ttype == Token.Name.Placeholder:
                    resop.append(fn1(token, args, resarg))
                else:
                    if normalize:
                        resop.append(token.normalized)
                    else:
                        resop.append(token.value)
        if isinstance(resarg, list):
            resarg = tuple(resarg)
        resop_str = "".join(resop)
        _log.debug("any2any: %s -> %s, arg=%s", repr(operation), repr(resop_str), resarg)
        return resop_str, resarg

    @classmethod
    def convert(cls, from_style: str, to_style: str, operation: str, args: Union[tuple, dict] = (),
                normalize: bool = True) -> tuple[str, Union[tuple, dict]]:
        """convert paramstyle

        Args:
            from_style: [qmark|format|numeric|named|pyformat|auto]
            to_style: [qmark|format|numeric|named|pyformat]
            operation: SQL statement with placeholder
            args: argument to placeholder
            normalize: output is normalized or not
        Returns:
            result_sql, result_args
        """
        if from_style == to_style:
            return operation, args
        if hasattr(cls, f"_do1_{from_style}2{to_style}"):
            fn = getattr(cls, f"_do1_{from_style}2{to_style}")
            if callable(fn):
                if to_style in dictarg_styles:
                    _log.debug("do1(dict): %s to %s", from_style, to_style)
                    return cls._do_any2any(operation, fn, args, dict, normalize)
                else:
                    _log.debug("do1(tuple): %s to %s", from_style, to_style)
                    return cls._do_any2any(operation, fn, args, list, normalize)
        elif hasattr(cls, f"_do1_{from_style}2qmark") and hasattr(cls, f"_do1_qmark2{to_style}"):
            fn1 = getattr(cls, f"_do1_{from_style}2qmark")
            fn2 = getattr(cls, f"_do1_qmark2{to_style}")
            if callable(fn1) and callable(fn2):
                op, a = cls._do_any2any(operation, fn1, args, list, normalize)
                _log.debug("qmark1: op=%s, arg=%s", op, a)
                if to_style in dictarg_styles:
                    _log.debug("do1-q(dict): %s to %s", from_style, to_style)
                    return cls._do_any2any(op, fn2, a, dict, normalize)
                else:
                    _log.debug("do1-q(tuple): %s to %s", from_style, to_style)
                    return cls._do_any2any(op, fn2, a, list, normalize)
        raise NotImplementedError(f"not implemented: from={from_style}, to={to_style}")
