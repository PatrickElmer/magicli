import inspect
import sys


__version__ = "1.1.0"


def magicli(
    frame_globals=inspect.currentframe().f_back.f_globals,
    argv=sys.argv,
    help_message=lambda function: inspect.getdoc(function),
    version_message=lambda frame_globals: frame_globals.get("__version__"),
):
    """Calls a function according to the arguments specified in the argv."""

    function, argv = get_function_to_call(argv, frame_globals)

    try:
        kwargs = get_kwargs(argv, function, help_message)
    except (IndexError, KeyError):
        handle_error(frame_globals, argv, help_message, version_message, function)
    else:
        function(**kwargs)


def handle_error(frame_globals, argv, help_message, version_message, function):
    if "--version" in argv and (version := version_message(frame_globals)):
        print(version)
    elif "--help" in argv and (help := help_message(function)):
        print(help)
    else:
        raise SystemExit(help_message(function))


def get_function_to_call(argv, frame_globals):
    """
    Returns the function to be called based on command line arguments
    and the command line arguments to be fed into the function.
    """

    if not argv:
        raise ValueError

    _all = frame_globals.get("__all__")

    def get_function(function_name):
        if inspect.isfunction(function := frame_globals.get(function_name)) and function.__module__ == frame_globals["__name__"]:
            return function

    def is_valid_function(arg):
        function_name = arg.replace("-", "_")
        if _all and function_name in _all and (function := get_function(function_name)):
            return function
        if not function_name.startswith("_"):
            return get_function(function_name)

    # Try argv number 2
    if len(argv) > 1 and argv[0] != argv[1]:
        if function := is_valid_function(argv[1]):
            return function, argv[2:]

    # Try argv number 1
    if function := is_valid_function(argv[0]):
        return function, argv[1:]

    # Use first function in __all__
    if _all:
        for function_name in _all:
            if function := is_valid_function(function_name):
                return function, argv[1:]

    # Use first function in module
    return first_function(frame_globals), argv[1:]


def first_function(frame_globals):
    """Returns the first non-private function of the current module."""

    for function in frame_globals.values():
        if (
            inspect.isfunction(function)
            and not function.__name__.startswith("_")
            and function.__module__ == frame_globals["__name__"]
        ):
            return function


def short_to_long_option(short, docstring):
    """Convert the one character short option into the option specified in the docstring."""
    if not docstring:
        raise KeyError
    start = docstring.index(f"-{short}, --") + 6
    ends = sorted([docstring.find(" ", start), docstring.find("\n", start)])
    end = ends[1] if ends[0] == -1 else ends[0]
    if end == -1:
        if docstring[start:]:
            return docstring[start:].replace("-", "_")
        else:
            raise KeyError
    return docstring[start:end].replace("-", "_")


def get_kwargs(argv, function, help_message=None):
    """Parses argv into kwargs and converts the values according to a function signature."""
    parameters = inspect.signature(function).parameters
    parameter_values = list(parameters.values())
    iterator = iter(argv)
    kwargs = {}

    for key in iterator:
        if key.startswith("-"):
            if not key.startswith("--") and len(key) > 1:
                _, *flags, short_option = key
                if not help_message:
                    raise KeyError
                docstring = help_message(function)

                for flag in flags:
                    long_option = short_to_long_option(flag, docstring)
                    if not long_option:
                        raise KeyError
                    key = long_option.replace("-", "_")

                    cast_to = type_to_cast(parameters[key])
                    if cast_to == bool:
                        kwargs[key] = not parameters[key].default
                    elif cast_to == type(None):
                        kwargs[key] = True
                    else:
                        raise KeyError

                long_option = short_to_long_option(short_option, docstring)
                if not long_option:
                    raise KeyError
                key = long_option.replace("-", "_")

            elif len(key) < 3:
                raise KeyError
            else:
                key = key[2:].replace("-", "_")

            value = None

            if "=" in key:
                key, value = key.split("=", 1)
            if key in kwargs:
                raise KeyError

            cast_to = type_to_cast(parameters[key])

            if cast_to == bool:
                kwargs[key] = not parameters[key].default
            elif cast_to == type(None):
                kwargs[key] = True
            else:
                if value is None:
                    value = next(iterator, None)
                kwargs[key] = cast_to(value)
        else:
            parameter = parameter_values.pop(0)

            if parameter.name in kwargs:
                raise KeyError
            
            # Prevent args from being used as kwargs
            if parameter.default is not inspect._empty:
                raise KeyError

            cast_to = type_to_cast(parameter)
            kwargs[parameter.name] = cast_to(key)

    if parameter_values and parameter_values[0].default is inspect._empty:
        raise IndexError

    return kwargs


def type_to_cast(parameter):
    """Returns the type of a parameter. Defaults to str."""

    if parameter.annotation is not inspect._empty:
        return parameter.annotation
    if parameter.default is not inspect._empty:
        return type(parameter.default)
    return str


def calling_frame(import_statement="import magicli"):
    """
    Walks the call stack to find the frame with the import statement.
    Returns the corresponding frame if it is found, and None otherwise.
    """

    frame = sys._getframe()
    while frame:
        frameinfo = inspect.getframeinfo(frame)
        if frameinfo.code_context and frameinfo.code_context[0].lstrip().startswith(
            import_statement
        ):
            return frame
        frame = frame.f_back


if frame := calling_frame():
    raise SystemExit(magicli(frame_globals=frame.f_globals))
