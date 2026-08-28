import sys

from magicli import get_commands, help_from_function, help_from_module


def f1(arg, kwarg=1): ...


def test_help_from_function():
    assert help_from_function(f1) == "usage:\n  f1 arg [--kwarg]"


def test_help_from_function_with_name():
    assert help_from_function(f1, "name") == "usage:\n  name f1 arg [--kwarg]"


def create_module(name="name"):
    module = type(sys)(name)
    f1.__module__ = name
    module.command = f1
    return module


def test_imported_functions_are_not_commands():
    module = create_module()
    module.imported = get_commands
    assert get_commands(module) == ["command"]


def test_all_can_expose_imported_functions():
    module = create_module()
    module.imported = get_commands
    module.__all__ = ["command", "imported"]
    assert get_commands(module) == ["command", "imported"]


def test_help_from_module():
    module = create_module()
    assert (
        help_from_module(module)
        == """\
usage:
  name command

commands:
  command\
"""
    )


def test_help_from_module_with_version():
    module = create_module()
    module.__dict__["__version__"] = "0.1.2"
    assert (
        help_from_module(module)
        == """\
name 0.1.2

usage:
  name command

commands:
  command\
"""
    )
