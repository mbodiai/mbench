# SPDX-FileCopyrightText: 2024-present Sebastian Peralta <sebastian@mbodi.ai>
#
# SPDX-License-Identifier: apache-2.0

from typing import Literal


from .profile import main, profile, profileme, profiling

__all__ = ["profileme", "profiling", "profile", "mbench"]


def mbench(when: Literal["calling", "called"] = "calling") -> None:
    """Profile the code"""
    return profileme(when)


