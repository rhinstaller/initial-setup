#!/usr/bin/env python3
"""
Minimal setup.py for dynamic configuration that pyproject.toml cannot handle.
Most configuration is now in pyproject.toml.
"""

import os
from setuptools import setup

# Handle s390 architecture-specific files dynamically
data_files = []
if os.uname()[4].startswith('s390'):
    data_files.extend([
        ('etc/profile.d', ['scripts/s390/initial-setup.sh']),
        ('etc/profile.d', ['scripts/s390/initial-setup.csh']),
    ])

# Call setup with only the dynamic parts
setup(
    data_files=data_files,
)
