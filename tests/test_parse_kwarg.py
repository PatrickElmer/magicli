from inspect import _ParameterKind
from inspect import Parameter
from magicli import parse_kwarg
from magicli import get_type
from magicli import args_and_kwargs
import pytest
import inspect


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
    assert get_type(Parameter("a", PK, annotation=int)) == int
    assert get_type(Parameter("b", PK, default=1)) == int
    assert get_type(Parameter("c", PK)) == str


def test_args_and_kwargs():
    parameters = inspect.signature(lambda arg, kwarg=1: None).parameters
    assert args_and_kwargs(["a", "--kwarg=2"], parameters, docstring="") == (
        ["a"],
        {"kwarg": 2},
    )
    assert args_and_kwargs(["a", "--kwarg", "2"], parameters, docstring="") == (
        ["a"],
        {"kwarg": 2},
    )


def test_args_and_kwargs_with_underscore():
    parameters = inspect.signature(lambda arg, kwarg_1=1: None).parameters
    assert args_and_kwargs(["a", "--kwarg-1=2"], parameters, docstring="") == (
        ["a"],
        {"kwarg_1": 2},
    )
    assert args_and_kwargs(["a", "--kwarg-1", "2"], parameters, docstring="") == (
        ["a"],
        {"kwarg_1": 2},
    )
