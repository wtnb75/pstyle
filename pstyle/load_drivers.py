from urllib.parse import ParseResult, parse_qsl
from typing import Any, Callable

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
