from time import time, sleep
from mbench import profiling, profileme, profile
from mbench.test_module import some_function

profileme(mode="callee")

def another_function():
    """
    This is another function
    """
    print("Hello")

if __name__ == "__main__":
    another_function()
    another_function()
    with profiling("some_function"):
        some_function()
        sleep(3)
    print("printed")