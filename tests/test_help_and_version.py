import pytest

from magicli import help_from_function, help_from_module


def f1(arg, kwarg=1): ...


def test_help_from_function():
    assert help_from_function(f1) == "usage:\n  f1 arg [--kwarg]"


def test_help_from_function_with_name():
    assert help_from_function(f1, "name") == "usage:\n  name f1 arg [--kwarg]"


def test_help_from_module(fake_module):
    module = fake_module(command=f1)
    assert (
        help_from_module(module)
        == f"""\
usage:
  {module.__name__} command

commands:
  command\
"""
    )


def test_help_from_module_with_version(fake_module):
    module = fake_module(command=f1, version="0.1.2")
    assert (
        help_from_module(module)
        == f"""\
{module.__name__} 0.1.2

usage:
  {module.__name__} command

commands:
  command\
"""
    )


@pytest.mark.parametrize("version", ["0.1.2", None])
def test_help_from_module_without_commands(fake_module, version):
    module = fake_module(version=version)
    expected = f"{module.__name__} {version}" if version else ""
    assert help_from_module(module) == expected


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


@pytest.mark.parametrize("flag", ["--version", "-V"])
def test_version(module, run, flag):
    module.__version__ = "1.2.3"
    result = run(flag)
    assert result.code is None
    assert result.out == "1.2.3\n"


def test_version_flag_not_in_docstring(module, run):
    module.__version__ = "1.2.3"
    assert run("-v").code.startswith("-v: invalid short option")


def test_version_with_command(module, run):
    module.__version__ = "1.2.3"
    result = run("command", "-v")
    assert result.code is None
    assert result.out == "1.2.3\n"
