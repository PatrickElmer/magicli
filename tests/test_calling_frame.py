import inspect
from magicli import calling_frame


def test_calling_frame():
    assert calling_frame("assert calling_frame(") == inspect.currentframe()


def test_no_calling_frame():
    assert calling_frame() is None
