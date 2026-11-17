"""
`magicli` generates command-line interfaces from Python modules
by introspecting its functions and automatically parsing command-
line arguments based on function signatures.
"""

import argparse
import ast
import importlib
import inspect
import re
import subprocess
import sys
from functools import partial
from importlib import metadata
from pathlib import Path


class ParseArgvError(Exception):
    """Failure to parse argv into args and kwargs based on function parameters and docstring."""


def info(message):
    """Print a status message for the user to stderr."""
    print(message, file=sys.stderr)


def magicli():
    """Parses command-line arguments and calls the appropriate function."""
    name = Path(sys.argv[0]).name
    argv = sys.argv[1:]

    if name == "magicli":
        raise SystemExit(call(cli, argv, sys.modules["magicli"]))

    module = load_module(name.replace("-", "_"))

    if function := get_function_from_argv(argv, module, name.replace("-", "_")):
        function()
    else:
        raise SystemExit(help_message(help_from_module, module))


def get_function_from_argv(argv, module, name):
    """Returns the module's function to call based on argv."""
    if function := is_command(argv, module):
        return partial(call, function, argv[1:], module, name)
    if inspect.isfunction(function := getattr(module, name, None)):
        return partial(call, function, argv, module)
    return None


def is_public_function(module, name):
    """
    Checks if `name` is a public function of the module. With `__all__`, only listed
    names are public. Without it, imported functions are excluded.
    """
    function = getattr(module, name, None)
    if not inspect.isfunction(function) or name.startswith("_"):
        return False
    if hasattr(module, "__all__"):
        return name in module.__all__
    return function.__module__ == module.__name__


def is_command(argv, module):
    """Returns the function named by `argv[0]` if it is a public command."""
    if argv and is_public_function(module, command := argv[0].replace("-", "_")):
        return getattr(module, command)
    return None


def call(function, argv, module=None, name=None):
    """
    Converts arguments to function parameters and calls the function.
    Displays a help message if an exception occurs.
    """
    docstring = inspect.getdoc(function) or ""
    parameters = inspect.signature(function, eval_str=True).parameters

    check_for_help_and_version(argv, parameters, docstring, module, function)

    try:
        kwargs = vars(build_parser(parameters, docstring).parse_intermixed_args(argv))
    except ParseArgvError as exc:
        raise SystemExit(
            help_message(help_from_function, function, name, module, error=exc.args[0])
        )

    args = []
    for parameter in parameters.values():
        if parameter.kind is parameter.POSITIONAL_ONLY:
            args.append(kwargs.pop(parameter.name, parameter.default))
        elif parameter.kind is parameter.VAR_POSITIONAL:
            args.extend(kwargs.pop(parameter.name, []))

    function(*args, **kwargs)


class _Parser(argparse.ArgumentParser):
    """Argument parser that raises `ParseArgvError` instead of exiting."""

    def error(self, message):
        raise ParseArgvError(message)


def build_parser(parameters, docstring):
    """
    Builds an argument parser from function parameters. Short options are
    read from the docstring, e.g. `-t, --times`.
    """
    parser = _Parser(add_help=False, allow_abbrev=False)
    shorts = {
        long.replace("-", "_"): short
        for short, long in re.findall(r"(?<![\w-])-(\w), --([\w-]+)", docstring)
    }
    for parameter in parameters.values():
        name, kind = parameter.name, parameter.kind
        cast_to = get_type(parameter)
        positional = {"type": cast_to, "default": argparse.SUPPRESS}

        if kind is parameter.VAR_KEYWORD:
            continue
        if kind is parameter.VAR_POSITIONAL:
            parser.add_argument(name, nargs="*", **positional)
            continue
        if kind is parameter.POSITIONAL_ONLY:
            parser.add_argument(
                name,
                nargs=None if parameter.default is parameter.empty else "?",
                **positional,
            )
            continue

        flags = list(dict.fromkeys([f"--{name.replace('_', '-')}", f"--{name}"]))
        if name in shorts:
            flags.insert(0, f"-{shorts[name]}")
        opts = {"dest": name, "default": argparse.SUPPRESS}
        if cast_to is bool:
            parser.add_argument(
                *flags, action="store_const", const=not parameter.default, **opts
            )
        elif cast_to is type(None):
            parser.add_argument(*flags, action="store_const", const=True, **opts)
        else:
            parser.add_argument(*flags, type=cast_to, **opts)
            parser.add_argument(
                name,
                nargs=None if parameter.default is parameter.empty else "?",
                **positional,
            )
    return parser


