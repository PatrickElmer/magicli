from inspect import Parameter

from magicli import get_type

PK = Parameter.POSITIONAL_OR_KEYWORD


def test_get_type():
    assert get_type(Parameter("a", PK, annotation=int)) is int
    assert get_type(Parameter("b", PK, default=1)) is int
    assert get_type(Parameter("c", PK)) is str
