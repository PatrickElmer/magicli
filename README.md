# magiᴄʟɪ✨

Automatically generates a CLI from functions.

## Install

```
pip install magicli
```

## Get started

Simple usage example.

```python
def hello(name, times=1):
    for _ in range(times):
        print("hello", name)

import magicli
```

Make sure you import `magicli` at the end of the file.

```bash
$ hello world --times 2
hello world
hello world
```

## Using subcommands

```python
# module.py
def hello(): ...

def world(times=1):
    for _ in range(times):
        print("hello world")

import magicli
```

```bash
$ hello world --times 2
hello world
hello world
```

### Define name of CLI in `pyproject.toml`

Add the following to your `pyproject.toml`.

```toml
[project.scripts]
hello = "module:hello"
```

This example assumes the following project structure with the CLI to be created specified in the file `module.py`.

```bash
.
├── module.py
└── pyproject.toml
```

Make sure to adjust the path to `module` if your project layout is different.

### Help message

By default, the docstring of the function will be displayed.

If no docstring is specified, there will be no output.
