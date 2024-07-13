import click
import functools
import json
from urllib.parse import urlparse
from typing import Any
from logging import getLogger
from .version import VERSION
from .convert import Pstyle, styles
from .load_drivers import dbapis

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


@cli.command()
@verbose_option
def list_drivers():
    click.echo(json.dumps(list(dbapis.keys())))


@cli.command()
@verbose_option
@click.option("--style", type=click.Choice(styles+["auto"]), default="auto", show_default=True)
@click.option("--normalize/--original", default=True, show_default=True)
@click.option("--ipython/--code", default=True, show_default=True)
@click.argument("dsn")
def try_db(dsn, style, normalize, ipython):
    if ipython:
        try:
            import IPython
        except ImportError:
            _log.warning("cannot import ipython")
            ipython = False
    if not ipython:
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
