# SPDX-FileCopyrightText: 2024-present Sebastian Peralta <sebastian@mbodi.ai>
#
# SPDX-License-Identifier: apache-2.0

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
