from magicli import help_from_function
from magicli import help_from_module
import sys


def f1(arg, kwarg=1): ...


def test_help_from_function():
    assert help_from_function(f1) == "usage:\n  f1 arg [--kwarg] [--version]"


def test_help_from_function_with_name():
    assert help_from_function(f1, "name") == "usage:\n  name f1 arg [--kwarg] [--version]"


def f2(version=1): ...


def test_help_from_function_with_custom_version():
    assert help_from_function(f2) == "usage:\n  f2 [--version]"


def test_help_from_module():
    module = type(sys)("name")
    module.command = f1
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
    module = type(sys)("name")
    module.__dict__["__version__"] = "0.1.2"
    module.command = f1
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
