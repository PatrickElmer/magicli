import pytest
from pathlib import Path
from unittest import mock
from magicli import cli
from fixtures import setup, two_py, pyproject_toml


@mock.patch("builtins.input", lambda _: "two")
def test_correct_name_input(setup, two_py):
    cli()

    path = Path("pyproject.toml")
    assert path.exists()
    with path.open() as f:
        assert 'name = "two"' in f.read()


@mock.patch("builtins.input", lambda _: "one")
def test_wrong_name_input(setup, two_py):
    with pytest.raises(SystemExit) as error:
        cli()
    assert error.value.code != 1


@mock.patch("builtins.input", lambda *args: "n")
def test_dont_overwrite_pyproject_toml(setup, pyproject_toml):
    with pytest.raises(SystemExit) as error:
        cli()
    assert error.value.code == 1


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
