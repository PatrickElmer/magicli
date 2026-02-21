from pathlib import Path
from unittest import mock

import pytest
from fixtures import pyproject_toml, setup, two_py, dotgit

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


def test_on_git_repo(capsys, setup):
    cli()
    out, _ = capsys.readouterr()

    with_git = (
        "Error: Not a git repo. Run `git init`. Specify version with `git tag`.\n"
    )
    without_git = "You can specify the version with `git tag`\n"
    assert out.endswith(with_git)
    assert without_git not in out


def test_git_repo(capsys, setup, dotgit):
    cli()
    out, _ = capsys.readouterr()

    with_git = (
        "Error: Not a git repo. Run `git init`. Specify version with `git tag`.\n"
    )
    without_git = "You can specify the version with `git tag`\n"
    assert out.endswith(without_git)
    assert with_git not in out
