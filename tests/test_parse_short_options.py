from magicli import short_to_long_option
import pytest


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
    with pytest.raises(SystemExit):
        short_to_long_option("a", docstring)
