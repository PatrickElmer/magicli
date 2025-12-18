"""Automatically generates a CLI from functions of a module."""

import sys
import importlib
import inspect
from pathlib import Path


__all__ = ["cli"]


def magicli(argv=None):
    """Parses sys.argv into a module with function names and args/kwargs and tries to call the function."""

    name, *argv = argv or sys.argv
    name = Path(name).name.replace("-", "_")

    if name == "magicli":
        raise SystemExit(call(cli, argv))

    try:
        module = importlib.import_module(name)
    except ModuleNotFoundError:
        raise SystemExit(f"{name}: command not found")

    if (
        argv
        and not (command := argv[0].replace("-", "_")).startswith("_")
        and command in module.__dict__.get("__all__", [command])
        and inspect.isfunction(function := module.__dict__.get(command))
    ):
        call(function, argv[1:], name)
    elif inspect.isfunction(function := module.__dict__.get(name)):
        call(function, argv)
    else:
        raise SystemExit(help_message(help_from_module, module))


def call(function, argv, name=None):
    try:
        args, kwargs = args_and_kwargs(argv, function)
        function(*args, **kwargs)
    except Exception:
        raise SystemExit(help_message(help_from_function, function, name))


def _parse_kwarg(key, argv, parameters={}):
    if "=" in key:
        key, value = key.split("=", 1)
        cast_to = _get_type(parameters[key])
    else:
        cast_to = _get_type(parameters[key])
        if cast_to == bool:
            value = not parameters[key].default
        elif cast_to == type(None):
            value = True
        else:
            value = next(argv)
    return key, value if cast_to in (str, type(None)) else cast_to(value)


def _get_type(parameter):
    if parameter.annotation is not parameter.empty:
        return parameter.annotation
    if parameter.default is not parameter.empty:
        return type(parameter.default)
    return str


def args_and_kwargs(argv, function):
    parameters = inspect.signature(function).parameters
    parameter_values = list(parameters.values())

    args, kwargs = [], {}

    argv = iter(argv)
    for key in argv:
        key = key.replace("-", "_")
        if key.startswith("__"):
            key, value = _parse_kwarg(key[2:], argv, parameters)
            kwargs[key] = value
        else:
            args.append(_get_type(parameter_values[len(args)])(key))

    return args, kwargs


def help_message(help_function, obj, *args):
    return inspect.getdoc(obj) or help_function(obj, *args) or 1


def help_from_function(function, name=None):
    message = [f"usage:\n  {(f"{name} " if name else "") + function.__name__}"]
    for parameter in inspect.signature(function).parameters.values():
        if parameter.default == parameter.empty:
            message.append(parameter.name)
        else:
            message.append(f"--{parameter.name}={parameter.default!r}")

    return " ".join(message) or None


def help_from_module(module):
    functions = inspect.getmembers(module, inspect.isfunction)
    if commands := [name for name, _ in functions]:
        message = f"usage:\n  {module.__name__} command\n\ncommands:"
        return "\n  ".join([message] + commands)


def cli():
    """Generates a pyproject.toml file for the current module for use with magicli."""

    if (
        Path("pyproject.toml").exists()
        and not input("Overwrite existing pyproject.toml? (yN) ").strip().lower() == "y"
    ):
        raise SystemExit(1)

    flat_layout = [path.stem for path in Path().iterdir() if path.suffix == ".py"]
    src_layout = [
        path for path in Path().iterdir() if (Path(path) / "__init__.py").exists()
    ]

    if len(names := flat_layout + src_layout) == 1:
        name = names[0]
    else:
        msg = f"{len(names)} modules found: {', '.join(names)}\n"
        name = input(msg + "CLI name: ")

    if not name in names:
        raise SystemExit("Please choose a valid module name.")

    with open("pyproject.toml", "w") as f:
        f.write(
            f"""[build-system]
requires = ["setuptools>=80", "setuptools-scm[simple]>=8"]
build-backend = "setuptools.build_meta"

[project]
name = "{name}"
dynamic = ["version"]
dependencies = ["magicli"]

[project.scripts]
{name} = "magicli:magicli"
"""
        )

    return """pyproject.toml created.
Set the version either through `git tag` or `__version__`."""
