from pathlib import Path
from unittest import mock

import pytest
from fixtures import pyproject_toml, setup, two_py

from magicli import cli, get_project_name


@mock.patch("builtins.input", lambda _: "two")
def test_correct_name_input(setup, two_py):
    cli()

    path = Path("pyproject.toml")
    assert path.exists()
    with path.open() as f:
        assert 'name = "two"' in f.read()


@mock.patch("builtins.input", lambda *args: "n")
def test_automatic_name(setup):
    cli()
    with Path("pyproject.toml").open() as f:
        assert 'name = "module"' in f.read()


@mock.patch("builtins.input", lambda *args: "y")
def test_overwrite_pyproject_toml(setup, pyproject_toml):
    cli()
    with pyproject_toml.open() as f:
        assert 'name = "module"' in f.read()


@mock.patch("builtins.input", lambda *args: "")
def test_empty_cli_name_failure(setup, two_py):
    with pytest.raises(SystemExit) as error:
        get_project_name()
    assert error.value.code == 1
