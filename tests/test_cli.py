import logging
from pathlib import Path
from unittest import mock

import pytest
from fixtures import (
    empty_directory,
    pyproject,
    with_git,
    with_license,
    with_readme_and_license,
    with_tempdir,
    with_two_files,
)

from magicli import (
    cli,
    get_description,
    get_homepage,
    get_license_expression,
    get_output,
    get_project_name,
)


def module(name):
    module = type(pytest)(name)
    module.__doc__ = "docstring"
    return module


@mock.patch("builtins.input", lambda _: "two")
def test_correct_name_input(with_two_files):
    cli()

    path = Path("pyproject.toml")
    assert path.exists()
    with path.open(encoding="utf-8") as f:
        assert 'name = "two"' in f.read()


@mock.patch("builtins.input", lambda *_: "y")
def test_automatic_name(pyproject):
    cli()

    assert 'name = "module"' in pyproject.read_text()


@mock.patch("builtins.input", lambda *_: "y")
def test_overwrite_pyproject_toml(pyproject):
    cli()

    assert 'name = "module"' in pyproject.read_text()


@mock.patch("builtins.input", lambda *_: "")
def test_empty_cli_name_failure(with_two_files):
    with pytest.raises(SystemExit) as error:
        get_project_name()
    assert error.value.code == 1


def test_with_git_repo(caplog, with_git):
    cli(name="_")
    assert "Specify the version with `git tag`" in caplog.messages


def test_without_git_repo(caplog, empty_directory):
    cli(name="_")
    assert "Not a git repo. Run `git init`" in caplog.messages


def test_get_output():
    assert get_output("ls") is not None
    assert get_output("-") is None


def test_get_homepage():
    for url in [
        "https://github.com/PatrickElmer/magicli.git",
        "git@github.com:PatrickElmer/magicli.git",
    ]:
        assert get_homepage(url) == "https://github.com/PatrickElmer/magicli"


def test_get_description():
    assert get_description("magicli") is not None


def test_get_license_expression():
    assert get_license_expression("Apache License") == "Apache-2.0"
    assert get_license_expression(" GNU GENERAL PUBLIC LICENSE ") == "GPL-3.0-or-later"
    assert get_license_expression("") is None


def test_cli_with_license(with_license):
    Path(with_license, "LICENSE").write_text("MIT License", encoding="utf-8")
    cli(name="name", author="Patrick Elmer", email="patrick@elmer.ws")
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")
    assert 'license = "MIT"' in pyproject
    assert 'license-files = ["LICENSE"]' in pyproject


def test_cli_with_kwargs(caplog, with_readme_and_license):
    cli(
        name="name",
        author="Patrick Elmer",
        email="patrick@elmer.ws",
        description="docstring",
        homepage="https://github.com/PatrickElmer/magicli",
    )
    assert any(msg == "Unknown license: LICENSE" for msg in caplog.messages)
    assert (
        Path("pyproject.toml").read_text(encoding="utf-8")
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