def get_type(parameter):
    """
    Determines the type based on function signature annotations or defaults.
    Falls back to `str` if neither is available.
    """
    if parameter.annotation is not parameter.empty:
        return parameter.annotation
    if parameter.default is not parameter.empty:
        return type(parameter.default)
    return str


def check_for_help_and_version(argv, parameters, docstring, module, function):
    """Displays version information if --version is specified in the docstring."""
    if not module or len(argv) != 1:
        return
    if argv[0] in ("--help", "-h") and "help" not in parameters:
        print(help_message(help_from_function, function, None, module))
        raise SystemExit
    args = {
        "--version": "--version",
        "-v": "-v, --version",
        "-V": "-V, --version",
    }
    if (doc := args.get(argv[0])) and doc in docstring and "version" not in parameters:
        print(get_version(module))
        raise SystemExit


def help_message(help_function, obj, *args, error=None):
    """
    Generates a help message for a function or module.
    Returns the object's docstring if available, otherwise generates the help message
    using the provided `help_function`.
    """
    message = inspect.getdoc(obj) or help_function(obj, *args)
    return (error + "\n\n" if error else "") + message if message else 1


def help_from_function(function, name=None, module=None):
    """
    Generates a help message for a function based on its signature.
    Displays the function name, required positional arguments, and
    optional keyword arguments with their default values.
    """
    message = [name] if name else []
    message.append(function.__name__)
    message.extend(map(format_kwarg, inspect.signature(function).parameters.values()))
    blocks = [["usage:", " ".join(message)]]
    if module and (commands := get_commands(module)):
        blocks[0].append(f"{module.__name__} <command>")
        blocks.append(["commands:", *commands])
    return format_blocks(blocks)


def format_kwarg(kwarg):
    """Formats a parameter as positional or optional argument."""
    return kwarg.name if kwarg.default is kwarg.empty else f"[--{kwarg.name}]"


def help_from_module(module):
    """
    Generates a help message for a module and lists available commands.
    Lists all public functions that are not excluded in `__all__`.
    """
    version = get_version(module)
    blocks = [[f"{module.__name__} {version}"]] if version else []
    if commands := get_commands(module):
        blocks.append(["usage:", f"{module.__name__} command"])
        blocks.append(["commands:", *commands])
    return format_blocks(blocks)


def format_blocks(blocks, sep="\n  "):
    """Formats blocks of text with proper indentation."""
    return "\n\n".join(sep.join(block) for block in blocks)


def load_module(name):
    """Load module from name"""
    try:
        return importlib.import_module(name)
    except ModuleNotFoundError as exc:
        raise SystemExit(f"{name}: command not found") from exc


def get_commands(module):
    """Returns list of public commands that are not excluded by `__all__`."""
    return [
        name
        for name in dir(module)
        if name != module.__name__ and is_public_function(module, name)
    ]


def get_version(module):
    """Returns the version of a module from its metadata or `__version__` attribute."""
    try:
        return metadata.version(module.__name__)
    except metadata.PackageNotFoundError:
        return getattr(module, "__version__", None)


def get_project_name():
    """Detect project name from project structure."""
    single_file_layout = [path.stem for path in Path().glob("*.py")]
    flat_layout = [
        path.parent.name
        for path in Path().glob("*/__init__.py")
        if path.parent.name != "tests"
    ]
    src_layout = [path.parent.name for path in Path().glob("src/*/__init__.py")]

    if len(names := single_file_layout + flat_layout + src_layout) == 1:
        return names[0]

    if name := input("CLI name: "):
        return name

    raise SystemExit(1)


def get_output(command):
    """Return the stdout of a command (list of arguments) or None on failure."""
    try:
        output = subprocess.run(
            command, capture_output=True, text=True, check=False
        ).stdout
    except OSError:
        return None
    return output.removesuffix("\n") or None


