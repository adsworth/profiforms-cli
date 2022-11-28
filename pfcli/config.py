from collections import UserDict
import os
from pathlib import Path

import click
import tomli


CONFIG_FILENAME = "package.toml"
BUILD_DIR = "_build"
BUILD_DIR_FILE = ".builddir"
RS_PACKAGE_CONFIGURATION = "rs_package_configuration.xml"

_DEBUG = False


def set_debug(debug: bool):
    global _DEBUG
    _DEBUG = debug


def decho(msg: str):
    if _DEBUG:
        click.echo(msg)


class Config(UserDict):
    pass


def load(path: Path):
    config_filename = os.path.join(path, CONFIG_FILENAME)

    if not os.path.exists(config_filename):
        raise click.UsageError(message)(
            f"{CONFIG_FILENAME} not found in {path}. This is not a pfcli package."
        )

    _toml = tomli.load(open(config_filename, "rb"))

    return Config(_toml)
