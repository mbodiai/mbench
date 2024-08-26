# SPDX-FileCopyrightText: 2024-present Sebastian Peralta <sebastian@mbodi.ai>
#
# SPDX-License-Identifier: apache-2.0
<<<<<<< HEAD

from typing import Literal
from .profile import profileme, profile, profiling, main, FunctionProfiler
from functools import wraps

__all__ = ["profileme", "profiling", "profile", "mbench"]

@wraps(profileme)
def mbench(mode: Literal["caller", "callee"] = "caller"):
    """Profile the code"""
    return profileme(mode)

if __name__ == '__main__':
    main()
=======
from .profile import profileme
from .profile import profiling
from .profile import profile

__all__ = ["profileme", "profiling", "profile"]
>>>>>>> 9caddfa4a3c5301a64f24efe60382ed55af85c9c
