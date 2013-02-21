#! /usr/bin/env python

"""
phyles: A package to simplify authoring utilites.
Copyright (C) 2013  James C. Stroud
All rights reserved.
"""

try:
  import _version
  __version__ = _version.__version__
except ImportError:
  __version__ = None

from _phyles import *

from terminalsize import get_terminal_size


__all__ = ["Undefined", "Schema", "Configuration",
           "read_schema", "load_schema",
           "sample_config", "validate_config", "read_config",
           "last_made", "wait_exec", "doyn",
           "banner", "usage", "graceful", "get_home_dir",
           "get_data_path", "prune", "default_argparser",
           "package_spec", "set_up", "run_main",
           "get_terminal_size"]
