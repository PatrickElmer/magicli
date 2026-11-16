import sys
from unittest import mock

import pytest

from magicli import (
    cli,
    get_description,
    get_homepage,
    get_license_expression,
    get_output,
    get_project_name,
)


@mock.patch("builtins.input", lambda _: "two")
def test_correct_name_input(project):
    path = project("module.py", "two.py")
    cli()

    assert 'name = "two"' in (path / "pyproject.toml").read_text(encoding="utf-8")


@mock.patch("builtins.input", lambda *_: "y")
def test_overwrite_pyproject_toml(project):
    path = project("pyproject.toml", "module.py")
    cli()

    assert 'name = "module"' in (path / "pyproject.toml").read_text(encoding="utf-8")


@mock.patch("builtins.input", lambda *_: "")
def test_empty_cli_name_failure(project):
    project("module.py", "two.py")
    with pytest.raises(SystemExit) as error:
        get_project_name()
    assert error.value.code == 1


def test_with_git_repo(capsys, project):
    project(git=True)
    cli(name="_")
    assert "Specify the version with `git tag`\n" in capsys.readouterr().err


def test_without_git_repo(capsys, project):
    project()
    cli(name="_")
    assert "Not a git repo. Run `git init`\n" in capsys.readouterr().err


def test_get_output():
    assert get_output(f"{sys.executable} -c print(1)") == "1"
    assert get_output("-") is None


@pytest.mark.parametrize(
    "url",
    [
        "https://github.com/PatrickElmer/magicli.git",
        "git@github.com:PatrickElmer/magicli.git",
    ],
)
def test_get_homepage(url):
    assert get_homepage(url) == "https://github.com/PatrickElmer/magicli"


def test_get_description(project):
    project(**{"module.py": '"""First  paragraph\nof docstring.\n\nSecond paragraph."""'})
    assert get_description("module") == "First paragraph of docstring."


def test_get_license_expression():
    assert get_license_expression("Apache License") == "Apache-2.0"
    assert get_license_expression(" GNU GENERAL PUBLIC LICENSE ") == "GPL-3.0-or-later"
    assert get_license_expression("") is None


def test_cli_with_license(project):
    path = project(LICENSE="MIT License")
    cli(name="name", author="Patrick Elmer", email="patrick@elmer.ws")
    pyproject = (path / "pyproject.toml").read_text(encoding="utf-8")
    assert 'license = "MIT"' in pyproject
    assert 'license-files = ["LICENSE"]' in pyproject


def test_cli_with_kwargs(capsys, project):
    path = project("README.md", "LICENSE")
    cli(
        name="name",
        author="Patrick Elmer",
        email="patrick@elmer.ws",
        description="docstring",
        homepage="https://github.com/PatrickElmer/magicli",
    )
    assert "Unknown license: LICENSE\n" in capsys.readouterr().err
    assert (
        (path / "pyproject.toml").read_text(encoding="utf-8")
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
