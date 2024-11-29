import inspect
import pytest

from magicli import type_to_cast


def function(
    arg,
    arg_2: int,
    kwarg_1=1,
    kwarg_2: int = 1,
): ...


@pytest.mark.parametrize(
    "parameter, result",
    [
        ("arg", str),
        ("arg_2", int),
        ("kwarg_1", int),
        ("kwarg_2", int),
    ],
)
def test_parameter_type(parameter, result):
    parameter = inspect.signature(function).parameters[parameter]
    assert type_to_cast(parameter) == result
