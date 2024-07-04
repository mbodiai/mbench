from mbench.profile import profile, profileme


profileme()  # Set up the profiler first


def another_function():
    """
    This is another function
    """
    print("Hello")

if __name__ == "__main__":
    another_function()
    another_function()
    print("printed")