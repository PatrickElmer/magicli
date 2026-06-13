# magiᴄʟɪ✨

Automatically turns a file into a CLI without any boilerplate by introspecting its functions.

**`hello world` example**

```python
# hello.py
def hello(name, greeting="hello"):
    print(greeting, name)
```

becomes

<img src="docs/img/hello.svg"/>

with only 3 commands

1. `pip install magicli`
1. `magicli`
1. `pip install .`

## Quick start

### Install magicli

```
pip install magicli
```

### Setup your repository

Initialize repo

```bash
git init
```

Add version info (optional)

```bash
git tag 1.0.0
```

### Automatically create CLI

```bash
magicli
```

_Make sure the name of your CLI, the module name and the name of the function have to same name._

### Install your Python package

```bash
pip install .
```

## Advanced use

### Using subcommands

```python
# module.py
def hello(): ...

def world(times=1):
    for _ in range(times):
        print("hello world")
```

```bash
$ hello world --times 2
hello world
hello world
```

### Help message

By default, the docstring of the function will be displayed.

If no docstring is specified, an error message will be printed.

## Development

Run pytest with coverage report:

```bash
python3 -m pytest -s --cov=magicli --cov-report=term-missing
```
