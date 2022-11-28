import os
from pathlib import Path

import click

from pfcli import config
from pfcli.package import Package, load_package
from pfcli.builder import Builder


@click.group()
@click.option("--debug/--no-debug", default=False)
@click.pass_context
def cli(ctx: click.Context, debug: bool):
    config.set_debug(debug)

    ctx.obj = load_package(Path.cwd())


@cli.command()
@click.pass_obj
def build(package: Package):
    """
    Build a package for the Redaktionssystem.
    """
    try:
        builder = Builder(package)

        builder.initialise_build_path()
        builder.copy_files()
        builder.generate_package_file()
        builder.zip_package()
    except (ValueError, KeyError) as e:
        raise click.UsageError(str(e))
    except OSError as os_error:
        raise click.UsageError(str(os_error))


if __name__ == "__main__":
    cli(auto_envvar_prefix="PFCLI")
