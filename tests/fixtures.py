import os
import shutil
from pathlib import Path

import pytest


@pytest.fixture()
def setup():
    cwd = Path.cwd()
    path = Path("tests", "tmp")

    # Make sure the directory does not exist
    if path.exists():
        shutil.rmtree(path)

    path.mkdir(exist_ok=True)
    Path(path, "module.py").touch()
    os.chdir(path)

    yield path

    os.chdir(cwd)
    shutil.rmtree(path)


@pytest.fixture()
def two_py():
    file = Path("two.py")
    file.touch()

    yield file

    file.unlink()


@pytest.fixture()
def pyproject_toml():
    file = Path("pyproject.toml")
    file.touch()

    yield file

    file.unlink()


@pytest.fixture()
def dotgit():
    dir = Path(".git")
    dir.mkdir(exist_ok=True)

    yield dir

    shutil.rmtree(dir)
