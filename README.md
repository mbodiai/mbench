# mbench

[![PyPI - Version](https://img.shields.io/pypi/v/mbench.svg)](https://pypi.org/project/mbench)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/mbench.svg)](https://pypi.org/project/mbench)

-----

Simple benchmarking tool for a module, function, or block of code.

```
Profile Information for Block: test_func
┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃           Metric ┃ Value                                                                                                         ┃
┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│         Duration │ 0.000616 seconds                                                                                              │
│         CPU time │ 0.000613 seconds                                                                                              │
│     Memory usage │ 1.00 KB                                                                                                       │
│        GPU usage │ 1.00 KB                                                                                                       │
│        I/O usage │ 1.00 KB                                                                                                       │
│     Avg Duration │ 1.000000 seconds                                                                                              │
│     Avg CPU time │ 1.000000 seconds                                                                                              │
│ Avg Memory usage │ 1.00 KB                                                                                                       │
│    Avg GPU usage │ 1.00 KB                                                                                                       │
│    Avg I/O usage │ 1.00 KB                                                                                                       │
│      Total calls │ 1                                                                                                             │
│            Notes │                                                                                                               │
└──────────────────┴───────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```
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
hello
Profile Information for Block: run_anything
┏━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┓
┃ Metric         ┃ Value                ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━┩
│      Duration  │ 0.000706 seconds     │
│      CPU time  │ 0.000668 seconds     │
│  Memory usage  │ 2.80 KB              │
│     GPU usage  │ 0.00 B               │
│      I/O usage │ 0.00 B               │
│   Avg Duration │ 0.000527 seconds     │
│   Avg CPU time │ 0.000521 seconds     │
│ Avg Memory usage │ 0.35 KB            │
│  Avg GPU usage │ 0.00 B               │
│   Avg I/O usage │ 0.00 B              │
│    Total calls │ 8                    │
│          Notes │ None                 │
└────────────────┴─────────────────────┘
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

## Caller Mode  (Default)

Functions you want to profile must

1. Be _defined_ in the same module that the `profileme` function is being called.
2. Be called after `profileme(mode="caller")` is called.

## Callee Mode

Functions you want to profile must

1. Be _called_ in the same module that the `profileme` function is being called.
2. Be called after `profileme(mode="callee")` is called.


## License

`mbench` is distributed under the terms of the [MIT License](LICENSE).