def get_homepage(url=None):
    """Return a homepage url from a git remote url."""
    url = url or get_output(["git", "remote", "get-url", "origin"]) or ""
    if url.startswith("git@"):
        url = "https://" + url.removeprefix("git@").replace(":", "/")
    return url.removesuffix(".git")


def get_description(name):
    """Return the first paragraph of a module's docstring if available."""
    for path in (
        Path(f"{name}.py"),
        Path(name, "__init__.py"),
        Path("src", name, "__init__.py"),
    ):
        if path.is_file():
            try:
                tree = ast.parse(path.read_bytes())
            except (SyntaxError, ValueError):
                return None
            doc = ast.get_docstring(tree) or ""
            return " ".join(doc.split("\n\n")[0].split()) or None
    return None


def get_license_expression(content):
    """Returns the license expression used in pyproject.toml."""
    return {
        "Apache License": "Apache-2.0",
        "BSD 2-Clause License": "BSD-2-Clause",
        "BSD 3-Clause License": "BSD-3-Clause",
        "GNU AFFERO GENERAL PUBLIC LICENSE": "AGPL-3.0-or-later",
        "GNU GENERAL PUBLIC LICENSE": "GPL-3.0-or-later",
        "GNU LESSER GENERAL PUBLIC LICENSE": "LGPL-3.0-or-later",
        "MIT License": "MIT",
        "Mozilla Public License Version 2.0": "MPL-2.0",
        "Public domain statement": "Unlicense",
    }.get(content.split("\n")[0].strip())


def detect_path(glob, extensions):
    """Returns only a single path of a glob if it ends with one of the provided extensions."""
    paths = [path for path in Path().glob(glob) if path.suffix in extensions]
    return paths[0] if len(paths) == 1 else None


def cli(name="", author="", email="", description="", homepage=""):
    """
    magiCLI✨

    Generates a "pyproject.toml" configuration file for a module and sets up the project script.
    The CLI name must be the same as the module name.

    usage:
      magicli [option]

    options:
      --name
      --author
      --email
      --description
      --homepage
      -v, --version
    """
    pyproject = Path("pyproject.toml")
    if (
        pyproject.exists()
        and input("Overwrite existing pyproject.toml? (yN) ").strip().lower() != "y"
    ):
        raise SystemExit(1)

    name = name or get_project_name()

    if Path(".git").exists():
        author = author or get_output(["git", "config", "--get", "user.name"])
        email = email or get_output(["git", "config", "--get", "user.email"])
        if not get_output(["git", "tag"]):
            info("Specify the version with `git tag`")
    else:
        info("Not a git repo. Run `git init`")

    authors = [f'{k}="{v}"' for k, v in {"name": author, "email": email}.items() if v]

    project = [
        "[project]",
        f'name = "{name}"',
        'dynamic = ["version"]',
        'dependencies = ["magicli<3"]',
    ]

    if authors:
        project.append(f"authors = [{{{', '.join(authors)}}}]")

    if readme := detect_path("README*", {".md", ".rst", ".txt"}):
        project.append(f'readme = "{readme.name}"')

    if license_file := detect_path("LICENSE*", {"", ".txt"}):
        license_content = license_file.read_text(encoding="utf-8")
        if license_expression := get_license_expression(license_content):
            project.append(f'license = "{license_expression}"')
        else:
            info(f"Unknown license: {license_file.name}")
        project.append(f'license-files = ["{license_file.name}"]')

    if description or (description := get_description(name)):
        project.append(f'description = "{description}"')

    blocks = [project, ["[project.scripts]", f'{name} = "magicli:magicli"']]

    if homepage or (homepage := get_homepage()):
        blocks.append(["[project.urls]", f'Home = "{homepage}"'])

    blocks.append(
        [
            "[build-system]",
            'requires = ["setuptools>=80", "setuptools-scm[simple]>=8"]',
            'build-backend = "setuptools.build_meta"',
        ]
    )

    pyproject.write_text(format_blocks(blocks, sep="\n") + "\n", encoding="utf-8")
    info("Created pyproject.toml ✨")
