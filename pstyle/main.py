import click
import functools
import json
import sys
from urllib.parse import urlparse, ParseResult, parse_qsl
from typing import Any, Callable
from logging import getLogger
from .version import VERSION
from .convert import Pstyle, styles

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


@cli.command()
@verbose_option
@click.option("--from-style", type=click.Choice(styles+["auto"]))
@click.option("--to-style", type=click.Choice(styles))
@click.option("--args", multiple=True)
@click.option("--kwargs", type=str, help="json")
@click.option("--normalize/--original", default=True, show_default=True)
@click.argument("operation")
def convert(operation, args, kwargs, from_style, to_style, normalize):
    """convert SQL and params with specified paramstyle"""
    if kwargs:
        conv_arg: dict[str, Any] = json.loads(kwargs)
    else:
        conv_arg: tuple[str] = tuple(args)
    _log.debug("SQL(before): %s, args=%s", operation, conv_arg)
    result_op, result_args = Pstyle.convert(from_style, to_style, operation, conv_arg, normalize)
    _log.debug("SQL(after): %s, args=%s", result_op, result_args)
    click.echo(f"op: {result_op}")
    click.echo(f"args: {result_args}")


dbapis: dict[str, tuple[str, Callable[[ParseResult], Any]]] = {}

try:
    import sqlite3

    def sqlite3_connect(u: ParseResult):
        return sqlite3.connect(u.netloc+u.path)
    dbapis["sqlite3"] = (sqlite3.paramstyle, sqlite3_connect)
except ImportError:
    pass
try:
    import mysql.connector

    def mysql_connect(u: ParseResult):
        return mysql.connector.connect(
            host=u.hostname, port=u.port, user=u.username, password=u.password,
            database=u.path.lstrip("/"))
    dbapis["mysql"] = (mysql.connector.paramstyle, mysql_connect)
except ImportError:
    pass
try:
    import mariadb

    def mariadb_connect(u: ParseResult):
        return mariadb.connect(
            host=u.hostname, port=u.port, user=u.username, password=u.password,
            database=u.path.lstrip("/"))
    dbapis["mariadb"] = (mariadb.paramstyle, mariadb_connect)
except ImportError:
    pass
try:
    import psycopg2

    def psql_connect(u: ParseResult):
        return psycopg2.connect(
            host=u.hostname, port=u.port, user=u.username, password=u.password,
            dbname=u.path.lstrip("/"))
    dbapis["postgres"] = (psycopg2.paramstyle, psql_connect)
except ImportError:
    pass
try:
    import pyodbc

    def odbc_connect(u: ParseResult):
        params = dict(parse_qsl(u.query))
        return pyodbc.connect(u.path.lstrip("/"), **params)
    dbapis["odbc"] = (pyodbc.paramstyle, odbc_connect)
except ImportError:
    pass
try:
    import pymssql

    def mssql_connect(u: ParseResult):
        params = dict(parse_qsl(u.query))
        return pymssql.connect(
            host=u.hostname, port=u.port, user=u.username, password=u.password,
            database=u.path.lstrip("/"), **params)
    dbapis["mssql"] = (pymssql.paramstyle, mssql_connect)
except ImportError:
    pass
try:
    import oracledb

    def oracle_connect(u: ParseResult):
        params = dict(parse_qsl(u.query))
        return oracledb.connect(
            host=u.hostname, port=u.port, user=u.username, password=u.password,
            service_name=u.path.lstrip("/"), **params)
    dbapis["oracle"] = (oracledb.paramstyle, oracle_connect)
except ImportError:
    pass
try:
    import duckdb

    def duckdb_connect(u: ParseResult):
        params = dict(parse_qsl(u.query))
        return duckdb.connect(u.netloc+u.path, config=params)
    dbapis["duckdb"] = (duckdb.paramstyle, duckdb_connect)
except ImportError:
    pass
try:
    import firebird.driver

    def firebird_connect(u: ParseResult):
        return firebird.driver.connect(
            database=f"{u.hostname}:{u.port}{u.path}", user=u.username, password=u.password)
    dbapis["firebird"] = (firebird.driver.paramstyle, firebird_connect)
except ImportError:
    pass
try:
    # XXX: pydrda can't execute with paramters against derby
    import drda

    def drda_connect(u: ParseResult):
        return drda.connect(
            host=u.hostname, port=u.port, user=u.username, password=u.password,
            database=u.path.lstrip("/")+";create=true")
    dbapis["drda"] = (drda.paramstyle, drda_connect)
except ImportError:
    pass
try:
    import pymonetdb

    def monetdb_connect(u: ParseResult):
        return pymonetdb.connect(
            hostname=u.hostname, port=u.port, username=u.username, password=u.password,
            database=u.path.lstrip("/"))
    dbapis["monetdb"] = (pymonetdb.paramstyle, monetdb_connect)
except ImportError:
    pass
try:
    import pyhive.hive

    def hive_connect(u: ParseResult):
        params = dict(parse_qsl(u.query))
        return pyhive.hive.connect(
            host=u.hostname, port=u.port, username=u.username, password=u.password,
            database=u.path.lstrip("/"), **params)
    dbapis["hive"] = (pyhive.hive.paramstyle, hive_connect)
except ImportError:
    pass
try:
    import pyhive.presto

    def presto_connect(u: ParseResult):
        params = dict(parse_qsl(u.query))
        return pyhive.presto.connect(
            host=u.hostname, port=u.port, username=u.username, password=u.password,
            schema=u.path.lstrip("/"), **params)
    dbapis["presto"] = (pyhive.presto.paramstyle, presto_connect)
except ImportError:
    pass


@cli.command()
@verbose_option
@click.option("--output", type=click.File('w'), default=sys.stdout)
def list_drivers(output):
    json.dump(list(dbapis.keys()), output)


@cli.command()
@verbose_option
@click.option("--style", type=click.Choice(styles+["auto"]), default="auto", show_default=True)
@click.option("--normalize/--original", default=True, show_default=True)
@click.option("--ipython/--code", default=True, show_default=True)
@click.argument("dsn")
def try_db(dsn, style, normalize, ipython):
    if ipython:
        import IPython
    else:
        import readline  # noqa
        import code
    from .wrapper import DBWrapper
    parsed = urlparse(dsn)
    if parsed.scheme not in dbapis:
        raise click.BadArgumentUsage(f"{parsed.scheme} not found in {list(dbapis.keys())}")
    paramstyle, connector = dbapis.get(parsed.scheme)
    db = connector(parsed)
    wrapped = DBWrapper(db, paramstyle, style, normalize)
    click.echo(f"db({paramstyle}): db.execute(...)")
    click.echo(f"wrapped({style}): wrapped.execute(...)")
    names = {"dsn": dsn, "db": db, "wrapped": wrapped, "paramstyle": (paramstyle, style), "version": VERSION}
    if ipython:
        IPython.start_ipython(argv=[], user_ns=names)
    else:
        code.InteractiveConsole(locals=names).interact()


if __name__ == "__main__":
    cli()
