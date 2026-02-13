from inspect import _ParameterKind
from inspect import Parameter
from magicli import parse_short_options
from magicli import short_to_long_option
import pytest
from functools import partial


@pytest.mark.parametrize(
    ["default", "result"],
    [
        (None, True),
        (True, False),
        (False, True),
        ("", "b"),
    ],
)
def test_parse_short_options(default, result):
    kwargs = {}
    parse_short_options(
        short_options="a",
        docstring="-a, --aa",
        argv=iter(["b"]),
        parameters={
            "aa": Parameter("aa", _ParameterKind.KEYWORD_ONLY, default=default)
        },
        kwargs=kwargs,
    )
    assert kwargs == {"aa": result}


def test_parse_short_options_failures():
    successful_function = partial(
        parse_short_options,
        short_options="a",
        docstring="-a, --aa",
        argv=iter(["b"]),
        parameters={"aa": Parameter("aa", _ParameterKind.KEYWORD_ONLY)},
        kwargs={},
    )
    successful_function()
    for kwargs in [
        {"parameters": {}},
        {"docstring": ""},
    ]:
        with pytest.raises(ValueError):
            successful_function(**kwargs)


@pytest.mark.parametrize(
    "docstring",
    [
        "-a, --ab c",
        "-a, --ab\n",
        "-a, --ab",
    ],
)
def test_short_to_long_option(docstring):
    assert short_to_long_option("a", docstring) == "ab"


@pytest.mark.parametrize(
    "docstring",
    [
        "",
        "-a, --",
        "-a, --a",
    ],
)
def test_short_to_long_option_failures(docstring):
    with pytest.raises(ValueError):
        short_to_long_option("a", docstring)
