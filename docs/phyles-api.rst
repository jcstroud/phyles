Phyles API
==========

API Overview
------------

The phyles API has several functions and classes to
facilitate the construction of medium-sized utilites.
These functions and classes are divided into four categories:

  - `Classes for Configurations and Schemata`_
  - `Functions for Configurations and Schemata`_
  - `Functions for Files and Directories`_
  - `Functions for User Interaction`_
  - `Functions for a One-Size-Fits-All Runtime`_


Classes for Configurations and Schemata
---------------------------------------

  - :class:`phyles.Schema`
       encapsulates a schema and wraps `phyles.sample_config`_,
       `phyles.validate_config`_, and `phyles.read_config`_
       for convenience
  - :class:`phyles.Configuration`
       encapsulates a configuration, remembering values
       before any conversion


Functions for Configurations and Schemata
-----------------------------------------

  - `phyles.read_schema`_
       makes a schema from a specification in a YAML file
  - `phyles.load_schema`_
       makes a schema a specification in YAML text, a mapping,
       or a :class:`list` of 2-:class:`tuples` with unique keys
  - `phyles.sample_config`_
       produces a sample config from a schema
  - `phyles.validate_config`_
       validates a config file with a schema
  - `phyles.read_config`_
       reads a yaml config file and validates the config
       with a schema


Functions for Files and Directories
-----------------------------------

  - `phyles.last_made`_
       returns the most recently created file in a directory
  - `phyles.get_home_dir`_
       returns the users home directory in a representation
       native to the host OS
  - `phyles.get_data_path`_
       returns the absolute path to a data directory
       within a package
  - `phyles.package_spec`_
       reads and returns the contents a schema specification
       somewhere in a package as YAML text
  - `phyles.prune`_
       recursively deletes files matching specified
       unix sytle patterns
  - `phyles.zipdir`_
       uses python zipfile package to create a zip archive
       of a directory


Functions for User Interaction
------------------------------

  - `phyles.wait_exec`_
       waits for a command to execute via a system call
       and returns the output from stdout; slightly
       more convenient than :class:`popen2.Popen3`
  - `phyles.doyn`_
       queries user for yes/no input from :func:`raw_input`
       and can execute an optional command with `phyles.wait_exec`_
  - `phyles.banner`_
       prints a banner for the program to stdout
  - `phyles.usage`_
       uses :class:`optparse.OptionParser` to print usage and
       can print an optional error message, if provided.
  - `phyles.default_argparser`_
       returns a default :class:`argparse.ArgumentParser`
       with mutually exclusive template, config, and
       override arguments added
  - `phyles.get_terminal_size`_
       returns the terminal size as a (width, height)
       :class:`tuple` (works with Linux, OS X, Windows, Cygwin)


Functions for a One-Size-Fits-All Runtime
-----------------------------------------

  - `phyles.set_up`_
       sets up the runtime with an :class:`argparse.ArgParser`,
       loads a schema and validates a config with config override,
       and prepares state for graceful recovery from user error
  - `phyles.run_main`_
       trivial try-except block for graceful recovery from
       anticipated types of user error
  - `phyles.mapify`_
       function decorator that converts a function taking
       any arbitrary set of arguments into a funciton taking
       as a single argument a mapping object keyed with the
       names of the original arguments


API Details
-----------

.. automodule:: phyles
   :members:
