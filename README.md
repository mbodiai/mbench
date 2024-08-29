# mbench

[![PyPI - Version](https://img.shields.io/pypi/v/mbench.svg)](https://pypi.org/project/mbench)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/mbench.svg)](https://pypi.org/project/mbench)

-----

Simple benchmarking tool for a module, function, or block of code.


## Installation

```console
pip install mbench
```

## Usage

```python
from mbench import profileme
profileme()

def some_function():
    print("Hello")

some_function()
```
```console
        Profile Information for         
     __main__.test_get_object_speed     
┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┓
┃           Metric ┃ Value             ┃
┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━┩
│         Duration │ 1.461318 seconds  │
│         CPU time │ 24.613764 seconds │
│     Memory usage │ 250.56 MB         │
│        GPU usage │ 0.00 B            │
│       GPU usages │                   │
│        I/O usage │ 0.00 B            │
│     Avg Duration │ 0.292264 seconds  │
│     Avg CPU time │ 4.922753 seconds  │
│ Avg Memory usage │ 50.11 MB          │
│    Avg GPU usage │ 0.00 B            │
│   Avg GPU usages │                   │
│    Avg I/O usage │ 0.00 B            │
│      Total calls │ 5                 │
└──────────────────┴───────────────────┘
```
### As a Decorator

```python
from mbench import profile
@profile
def some_function():
    print("Hello")
```

### As a Context Manager
```python

from mbench import profiling
with profiling:
  run_anything()
```

## _when_ calling

Functions you want to profile must

1. Be _defined_ in the same module that the `profileme` function is being called.
2. Be called after `profileme(when="calling")` is called.

## _when_ called

Functions you want to profile must

1. Be _called_ in the same module that the `profileme` function is being called.
2. Be called after `profileme(when="called")` is called.

## Docs
```python
profileme(when: Literal['called', 'calling'] = 'called')
    Profile all functions in a module. Set `when` to 'calling' to profile only the functions called by the target module.
```
## License

`mbench` is distributed under the terms of the [MIT License](LICENSE).
