import sys
from types import SimpleNamespace

import pytest

from magicli import magicli

MODULE_NAME = "magicli_testmod"


def magicli_testmod():
    "-V, --version"
    print("main")


def command():
    "-v, --version"
    print("command")


@pytest.fixture
def git_output(monkeypatch):
    """
    Replaces `magicli.get_output` so no git process runs. Map argument tuples to the
    output to return, e.g. `git_output["git", "tag"] = "v0.1.0"`. Unmapped commands
    return None, like a failing command.
    """
    outputs = {}
    monkeypatch.setattr(
        "magicli.get_output", lambda command: outputs.get(tuple(command))
    )
    return outputs


@pytest.fixture
def project(tmp_path, monkeypatch, git_output):
    """
    Factory that turns `tmp_path` into the working directory and populates it.
    Positional arguments are touched as empty files, keyword arguments are written
    with their value as content and `git=True` creates a `.git` directory. Git calls
    are answered by the `git_output` fixture.
    """
    monkeypatch.chdir(tmp_path)

    def make(*files, git=False, **contents):
        if git:
            (tmp_path / ".git").mkdir()
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
    name. All of them are listed in `__all__` unless `all_=False`. `doc` and
    `version` set `__doc__` and `__version__`; `__version__` is only set if given.
    """

    def make(*functions, doc=None, version=None, all_=True, **named):
        module = type(sys)(MODULE_NAME)
        module.__doc__ = doc
        if version is not None:
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
def module_functions():
    """A main function named like the module and a `command`, for `fake_module`."""
    return magicli_testmod, command


@pytest.fixture
def module(fake_module, module_functions):
    """Fake module with the default `module_functions`."""
    return fake_module(*module_functions)


@pytest.fixture
def run(monkeypatch, capsys):
    """
    Runs `magicli` with the given command-line arguments. Returns the exit `code`
    (None if `magicli` returned or exited without a code) and the captured `out`.
    """

    def run_magicli(*argv, prog=MODULE_NAME):
        monkeypatch.setattr(sys, "argv", [prog, *argv])
        try:
            magicli()
            code = None
        except SystemExit as exc:
            code = exc.code
        return SimpleNamespace(code=code, out=capsys.readouterr().out)

    return run_magicli
