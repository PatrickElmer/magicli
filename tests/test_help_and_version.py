import pytest

from magicli import help_from_function, help_from_module


def f1(arg, kwarg=1): ...


def test_help_from_function():
    assert help_from_function(f1) == "usage:\n  f1 arg [--kwarg]"


def test_help_from_function_with_name():
    assert help_from_function(f1, "name") == "usage:\n  name f1 arg [--kwarg]"


USAGE = "usage:\n  {name} command\n\ncommands:\n  command"


@pytest.mark.parametrize(
    ("version", "commands", "expected"),
    [
        (None, {"command": f1}, USAGE),
        ("0.1.2", {"command": f1}, "{name} 0.1.2\n\n" + USAGE),
        ("0.1.2", {}, "{name} 0.1.2"),
        (None, {}, ""),
    ],
    ids=["commands", "commands_and_version", "version_only", "empty"],
)
def test_help_from_module(fake_module, version, commands, expected):
    module = fake_module(version=version, **commands)
    assert help_from_module(module) == expected.format(name=module.__name__)


def test_help_message_for_unknown_command(fake_module, run):
    def magicli_testmod(): ...
    def command(): ...
    def command_2(): ...

    module = fake_module(magicli_testmod, command, command_2)
    assert (
        run("unknown_command").code
        == f"""\
unknown_command: unknown command

usage:
  {module.__name__}
  {module.__name__} <command>

commands:
  command
  command_2\
"""
    )


def test_help_kwarg_displays_help_message(module, run, monkeypatch):
    monkeypatch.setattr(module.magicli_testmod, "__doc__", None)
    assert (
        run("--help").out
        == f"""\
usage:
  {module.__name__}
  {module.__name__} <command>

commands:
  command
"""
    )


@pytest.mark.parametrize("argv", [("--version",), ("-V",), ("command", "-v")])
def test_version(fake_module, module_functions, run, argv):
    fake_module(*module_functions, version="1.2.3")
    result = run(*argv)
    assert result.code is None
    assert result.out == "1.2.3\n"


def test_version_flag_not_in_docstring(fake_module, module_functions, run):
    fake_module(*module_functions, version="1.2.3")
    assert run("-v").code.startswith("-v: invalid short option")
