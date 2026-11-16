import subprocess
import sys

import pytest

MODULE_NAME = "magicli_testmod"


def git_run(*args):
    subprocess.run(
        ["git", "-c", "user.name=test", "-c", "user.email=test@example.com", *args],
        check=True,
    )


def magicli_testmod():
    "-V, --version"
    print("name")


def command():
    "-v, --version"
    print("command")


@pytest.fixture
def project(tmp_path, monkeypatch):
    """
    Factory that turns `tmp_path` into the working directory and populates it.
    Positional arguments are touched as empty files, keyword arguments are written
    with their value as content. `git=True` initializes a git repository and `tag`
    creates an initial commit with that tag. Git is isolated from the user's
    config and from repositories above `tmp_path`.
    """
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", "/dev/null")
    monkeypatch.setenv("GIT_CONFIG_SYSTEM", "/dev/null")
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))

    def make(*files, git=False, tag=None, **contents):
        if git or tag:
            git_run("init", "--quiet")
        if tag:
            git_run("commit", "--allow-empty", "--quiet", "--message=init")
            git_run("tag", tag)
        for filename in files:
            (tmp_path / filename).touch()
        for filename, content in contents.items():
            (tmp_path / filename).write_text(content, encoding="utf-8")
        return tmp_path

    return make


@pytest.fixture
def fake_module(monkeypatch):
    """
    Factory that registers a fake module in `sys.modules` so `magicli` imports it.
    Functions are added under their `__name__`, keyword arguments under the given
    name. All of them are listed in `__all__` unless `all_=False`.
    """

    def make(*functions, version=None, all_=True, **named):
        module = type(sys)(MODULE_NAME)
        module.__doc__ = "docstring"
        module.__version__ = version
        named = {function.__name__: function for function in functions} | named
        for name, function in named.items():
            setattr(module, name, function)
        if all_:
            module.__all__ = list(named)
        monkeypatch.setitem(sys.modules, MODULE_NAME, module)
        return module

    return make


@pytest.fixture
def module(fake_module):
    """Fake module with a main function named like the module and a `command`."""
    return fake_module(magicli_testmod, command)


@pytest.fixture
def run(monkeypatch):
    """Runs `magicli` with the given command-line arguments."""
    from magicli import magicli

    def run_magicli(*argv, prog=MODULE_NAME):
        monkeypatch.setattr(sys, "argv", [prog, *argv])
        magicli()

    return run_magicli
