from inspect import Parameter, _ParameterKind

import pytest

from magicli import ParseArgvError, parse_short_options, short_to_long_option


@pytest.mark.parametrize(
    ("default", "result"),
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
        iter_argv=iter(["b"]),
        parameters={
            "aa": Parameter("aa", _ParameterKind.KEYWORD_ONLY, default=default)
        },
        kwargs=kwargs,
    )
    assert kwargs == {"aa": result}


def test_parse_short_options_failures():
    kwargs = {
        "short_options": "a",
        "docstring": "-a, --abc",
        "iter_argv": iter(["b"]),
        "parameters": {"abc": Parameter("abc", _ParameterKind.KEYWORD_ONLY)},
        "kwargs": {},
    }
    for args, err in [
        ({"parameters": {}}, ("--abc: invalid long option",)),
        ({"docstring": ""}, ("-a: invalid short option",)),
        ({"short_options": "aa", "iter_argv": iter(["aa"])}, ("-a: expected boolean",)),
    ]:
        with pytest.raises(ParseArgvError) as error:
            parse_short_options(**(kwargs | args))
        assert error.value.args == err


@pytest.mark.parametrize(
    "docstring",
    [
        "-a, --ab c",
        "-a, --ab\n",
        "-a, --ab",
        "[-a, --ab]",
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
    with pytest.raises(ParseArgvError) as error:
        short_to_long_option("a", docstring)
    assert error.value.args[0] == "-a: invalid short option"
