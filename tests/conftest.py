import os
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest


def _setup(filenames, dirname=None):
    cwd = Path.cwd()
    directory = TemporaryDirectory()
    if dirname:
        Path(directory.name, dirname).mkdir()
        os.chdir(directory.name)
    else:
        os.chdir(directory.name)
    for filename in filenames:
        Path(directory.name, filename).touch()
    return directory, cwd


def _teardown(directory, cwd):
    directory.cleanup()
    os.chdir(cwd)


@pytest.fixture
def with_tempdir():
    directory, cwd = _setup(["module.py"])
    yield directory.name
    _teardown(directory, cwd)


@pytest.fixture
def with_license():
    directory, cwd = _setup(["LICENSE"])
    yield directory.name
    _teardown(directory, cwd)


@pytest.fixture
def with_readme_and_license():
    directory, cwd = _setup(["README.md", "LICENSE"])
    yield directory.name
    _teardown(directory, cwd)


@pytest.fixture
def with_two_files():
    directory, cwd = _setup(["module.py", "two.py"])
    yield
    _teardown(directory, cwd)


@pytest.fixture
def pyproject():
    directory, cwd = _setup(["pyproject.toml", "module.py"])
    yield Path(directory.name, "pyproject.toml")
    _teardown(directory, cwd)


@pytest.fixture
def with_git():
    directory, cwd = _setup([], dirname=".git")
    yield
    _teardown(directory, cwd)


@pytest.fixture
def empty_directory():
    directory, cwd = _setup([])
    yield
    _teardown(directory, cwd)
