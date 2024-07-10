import click
import functools
import json
from typing import Any
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
def conv(operation, args, kwargs, from_style, to_style, normalize):
    if kwargs:
        conv_arg: dict[str, Any] = json.loads(kwargs)
    else:
        conv_arg: tuple[str] = tuple(args)
    result_op, result_args = Pstyle.convert(from_style, to_style, operation, conv_arg, normalize)
    click.echo(f"op: {result_op}")
    click.echo(f"args: {result_args}")


if __name__ == "__main__":
    cli()
