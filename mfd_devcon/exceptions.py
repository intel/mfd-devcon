# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: MIT
"""Module for Devcon exceptions."""

import subprocess
from mfd_base_tool.exceptions import ToolNotAvailable


class DevconException(Exception):
    """Handle Devcon exceptions."""


class DevconNotAvailable(ToolNotAvailable, DevconException):
    """Handle tool not available exception."""


class DevconExecutionError(DevconException, subprocess.CalledProcessError):
    """Handle Devcon execution errors."""


class DevconParserException(Exception):
    """Handle Devcon parser exceptions."""
