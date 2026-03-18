from pathlib import Path
from unittest import mock

import pytest
from fixtures import empty_directory, pyproject, with_git, with_tempdir, with_two_files

from magicli import cli, get_description, get_homepage, get_output, get_project_name


def module(name):
    module = type(pytest)(name)
    module.__doc__ = "docstring"
    return module


@mock.patch("builtins.input", lambda _: "two")
def test_correct_name_input(with_two_files):
    cli()

    path = Path("pyproject.toml")
    assert path.exists()
    with path.open() as f:
        assert 'name = "two"' in f.read()


@mock.patch("builtins.input", lambda *_: "y")
def test_automatic_name(pyproject):
    cli()

    assert 'name = "module"' in pyproject.read_text()


@mock.patch("builtins.input", lambda *args: "y")
def test_overwrite_pyproject_toml(pyproject):
    cli()

    assert 'name = "module"' in pyproject.read_text()


@mock.patch("builtins.input", lambda *args: "")
def test_empty_cli_name_failure(with_two_files):
    with pytest.raises(SystemExit) as error:
        get_project_name()
    assert error.value.code == 1


def test_with_git_repo(capsys, with_git):
    cli(name="_")
    out, _ = capsys.readouterr()

    without_git = (
        "Error: Not a git repo. Run `git init`. Specify version with `git tag`.\n"
    )
    with_git = "You can specify the version with `git tag`\n"
    assert out.endswith(with_git)
    assert without_git not in out


def test_without_git_repo(capsys, empty_directory):
    cli(name="_")
    out, _ = capsys.readouterr()

    without_git = (
        "Error: Not a git repo. Run `git init`. Specify version with `git tag`.\n"
    )
    with_git = "You can specify the version with `git tag`\n"
    assert out.endswith(without_git)
    assert with_git not in out


def test_get_output():
    assert get_output("ls") != None
    assert get_output("-") == None


def test_get_homepage():
    for url in [
        "https://github.com/PatrickElmer/magicli.git",
        "git@github.com:PatrickElmer/magicli.git",
    ]:
        assert get_homepage(url) == "https://github.com/PatrickElmer/magicli"


def test_get_description():
    assert get_description("magicli") != None


def test_cli_with_kwargs(with_tempdir):
    cli(
        name="name",
        author="Patrick Elmer",
        email="patrick@elmer.ws",
        readme="README.md",
        license="LICENSE",
        description="docstring",
        homepage="https://github.com/PatrickElmer/magicli",
    )
    assert (
        Path("pyproject.toml").read_text()
        == """\
[project]
name = "name"
dynamic = ["version"]
dependencies = ["magicli<3"]
authors = [{name="Patrick Elmer", email="patrick@elmer.ws"}]
readme = "README.md"
license-files = ["LICENSE"]
description = "docstring"

[project.scripts]
name = "magicli:magicli"

[project.urls]
Home = "https://github.com/PatrickElmer/magicli"

[build-system]
requires = ["setuptools>=80", "setuptools-scm[simple]>=8"]
build-backend = "setuptools.build_meta"
"""
    )
