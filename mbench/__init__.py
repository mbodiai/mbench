# SPDX-FileCopyrightText: 2024-present Sebastian Peralta <sebastian@mbodi.ai>
#
# SPDX-License-Identifier: apache-2.0

from typing import Literal

from funkify import funkify

from .profile import main, profile, profileme, profiling

__all__ = ["profileme", "profiling", "profile", "mbench"]

@funkify
def mbench(mode: Literal["caller", "callee"] = "caller"):
    """Profile the code"""
    return profileme(mode)

if __name__ == '__main__':
    main()
