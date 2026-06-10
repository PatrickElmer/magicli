import inspect
from inspect import Parameter, _ParameterKind

import pytest

from magicli import ParseArgvError, get_type, parse_argv, parse_kwarg

PK = _ParameterKind.POSITIONAL_OR_KEYWORD


def test_parse_kwarg():
    kwarg = Parameter("kwarg", PK, default="")
    assert parse_kwarg("kwarg=1", iter([]), {"kwarg": kwarg}) == ("kwarg", "1")
    assert parse_kwarg("kwarg", iter(["1"]), {"kwarg": kwarg}) == ("kwarg", "1")


@pytest.mark.parametrize(
    ("default", "result"),
    [
        (True, False),
        (False, True),
        (None, True),
    ],
)
def test_parse_kwarg_bool_and_none(default, result):
    assert parse_kwarg(
        "kwarg", iter([]), {"kwarg": Parameter("kwarg", PK, default=default)}
    ) == ("kwarg", result)


def test_get_type():
    assert get_type(Parameter("a", PK, annotation=int)) is int
    assert get_type(Parameter("b", PK, default=1)) is int
    assert get_type(Parameter("c", PK)) is str


def test_parse_argv():
    parameters = inspect.signature(lambda arg, kwarg=1: None).parameters
    assert parse_argv(["a", "--kwarg=2"], parameters, docstring="") == (
        ["a"],
        {"kwarg": 2},
    )
    assert parse_argv(["a", "--kwarg", "2"], parameters, docstring="") == (
        ["a"],
        {"kwarg": 2},
    )


def test_parse_argv_with_underscore():
    parameters = inspect.signature(lambda arg, kwarg_1=1: None).parameters
    assert parse_argv(["a", "--kwarg-1=2"], parameters, docstring="") == (
        ["a"],
        {"kwarg_1": 2},
    )
    assert parse_argv(["a", "--kwarg-1", "2"], parameters, docstring="") == (
        ["a"],
        {"kwarg_1": 2},
    )


@pytest.mark.parametrize(
    ("command", "error_message"),
    [
        (["a", "--unknown=2"], "--unknown: unknown long option"),
        (["a", "--kwarg"], "error: missing option value"),
        ([], "arg: positional argument missing"),
    ],
)
def test_parse_argv_errors(command, error_message):
    parameters = inspect.signature(lambda arg, kwarg=1: None).parameters
    with pytest.raises(ParseArgvError) as error:
        parse_argv(command, parameters, docstring="")
    assert error.value.args[0] == error_message


@pytest.mark.parametrize(
    ("command", "result"),
    [
        (["--kwarg", "''"], "''"),
        (["--kwarg="], ""),
    ],
)
def test_parse_argv_empty_kwarg(command, result):
    parameters = inspect.signature(lambda kwarg="1": None).parameters
    res = parse_argv(command, parameters, docstring="")
    assert res == ([], {'kwarg': result})


def test_parse_argv_with_invalid_type_raises_parse_error():
    with pytest.raises(ParseArgvError) as error:
        parse_argv(["not-an-int"], {"arg": Parameter("arg", PK, annotation=int)}, "")
    assert error.value.args[0].startswith("invalid literal for int() with base 10: 'not-an-int'")
