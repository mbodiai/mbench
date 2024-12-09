from mbench.profile import profileme, profiling, main
from typing import Literal

def mbench(when: Literal["calling", "called"] = "calling") -> None:
    """Profile the code"""
    return profileme(when)

if __name__ == '__main__':
    main()