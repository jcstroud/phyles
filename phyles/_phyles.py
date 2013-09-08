#! /usr/bin/env python

"""
phyles: A package to simplify authoring utilites.
Copyright (C) 2013  James C. Stroud
All rights reserved.
"""

from _version import __version__

import os
import sys
import modulefinder
import subprocess
import textwrap
import pprint
import re
import argparse
import logging
import glob
import inspect
from stat import S_ISREG, ST_CTIME, ST_MODE
from contextlib import closing
from zipfile import ZipFile, ZIP_DEFLATED

import pkg_resources

try:
  # python 2.7
  from collections import OrderedDict
except ImportError:
  # python 2.6 (http://pypi.python.org/pypi/ordereddict)
  from ordereddict import OrderedDict

import yaml

"""
Name of the package
"""
PACKAGE = "phyles"

"""
Root name of skeleton package directory
"""
SKEL = "skel"

"""
Environment variable for phyles pacakge data directory
"""
PHYLES_DATA = "PHYLES_DATA"

"""
Extension of phyles templates
"""
PHYLES_TEMPLATE = "phyles_template"

"""
Name of phyles package data directory
"""
PACKAGE_DATA = "package-data"

"""
Name of schema for quickstart
"""
QUICKSTART_SCHEMA = "quickstart-schema.yml"

"""
String that separates settings, i.e. for overrides.
"""
SETTING_SEP = ","

"""
String that splits a setting into key and value.
"""
SETTING_SPLIT = ":"

"""
Standard width and pad, in characters, for a CLI program.
"""
WIDTH = 70
PAD = 4

class PhylesError(Exception):
  pass

class DummyException(PhylesError):
  pass

class ConfigError(PhylesError):
  pass

class OptionError(PhylesError):
  pass

class ArchiveError(PhylesError):
  pass

class Schema(OrderedDict):
  """
  An :class:`OrderedDict` subclass that provides
  identity for schemata.

  A :class:`Schema` has an implicit structure and is created by the
  :func:`load_schema` or :func:`read_schema` functions. See the
  documentation in :func:`load_schema` for a detailed explanation.

  .. warning::

       Creating instances of :class:`Schema` through its class
       constructor (i.e. ``'__init__'``) is not yet advised
       or supported and may break forward compatibility.
  """
  def validate_config(self, *args, **kwargs):
    """
    This is a wrapper for :func:`validate_config` (see documentation
    therein).

    Comparison of usage with :func:`validate_config`::

       phyles.validate_config(schema, config)
       schema.validate_config(config)
    """
    return validate_config(self, *args, **kwargs)
  def read_config(self, *args, **kwargs):
    """
    This is a wrapper for :func:`read_config` (see documentation
    therein).

    Comparison of usage with :func:`read_config`::

       phyles.read_config(schema, config)
       schema.read_config(config)
    """
    return read_config
  def sample_config(self, *args, **kwargs):
    """
    This is a wrapper for :func:`sample_config` (see documentation
    therein).

    Comparison of usage with :func:`sample_config`::

       phyles.sample_config(schema)
       schema.sample_config()
    """
    return sample_config(self, *args, **kwargs)

class Configuration(OrderedDict):
  """
  An :class:`OrderedDict` subclass that encapsulates configurations
  and also remembers the original input.

  A :class:`Configuration` has a specific structure and is creatd by
  :func:`validate_config` or :func:`read_config` functions, usually
  by the latter.  The :class:`Configuration` class is exposed in
  the API purely for purposes of documentation.

  Attributes:
    `original`: the original config as an :class:`OrderedDict`,
                allowing the remembering of user input while
                also allowing conversion

                >>> colors = {'red': 'ff0000',
                ...           'green': '00ff00',
                ...           'blue': '0000ff'}
                >>> c = Configuration({'color': 'blue'})
                >>> c['color'] = colors[c['color']]
                >>> c['color']
                >>> '0000ff'
                >>> c.original['color']
                'blue'

  .. warning::

       Creating instances of :class:`Configuration` through its
       class constructor (i.e. with ``phyles.Configuration()``)
       is not yet advised or supported and may break forward
       compatibility.
  """
  def __init__(self, config=None):
    if config is None:
      self.original = OrderedDict()
    else:
      try:
        self.original = OrderedDict(config)
      except (TypeError, ValueError) as e:
        tmplt = ("Configuration Error:\n   '%s'\n" +
                 "Configuration as parsed by pyyaml:\n-----\n%s")
        msg = tmplt % (e, repr(config))
        graceful(msg)
    OrderedDict.__init__(self, config)

class Sentinel(object):
  """
  A class for sentinel objects.

  Immutable so it's hard to change the name--a sentinel
  is all about identity.
  """
  def __init__(self, name):
    object.__setattr__(self, "name", str(name))
  def __setattr__(self, *args, **kwargs):
    msg = "'%s' is immutable." % self.name
    raise TypeError(msg)
  def __repr__(self):
    return self.name

Undefined = Sentinel("Undefined")

def atype_or_list_of_atype(atype):
  def _f(things):
    if atype is list:
      if isinstance(things, list):
        if len(things) == 0:
          things = [things]
        else:     
          for t in things:
            if not isinstance(t, list):
              things = [things]
              break
      else:
        raise TypeError("Value '%s' is not a list." % (things,))
    elif isinstance(things, list):
      try:
        things = [atype(t) for t in things]
      except Exception, e:
        params = (t, atype)
        msg = "Value '%s' can not be converted with '%s'." % params
        raise TypeError(msg)
    else:
      try:
        things = [atype(things)]
      except Exception, e:
        params = (things, atype)
        msg = "Value '%s' can not be converted with '%s'." % params
        raise TypeError(msg)
    return things
  return _f

def timestamp(d):
  try:
    t = d.timetuple()[:6]
  except AttributeError:
    t = tuple(d[:6])
  return datetime.datetime(*t)

def pairs(p):
  for t in p:
    if len(t) == 2:
      result.append(tuple(t))
    else:
      msg = "Item %s is not a pair." % repr(t)
      raise ValueError(msg)
  return result

def complex_(n):
  try:
    c = complex(n)
  except TypeError:
    try:
      c = complex(*n)
    except Exception:
      msg = "The valued '%s' can't convert to a complex number."
      raise ConfigError(msg)

def slice_(s):
  return slice(*n)

# see http://yaml.org/type/
# note that names can be yaml data type names or python equivalents
CONVERTERS = {'map' : dict,
              'dict' : dict,
              'omap' : OrderedDict,
              'odict' : OrderedDict,
              'pairs' : pairs,
              'set' : set,
              'seq' : list,
              'list' : list,
              'tuple' : tuple,
              'bool' : bool,
              'float' : float,
              'int' : int,
              'long' : long,
              'complex' : complex_,
              'str' : str,
              'unicode' : unicode,
              'timestamp' : timestamp,
              'slice' : slice_,}

def unpack_omap(seq):
  """
  Takes `YAML seq <http://yaml.org/type/>`_
  and, if possible, creates an :class:`OrderedDict`.

  This function is useful if it is known that an item
  should be a YAML omap but the YAML parser might produce
  a :class:`list` of :class:`dict` objects instead.
  """
  if hasattr(seq[0], 'keys'):
    loaded = [d.items()[0] for d in seq]
  else:
    loaded = [tuple(i) for i in seq]
  return OrderedDict(loaded)

def read_schema(yaml_file, converters=None):
  """
  Loads the schema specified in the file named
  in `yaml_file`. This function simply opens
  and reads the `yaml_file` before sending
  its contents to :func:`load_schema` to produce
  the :class:`Schema`.

  Args:
    `yaml_file`: name of a yaml file holding the specification

    `converters`:
         a :class:`dict` of converters keyed by config entry names,
         as described in :func:`load_schema`

  Returns:
       a :class:`Schema` as described in :func:`load_schema`
    
  """
  with open(yaml_file) as f:
    y = f.read()
  loaded = load_schema(y, converters)
  return loaded

def load_schema(spec, converters=None):
  """
  Creates a :class:`Schema` from the specification, `spec`.

  .. note:: If the schema specification is in a YAML file,
            then use :func:`phyles.read_schema`, which is a
            convenience wrapper around :func:`load_schema`.

  Args:

    `spec`:
        Can either be YAML text, a :class:`list` of
        2-:class:`tuples` with unique first elements,
        or a mapping object (e.g. :class:`dict`).
        If the schema is in a YAML file, then use
        :func:`phyles.read_schema`. The values
        of the items of `spec` are:

           1. converter
           2. example value
           3. help string
           4. default value (optional)

        Example YAML specification as a complete YAML file::

           %YAML 1.2
           ---
           !!omap
           - 'pdb model' : [str, my_model.pdb, null]
           - 'reset b-facs' : 
                 - float
                 - -1
                 - "New B factor (-1 for no reset)"
                 - -1
           - 'cell dimensions' : [get_cell, [200, 200, 200], null]

        The same example as a python specification via a
        :class:`list` of 2-:class:`tuples` with unique
        first elements::

           [('pdb model',
             ['str', 'my_model.pdb', None]),
            ('reset b-facs',
             ['float', -1, 'New B factor (-1 for no reset)', -1]),
            ('cell dimensions',
             [get_cell, [200, 200, 200], None])]

        For completeness, the same example as a :class:`dict`::

           {'pdb model': ['str', 'my_model.pdb', None],
            'reset b-facs':
              ['float', -1, 'New B factor (-1 for no reset)', -1],
            'cell dimensions': [get_cell, [200, 200, 200], None]}

        .. note:: The python structure (:class:`list` of
                  2-:class:`tuples`) of this example specification
                  is simply the result of parsing the YAML with
                  the `PyYAML`_ parser.  Because of isomorphism
                  between a :class:`list` of 2-:class:`tuples`
                  with unique first elements, :class:`OrderedDicts`,
                  :class:`dicts`, and other mapping types,
                  the specification may take any of these forms.

        The following YAML representation of a config conforms to
        the preceding schema specification::

           pdb model : model.pdb
           reset b-facs : 20
           cell dimensions : [59, 95, 159]

    `converters`:
        A :class:`dict` of `callables`_ keyed by converter name
        (which must match the converter names in `spec`), The
        callables convert values from the actual config.

        Converters that correspond to several native
        `python types`_ and `YAML types`_
        do not need to be explicitly specified. The names
        that these converters take in a schema specification
        and the corresponding python types produced by these
        converters are:

          - **map**: :class:`dict`
          - **dict**: :class:`dict`
            (encoded as a `YAML dict`_)
          - **omap**: :class:`collections.OrderedDict`
          - **odict**: :class:`collections.OrderedDict`
            (alias for "omap")
          - **pairs**: :class:`list` of 2-:class:`tuples`
          - **set**: :class:`set`
          - **seq**: :class:`list`
          - **list**: :class:`list`
            (encoded as a sequence, see :func:`list`)
          - **tuple**: :class:`tuple`
            (encoded as a sequence, see :func:`tuple`)
          - **bool**: :class:`bool`
          - **float**: :class:`float`
          - **int**: :class:`int`
          - **long**: :class:`long` (encoded as a `YAML int`_)
          - **complex**: :class:`complex`
            (encoded as a sequence of 0 to 2, or as a string
            representation, e.g. ``'3+2j'``; see :func:`complex`)
          - **str**: :class:`str`
          - **unicode**: :class:`unicode`
          - **timestamp**: :class:`datetime.datetime`
            (encoded as a `YAML timestamp`_)
          - **slice**: :class:`slice`
            (encoded as a sequence of 1 to 3, see :func:`slice`)

        .. note:: Except where noted, these types are encoded
                  according to the `YAML types`_ specification
                  in a YAML representation of a config.

  Returns:
    A fully constructed schema in the form of a
    :class:`Schema`. Most notably, the strings specifying
    the converters in the `spec` are replaced by the converters
    themselves.

  .. doctest::

    >>> import phyles
    >>> import textwrap
    >>> def get_cell(cell):
          return [float(f) for f in cell]
    >>> converters = {'get_cell' : get_cell}
    >>> y = '''
            %YAML 1.2
            ---
            !!omap
            - 'pdb model' : [str, my_model.pdb, null]
            - 'reset b-facs' : 
                  - float
                  - -1
                  - "New B factor (-1 for no reset)"
                  - -1
            - 'cell dimensions' : [get_cell, [200, 200, 200], null]
            '''
    >>> phyles.load_schema(textwrap.dedent(y), converters=converters)
    Schema([('pdb model',
             [<type 'str'>, 'my_model.pdb', None]),
            ('reset b-facs',
             [<type 'float'>, -1,
              'New B factor (-1 for no reset)', -1]),
            ('cell dimensions',
             [<function get_cell at 0x101d7cf50>,
              [200, 200, 200], None])])

  .. _`PyYAML`: http://pyyaml.org/
  .. _`callables`: http://en.wikibooks.org/wiki/Python_Programming/
  .. _`pairs`: http://yaml.org/type/pairs.html
  .. _`YAML dict`: http://yaml.org/type/dict.html
  .. _`YAML int`: http://yaml.org/type/int.html
  .. _`YAML timestamp`: http://yaml.org/type/timestamp.html
  .. _`YAML types`: http://yaml.org/type/
  .. _`python types`: http://docs.python.org/2/library/types.html
  """
  try:
    loaded = Schema(spec)
  except ValueError:
    if (len(spec) > 0):
      try:
        try :
          loaded = yaml.load(spec)
        except yaml.constructor.ConstructorError as e:
          _schema_error(e)
        loaded = unpack_omap(loaded)
      except AttributeError:
        loaded = unpack_omap(spec)
    else:
      loaded = []
    loaded = Schema(loaded)
  convs = CONVERTERS.copy()
  if converters is not None:
    convs.update(converters)
  for k, v in loaded.items():
    converter = v[0]
    if not (3 <= len(v) <= 4):
      msg = "Item '%s' of specification is not valid." % k
      _schema_error(msg)
    try:
      loaded[k][0] = convs[converter]
    except (TypeError, KeyError):
      if hasattr(converter, 'keys'):
        def _converter(i, key=k, c=converter):
          if i in c:
            return c[i]
          else:
            msg = "Bad value ('%s') for option '%s'." % (i, key)
            raise KeyError(msg)
        _converter.choices = tuple(converter)
        loaded[k][0] = _converter
      elif isinstance(converter, basestring):
        if converter.startswith("<") and converter.endswith(">"):
          atype = converter[1:-1]
          if atype in convs:
            loaded[k][0] = atype_or_list_of_atype(convs[atype])
            no_such_converter = False
        else:
            no_such_converter = True
        if no_such_converter:
          msg = "No such converter: '%s'" % converter
          _schema_error(msg)
      else:
        try:
          iter(converter)
        except TypeError as e:
          msg = "%s is not mapping, sequence or in converters." % v
          raise ConfigError(msg)
        else:
          def _converter(value, key=k, c=converter):
            if value in c:
              return value
            else:
              msg = "Bad value ('%s') for option '%s'." % (value, key)
              raise ValueError(msg)
          _converter.choices = tuple(converter)
          loaded[k][0] = _converter
  return loaded

def _ydump(v, newline=False):
  """
  This should really only be called with strings numbers.
  """
  r = yaml.dump(v, default_flow_style=True,
                   Dumper=yaml.dumper.SafeDumper)
  if r.endswith('\n...\n'):
    r = r[:-4]
  if not newline:
    if r.endswith('\n'):
      r = r[:-1]
  return r

def sample_config(schema):
  """
  Creates a sample config specification (returned as a :class:`str`)
  from the `schema`, as described in :func:`read_schema`.

  Args:
    `schema`: a :class:`Schema`

  Returns:
    A :class:`str` that is useful as a template config specification.
    Example values from the schema will be used. Additionally, the help
    strings will be inserted as reasonably formatted YAML comments.

  .. doctest::

    >>> import phyles
    >>> import textwrap
    >>> def get_cell(cell):
          return [float(f) for f in cell]
    >>> converters = {'get_cell' : get_cell}
    >>> y = '''
            !!omap
            - 'pdb model' : [str, my_model.pdb, null]
            - 'reset b-facs' : 
                  - float
                  - -1
                  - "New B factor (-1 for no reset)"
                  - -1
            - 'cell dimensions' : [get_cell, [200, 200, 200], null]
            '''
    >>> schema = phyles.load_schema(textwrap.dedent(y),
                                    converters=converters)
    >>> print phyles.sample_config(schema)
    %YAML 1.2
    ---
    <BLANKLINE>
    pdb model : my_model.pdb
    <BLANKLINE>
    # New B factor (-1 for no reset)
    reset b-facs : -1
    <BLANKLINE>
    cell dimensions : [200, 200, 200]
  """
  rstr = ["%YAML 1.2", "---"]
  last = len(schema) - 1
  was_help = True 
  for i, (key, value) in enumerate(schema.items()):
    if len(value) == 3:
      c, example, help_ = value
      d = Undefined
    else:
      c, example, help_, default = value
    if was_help:
      rstr.append("")
    if help_ is not None:
      if (not was_help) and (i > 0):
        rstr.append("")
      wrapper = textwrap.TextWrapper(initial_indent="# ",
                                     subsequent_indent="# ")
      rstr.append(wrapper.fill(help_))
      if hasattr(c, "choices"):
        choices = "One of: " + ", ".join([str(_c) for _c in c.choices])
        rstr.append(wrapper.fill(choices))
      key = _ydump(key)
      example = _ydump(example)
      rstr.append('%s : %s' % (key, example))
      was_help = True
    else:
      rstr.append('%s : %s' % (key, example))
      was_help = False
  return "\n".join(rstr)

def validate_config(schema, config):
  """
  Takes a YAML specification for a configuration, `config`,
  and uses the `schema` (as described in
  :func:`load_schema`) for validation, which:

     1. checks for required config entries, raising
        a :class:`ConfigError` if any are missing
     2. ensures that no unrecognized config entries are
        present, raising a :class:`ConfigError` in any such
        entries are present
     3. ensures, through the use of converters, that the
        values given in the config specification are of
        the appropriate types and within accepted limits
        (if applicable), raising a :class:`ConfigError`
        if any fail to convert
     4. uses the converters to turn values given in
        the configuration into values of the appropriate
        types (e.g. the `YAML str`_ ``'1+4j'`` is converted
        into the python :class:`complex` number ``(1+4j)`` if
        the converter is ``'complex'``)

  .. note::

        **Why is conversion a part of validation?**
        Conversion facilitates the end-user's working
        with a minimal subset of the YAML vocabulary.
        In the :class:`complex` number example above, the
        end-user only needs to know how complex numbers are
        usually represented (e.g. ``'1+4j'``) and
        not what gibbersh like
        ``'!!python/object:__main__.SomeComplexClass'`` `means
        <http://pyyaml.org/wiki/PyYAMLDocumentation#LoadingYAML>`_,
        where to put it, how to specify its attributes, etc.

  Args:
    `config`:
       a mapping (e.g. :class:`OrderedDict` or :class:`dict`)
       of configuration entries
    `schema`:
       a :class:`Schema` as described in :func:`load_schema`

  Returns:
    The converted config as a :class:`Configuration`.

  Raises:
    :class:`ConfigError`

  .. doctest::

    >>> import phyles
    >>> import textwrap
    >>> import yaml
    >>> def get_cell(cell):
          return [float(f) for f in cell]
    >>> converters = {'get_cell' : get_cell}
    >>> y = '''
            %YAML 1.2
            ---
            !!omap
            - 'pdb model' : [str, my_model.pdb, null]
            - 'reset b-facs' : 
                  - float
                  - -1
                  - "New B factor (-1 for no reset)"
                  - -1
            - 'cell dimensions' : [get_cell, [200, 200, 200], null]
            '''
    >>> schema = phyles.load_schema(textwrap.dedent(y),
                                    converters=converters)
    >>> y = '''
            pdb model : model.pdb
            reset b-facs : 20
            cell dimensions : [59, 95, 159]
            '''
    >>> cfg = yaml.load(textwrap.dedent(y))
    >>> cfg
    {'cell dimensions': [59, 95, 159],
     'pdb model': 'model.pdb',
     'reset b-facs': 20}
    >>> phyles.validate_config(schema, cfg)
    Configuration([('pdb model', 'model.pdb'),
                   ('reset b-facs', 20.0),
                   ('cell dimensions', [59.0, 95.0, 159.0])])

  .. _`YAML str`: http://yaml.org/type/str.html
  """
  validated = Configuration(config)
  for k in config:
    if k not in schema:
      msg = "Unknown setting: '%s'" % k
      raise ConfigError(msg)
  for k, v in schema.items():
    if len(v) == 3:
      converter, example, help_ = v
      default = Undefined
    else:
      converter, example, help_, default = v
    value = config.get(k, default)
    if value is Undefined:
      msg = "Settings file must specify a value for '%s'." % k
      raise ConfigError, msg
    try:
      validated[k] = converter(value)
    except (ValueError, TypeError, KeyError) as e:
      raise ConfigError(str(e))
  return validated

def read_cfg(config_file):
  if not os.path.exists(config_file):
    msg = 'Settings file "%s" does not exist.' % config_file
    raise ConfigError(msg)
  try:
    msg = 'Problem reading settings file "%s".' % config_file
    with open(config_file) as f:
      settings = f.read()
  except IOError:
    raise ConfigError(msg)
  cfg = yaml.load(settings)
  return cfg


def read_config(schema, config_file):
  """
  Reads a YAML config file from the the file named
  `config_file` and returns the config validated
  by `schema`.

  Args:
    `config_file`:
         YAML file holding the config, for example::

              pdb model : model.pdb
              reset b-facs : 20
              cell dimensions : [59, 95, 159]

    `schema`: a :class:`Schema` as described in :func:`load_schema`

  Returns:
     a :class:`Configuration`
  """
  cfg = read_cfg(config_file)
  return validate_config(schema, cfg)

def _last_made_helper(dirpath, suffix):
  # get all entries in the directory w/ stats
  entries = [os.path.join(dirpath, fn) for fn in os.listdir(dirpath)]
  entries = [(os.stat(path), path) for path in entries]

  # leave only regular files, insert creation date
  entries = [(stat[ST_CTIME], path)
             for stat, path in entries if S_ISREG(stat[ST_MODE])]

  if suffix is not None:
    if isinstance(suffix, basestring):
      suffix = (suffix,)
    selected = []
    for sfx in suffix:
      es = [e for e in entries if e[1].endswith(sfx)]
      selected.extend(es)
    entries = selected

  entries.sort(reverse=True)

  if entries:
    result = entries[0]
  else:
    result = None

  return result

def last_made(dirpath='.', suffix=None, depth=0):
  """
  Returns the most recently created file in `dirpath`. If provided,
  the newest of the files with the given suffix/suffices is returned.
  This will recurse to `depth`, with `dirpath` being at depth 0 and
  its children directories being at depth 1, etc. Set `depth` to
  any value but 0 or a positive integer if recursion should be exauhstive
  (e.g. ``-1`` or ``None``).

  Returns ``None`` if no files are found that match `suffix`.

  The `suffix` parameter is either a single suffix
  (e.g. ``'.txt'``) or a sequence of suffices
  (e.g. ``['.txt', '.text']``).
  """
  result = None
  i = 0
  for (apath, dirs, files) in os.walk(dirpath):
    newest = _last_made_helper(apath, suffix)
    if ((newest is not None) and
        ((result is None) or (newest[0] > result[0]))):
      result = newest
    if (i == depth):
      break
    else:
       i += 1
  return result[1]

def wait_exec(cmd, instr=None):
  """
  Waits for `cmd` to execute and returns the output
  from stdout. The `cmd` follows
  the same rules as for python's :class:`popen2.Popen3`.
  If `instr` is provided, this string is passed to
  the standard input of the child process.

  Except for the convenience of passing `instr`, this
  funciton is somewhat redundant with pyhon's
  :func:`subprocess.call`.
  """
  handle = subprocess.Popen(cmd,
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            close_fds=True)

  if instr is None:
    out, err = handle.communicate()
  else:
    out, err = handle.communicate(input=instr)

  if out is None:
    out = ""

  return out


def doyn(msg, cmd=None, exc=os.system, outfile=None):
  """
  Uses the :func:`raw_input` builtin to query the user a
  yes or no question. If `cmd` is provided, then
  the function specified by `exc` (default :func:`os.system`)
  will be called with the argument `cmd`.

  If a file name for `outfile` is provided, then stdout will be
  directed to a file of that name.
  """
  while True:
    yn = raw_input("\n" + msg + " [y or n] ")
    if yn.strip().lower() == "y":
      yn = True
      if cmd is None:
        out = None
      else:
        try:
          out = exc(cmd, outfile=outfile)
        except TypeError:
          out = exc(cmd)
      if out is not None:
        if outfile is None:
          sys.stdout.write(str(out))
          sys.stdout.write("\n")
        else:
          with open(outfile, "w") as f:
            f.write(out)
      break
    elif yn.strip().lower() == "n":
      yn = False
      break
    print "Didn't understand your response. Answer 'y' or 'n'."
  return yn


def banner(program, version, width=WIDTH):
  """
  Uses the `program` and `version` to print a banner to stderr.
  The banner will be printed at `width` (default 70).

  Args:
    `program`: :class:`str`

    `version`: :class:`str`

    `width`: :class:`int`
  """
  hline = "=" * width
  sys.stderr.write(hline + "\n")
  p = ("%s v.%s " % (program, version)).center(width)
  sys.stderr.write(p + "\n")
  sys.stderr.write(hline + "\n")

def format_error_message(msg, width, pad):
  lead_space = " " * (pad)
  w = width - pad
  err = ' ERROR '.center(w, '#').center(width)
  errbar = '#' * w
  errbar = errbar.center(width)
  msg_list = str(msg).splitlines()
  msg = []
  for aline in msg_list:
    aline = lead_space + aline.rstrip()
    msg.append(aline)
  msg = "\n".join(msg)
  msg = '\n'.join(('', err, '', msg, '', errbar, ''))
  return msg

def usage(parser, msg=None, width=WIDTH, pad=PAD):
  """
  Uses the `parser` (:class:`argparse.ArgumentParser`) to
  print the usage. If `msg` (which can be an :class:`Exception`,
  :class:`str`, etc.) is supplied then it will be printed as an error
  message, hopefully in a way that catches the user's eye. The usage
  message will be formatted at `width` (default 70). The `pad`
  is used to add some extra space to the beginning of the error
  lines to make them stand out (default 4).
  """
  hline = '=' * width
  if msg is not None:
    print format_error_message(msg, width, pad)
    print hline
  print
  print parser.format_help()
  sys.exit(0)

def graceful(msg=None, width=WIDTH, pad=PAD):
  """
  Gracefully exits the program with an error message.

  The `msg`, `width` and `pad` arguments are the same
  as for :func:`usage`.
  """
  print format_error_message(msg, width, pad)
  sys.exit(0)

def get_home_dir():
    """
    Returns the home directory of the account under which
    the python program is executed. The home directory
    is represented in a manner that is comprehensible
    by the host operating system (e.g. ``C:\\something\\``
    for Windows, etc.).
    
    Adapted directly from K. S. Sreeram's approach, message
    393819 on c.l.python (7/18/2006). I treat this code
    as public domain.
    """
    if sys.platform != 'win32' :
        return os.path.expanduser( '~' )
    def valid(path) :
        if path and os.path.isdir(path) :
            return True
        return False
    def env(name) :
        return os.environ.get( name, '' )
    homeDir = env( 'USERPROFILE' )
    if not valid(homeDir) :
        homeDir = env( 'HOME' )
        if not valid(homeDir) :
            homeDir = '%s%s' % (env('HOMEDRIVE'),env('HOMEPATH'))
            if not valid(homeDir) :
                homeDir = env( 'SYSTEMDRIVE' )
                if homeDir and (not homeDir.endswith('\\')) :
                    homeDir += '\\'
                if not valid(homeDir) :
                    homeDir = 'C:\\'
    return homeDir

def basic_logger(name, level=logging.INFO):
  """
  Returns an instance of :class:`logging.Logger` named `name` with
  level of `level` (defaults to `logging.INFO`). The format of the
  messages is "%(levelname)s: %(message)s".
  """
  logger = logging.getLogger(name)
  logger.setLevel(level)
  ch = logging.StreamHandler()
  ch.setLevel(level)
  formatter = logging.Formatter("%(levelname)s: %(message)s")
  ch.setFormatter(formatter)
  logger.addHandler(ch)
  return logger

def get_data_path(env_var, package_name, data_dir):
  """
  Returns the path to the data directory. First
  it looks for the directory specified in the
  `env_var` environment variable and if that directory
  does not exists, finds `data_dir` in one of the
  following places (in this order):

    1. The package directory (i.e. where the ``__init.py__`` is
       for the package named by the `package_name` parameter)
    2. If the package is a file, the directory holding
       the package file
    3. If frozen, the directory holding the frozen executable
    4. If frozen, the parent directory of the directory
       holding the frozen executable
    5. If frozen, the first element of `sys.path`

  Thus, if the package were at ``/path/to/my_package``,
  (i.e. with ``/path/to/my_package/__init__.py``),
  then a very reasonable place for the data directory would be
  ``/path/to/my_package/package-data/``.

  The anticipated use of this function is within the package
  with which the data files are associated. For this use,
  the package name can be found with the global variable
  `__package__`_, which for this example would have the value
  ``'my_package'``. E.g.::

     pth = get_data_path('MYPACKAGEDATA', __package__, 'package-data')

  This code is adapted from `_get_data_path()`
  from matplotlib ``__init__.py``. Some parts of this code
  are most likely subject to the `matplotlib license`_.

  .. note::

       The `env_var` argument can be ignored using
       ``phyles.Undefined`` because it's guaranteed not to
       be in :attr:`os.environ`:

       ::

           pth = get_data_path(Undefined, __package__, 'package-data')


  .. warning::

       The use of ``'__package__'`` for `package_name` will fail
       in certain circumstances.  For example, if the value of
       ``__name__`` is ``'__main__'``, then ``__package__``
       is usually ``None``. In such cases, it is necessary
       to pass the package name explicitly.

       ::

          pth = get_data_path(Undefined, 'my_package', 'package-data')

  .. _`matplotlib license`:
     http://matplotlib.sourceforge.net/users/license.html
  .. _`__package__`: http://www.python.org/dev/peps/pep-0366/
  """

  if env_var in os.environ:
    p = os.environ[env_var]
    if os.path.isdir(p):
      return p
    else:
      tmplt = 'Path in environment variable "%s" is not a directory.'
      msg = tmplt % env_var
      raise RuntimeError(msg)

  finder = modulefinder.ModuleFinder()
  node = finder.find_module(package_name, None)[1]
  if os.path.isdir(node):
    d = node
  else:
    d = os.path.dirname(node)
  p = os.sep.join([d, data_dir])
  if os.path.isdir(p):
    return p

  if getattr(sys, 'frozen', False):
    exe_path = os.path.dirname(sys.executable)
    p = os.path.join(exe_path, data_dir)
    if os.path.isdir(p):
      return p

    # Try again assuming we need to step up one more directory
    p = os.path.join(os.path.split(exe_path)[0], data_dir)
    if os.path.isdir(p):
      return p

    # Try again assuming sys.path[0] is a dir not a exe
    p = os.path.join(sys.path[0], data_dir)
    if os.path.isdir(p):
      return p

  msg = 'Could not find the %s data files.' % package_name
  raise RuntimeError(msg)


def format_config_dict(config, first_space=None):
  """
  The `config` must be a dictionary or other mapping.
  If given, `first_space` will replace the first space of any
  leading space.
  """
  config = dict(config)
  pp = pprint.PrettyPrinter(indent=2)
  f = " " + pp.pformat(config)[1:-1]
  f = f.replace(r"\n'", "'")
  f = re.sub(r"\\n +", " ", f)
  f = textwrap.dedent(f)
  if first_space is not None:
    f = f.replace('\n ', '\n' + first_space)
  return f

def default_argparser():
  """
  Returns a default :class:`argparse.ArgumentParser` with
  mutually exclusive template (``-t``, ``--template``)
  and config (``-c``, ``--config``) arguments added. It
  also has the override (``-o``, ``--override``) option
  added, to override configuration items on the command line.

  The argument to ``--override`` should be a valid `YAML map`_
  (with the **single** exception that the outermost curly braces
  are optional for `YAML flow style`_).  Because YAML relies on
  syntactically meaningful whitespace, single quotes should
  surround the argument to ``--override``.

  The following examples execute a program called
  ``program``, overriding ``opt1`` and ``opt2``
  of the config in the file ``config.yml``
  with ``foo`` and ``bar``, respctively::

     program -c config.yml -o 'opt1 : foo, opt2 : bar'

  ::

     program -c config.yml -o '{opt1 : foo, opt2 : bar}'

  ::

     program -c config.yml -o 'opt1 : foo\\nopt2 : bar'


  .. note:: The latter example illustrates how `YAML block style`_
            can be used with ``--override``: a single forward slash
            (``\\``) escapes an ``n``, which evaluates to a
            so-called "newline". In other words, the YAML that
            corresponds to this latter example is::

               opt1 : foo
               opt2 : bar

            Similarly, other escape sequences can also be used
            with ``--override``. For example, the following
            overrides an option called ``sep``, setting its value
            to the tab character::

               program -c config.yml -o 'sep : "\\t"'


  Returns: :class:`argparse.ArgumentParser`

  .. _`YAML map`: http://yaml.org/type/map.html
  .. _`YAML flow style`: http://yaml.org/spec/current.html#id2544175
  .. _`YAML block style`: http://yaml.org/spec/current.html#id2545757
  """
  parser = argparse.ArgumentParser()

  group = parser.add_mutually_exclusive_group(required=True)

  group.add_argument("-t", "--template",
                     action="store_true", default=False,
                     help="print template settings file",
                     dest="template")

  group.add_argument("-c", "--config", default=None, type=str,
                     help="config file to further specify conversion",
                     metavar="CONFIGFILE", dest="config")

  parser.add_argument("-o", "--override", default=None, type=str,
                      help="override settings in config file",
                      metavar="OVERRIDE_SETTINGS", dest="override")

  return parser

def parse_override(override):
  """
  Parses the ``--override`` argument, which overrides
  config file settings.
  """
  y = override.decode('string_escape')
  cfg = yaml.load(y)
  try:
    {}.update(cfg)
  except:
    y = "{" + y + "}"
    cfg = yaml.load(y)
    try:
      {}.update(cfg)
    except:
      msg = "value for --override option is not a mapping object"
      raise OptionError(msg)
  return cfg

def run_main(main, config, catchall=DummyException):
  """
  Trivial convenience function that runs a `main` function
  within a try-except block. The `main` function should take
  as its sole argument the `config`, which is a mapping object
  that holds the configuration (usually a :class:`Configuration`
  object). The `catchall` is an :class:`Exception` or a
  tuple of :class:`Exceptions`, which if caught will result in a
  graceful exit of the program (see :func:`graceful`).

  Args:
    `main`: a function, equivalent to the main function of a program

    `config`: a mapping object, usually a :class:`Configuration`
     which is generally produced by :func:`validate_config` or
     :func:`read_config`

    `catchall`: an :class:`Exception` or a :class:`tuple` of
    :class:`Exceptions`
  """
  try:
    main(config)
  except catchall, e:
    graceful(e)

def _schema_error(e):
  msg = ("Schema specification error:\n\n" +
         "-----\n\n%s\n\n-----\n\n" + \
         "This may be an internal error. " +
         "If you didn't write the schema\n" +
         "specification, then please contact " +
         "the program author.\n") % (e,)
  graceful(msg)

def set_up(program, version, spec, converters=None):
  """
  Given the name of the program (`program`), the `version`
  string, the specification for the schema (`spec`;
  described in :func:`load_schema`), and `converters`
  for the schema (also described in :func:`load_schema`),
  this function:

    1. sets up the default argparser (see
       :func:`default_argparser`)

    2. prints the template or banner as appropriate (see
       :func:`template` and :func:`banner`)

    3. creates a schema and uses it to validate the config
       (see :func:`load_config` and :func:`validate_config`)

    4. overrides items in the config according to the command
       line option ``--override`` or ``-o`` (see
       :func:`default_argparser` for a description of ``--override``)

    5. exits gracefully with :func:`usage` if any problems are
       found in the command line arguments of config

    6. returns a :class:`dict` of the
       :class:`argparse.ArgumentParser`, the parsed command line
       arguments, the :class:`Schema`, and the :class:`Configuration`
       with keys ``'argparser'``, ``'args'``, ``'schema'``,
       ``'config'``, respectively

  Args:
    `program`: the program name as a :class:`str` 

    `version`: the program version as a :class:`str`

    `spec`: a schema specification as described in
    :func:`load_schema`

    `coverters`: a :class:`dict` of converters as described
    in :func:`load_schema`


  Returns: a :class:`dict` with the keys:

      1. ``'argparser'``: :class:`argparse.ArgumentParser`

      2. ``'args'``: the parsed command lines arguments as a 
         :class:`argparse.Namespace`

      3. ``'schema'``: schema for the configuration
         as a :class:`Schema`

      4. ``'config'``: the configuration
         as a :class:`Configuration`
  """
  parser = default_argparser()
  args = parser.parse_args()
  try:
    schema = load_schema(spec, converters=converters)
  except yaml.constructor.ConstructorError as e:
    _schema_error(e)
  if args.template:
    print schema.sample_config()
    sys.exit()
  else:
    banner(program, version)
    try:
      cfg = read_cfg(args.config)
      if args.override is not None:
        override_cfg = parse_override(args.override)
        for k in override_cfg:
          if k in schema:
            cfg[k] = override_cfg[k]
          else:
            msg = "Command line option '%s' for is not valid." % k
            raise ConfigError(msg)
      config = schema.validate_config(cfg)
    except (ConfigError, OptionError,
            yaml.constructor.ConstructorError) as e:
      usage(parser, e)
    return {'argparser': parser,
            'args': args,
            'schema': schema,
            'config': config}

def package_spec(env_var, package_name, data_dir, specfile_name):
  """
  Reads and returns the contents of a schema specification
  somewhere in a package as YAML text (described in
  :func:`load_schema`). 

  This function pulls out all the stops to find the specification.
  It is best to try to give all of `env_var`, `package_name`,
  and `data_dir` if they are available to have the best chance
  of finding the path to the specification file. See
  :func:`get_data_path` for a full description.

  Args:
    The arguments `env_var`, `package_name`, and `data_dir` are
    identical to those required in :func:`get_data_path`.

    `specfile_name`: name of the schema specification file found
    within the package contents.

  Returns:
    A YAML string specifying the schema.
  """
  try:
     p = os.path.join(data_dir, specfile_name)
     result = pkg_resources.resource_string(package_name, p)
  except IOError:
     dirpath = get_data_path(env_var, package_name, data_dir)
     filepath = os.path.join(dirpath, specfile_name)
     with open(filepath) as f:
       result = f.read()
  return result

def prune(patterns, doit=False):
  """
  Recursively deletes files matching the specified unix style
  `patterns`. The `doit` parameter must be explicitly set to
  ``True`` for the files to actually get deleted, otherwise,
  it just logs with :func:`logging.info` what *would* happen.
  Raises a :class:`SystemExit` if deletion of any file
  is unsuccessful (only when `doit` is ``True``).

  Example::

     prune(['*~', '*.pyc'], doit=True)

  Args:
    - `patterns`: :class:`list` of unix style pathname patterns
    - `doit`: :class:`bool`

  Returns: ``None``

  Raises: :class:`SystemExit`
  """
  if doit:
    erasing = "Erasing: %s"
  else:
    erasing = "Would erase: %s"
  for (path, dirs, files) in os.walk('.'):
    g = []
    for pattern in patterns:
      p = os.path.join(path, pattern)
      _g = glob.glob(p)
      g.extend(_g)
    g = set(g)
    if g:
      for f in g:
        logging.info(erasing, f)
        if doit:
          try:
            os.remove(f)
          except Exception as e:
            logging.exception(e)
            sys.exit(e)

def _pack_skeleton():
  listing = [(n + "/" if os.path.isdir(n) else n)
                                 for n in os.listdir(SKEL)]
  s = "   " + "\n   ".join(listing)
  print
  print "Creating zip archive of directory '%s':" % SKEL
  print
  print s
  print
  zname = SKEL + '.zip'
  print "New archive is '%s'." % zname
  zipdir(SKEL, zname)
  print

def _unpack_skeleton(config):
   """
   Unpacks skeleton specified in `config`, which has the
   following keys:

      - ``zip_name``: Name of the zip file holding the skeleton
                      template as a zip file
      - ``data_dir``: Directory holding the skeleton template
      - ``extension``: File name extension (without the leading '.')
            Files ending with this extension will
              1. be formatted with config, as if with the pseduocode
                 ``file_contents % config``
              2. have the extension (and leading '.') removed from
                 the name before being written to the filesystem
   """
   config = config.copy()
   title = " " + config['package'] + " "
   hline = "=" * (len(title))
   config['package_header'] = "\n".join([hline, title, hline])
   zip_path = os.path.join(config['data_dir'],
                           config['zip_name'])
   z = ZipFile(zip_path, 'r')
   extension = config['extension']
   last = -(len(extension) + 1)
   print
   print "Unpacking '%s' directory archive." % config['zip_name']
   print
   for name in z.namelist():
     print "  " + name
     if name.endswith(extension):
       bytes = z.read(name)
       name = name[:last]
       bytes = bytes % config
       with open(name, 'w') as f:
         f.write(bytes)
     else:
       z.extract(name)
   print

def map_nested(nested, amap, pop=False):
  """
  Maps a mapping object `amap` to a `nested` iterable of keys.
  If `pop` is ``True``, then the items matching keys in `nested`
  are popped from `amap`.

  Args: 
    - `nested`: nested iterable (e.g. :class:`list`)
    - `amap`: mapping object (e.g. :class:`dict`)

  Kwargs:
    - `pop`: bool
 

  Args: :class:`collections.Iterable`

  Returns: :class:`list`

  >>> nested = ("a", (("b", "c"), "d"), "e")
  >>> amap = dict(zip("abcde", range(5)))
  >>> map_nested(nested, amap)
  [0, [[1, 2], 3], 4]
  """
  built = []
  for n in nested:
    if (isinstance(n, collections.Iterable) and
                         not isinstance(n, basestring)):
      built.append(map_nested(n, amap, pop=pop))
    else:
      if pop:
        built.append(amap.pop(n))
      else:
        built.append(amap[n])
  return built

def flatten(nested):
  """
  Flattens an arbitrarily nested iterable (`nested`).

  Taken from http://goo.gl/FfcWA.

  Args:
    -`nested`: :class:`collections.Iterable`

  Returns: :class:`list`
  """
  for el in alist:
    if (isinstance(el, collections.Iterable) and
        not isinstance(el, basestring)):
      for sub in flatten(el):
        yield sub
      else:
        yield el

def mapify(f):
  """
  Given a function `f` with an arbitrary set of arguments
  and keyword arguments, a new function is returned that
  instead takes as an argument a mapping object (e.g.
  a :class:`dict`) that has as keys the original arguments
  and keyword arguments of `f`.

  If f has "kwargs", as in (``def f(**kwargs):``), then items
  in the mapping object that do not correspond to any arguments
  or defaults are included in kwargs. See the ``'extra'`` key
  in the first example in the doctest below.

  Args:
    - `f`:a function

  Returns: a function

  >>> amap = {'a': 1, 'b': 2, 'c': 3, 'd': 42,
  ...         'args': [7, 8],
  ...         'kwargs': {'bob':39, 'carol':36},
  ...         'extra': 99}
  >>> @mapify
  ... def f(a, (b, c), d=2, *args, **kwargs):
  ...   print "a=%s  (b=%s  c=%s) d=%s" % (a, b, c, d)
  ...   print "args are: %s" % (args,)
  ...   print "kwargs are: %s" % (kwargs,)
  ...
  >>> f(amap)
  a=1  (b=2  c=3) d=42
  args are: (7, 8)
  kwargs are: {'bob': 39, 'carol': 36, 'extra': 99}
  >>> @mapify
  ... def g(a):
  ...   print "a is: %s" % (a,)
  ... 
  >>> g(amap)
  a is: 1
  >>> @mapify
  ... def h(y=4, *args):
  ...   print "y is: %s" % (y,)
  ...   print "args are: %s" % (args,)
  ... 
  >>> h(amap)
  y is: 4
  args are: (7, 8)
  """
  a = inspect.getargspec(f)
  args = a.args
  varargs = a.varargs
  keywords = a.keywords
  defaults = [] if a.defaults is None else a.defaults
  first = -len(defaults)
  default_args = args[first:]
  def _f(amap):
    amap = amap.copy()
    if defaults:
      for k, v in zip(default_args, defaults):
        if k not in amap:
          amap[k] = v
    _args = map_nested(args, amap, pop=True)
    if varargs is not None:
      _args += list(amap.pop(varargs, []))
    if keywords is None:
      _keywords = {}
    else:
      _keywords = amap.pop(keywords, {})
      _keywords = _keywords.copy()
      _keywords.update(amap)
    return f(*_args, **_keywords)
  return _f

def preserve_original(apath):
  if os.path.exists(apath):
    bak = apath + ".orig"
    msg = "File '%s' exists. Renaming to '%s'."
    logging.warning(msg, apath, bak)
    os.rename(apath, bak)


def _quickstart_main(config):
  package = config['package']
  config['zip_name'] = config['archive_dir'] + ".zip"
  if not os.path.exists(config['package']):
    os.mkdir(config['package'])
  version_path = os.path.join(package, "_version.py")
  preserve_original(version_path)
  with open(version_path, "w") as f:
    version = "%(major)s.%(minor)s.%(micro)s%(tag)s" % config
    f.write("__version__ = '%s'\n" % version)
  init_path = os.path.join(package, "__init__.py")
  preserve_original(init_path)
  with open(init_path, "w") as f:
    body = """
           #! /usr/bin/env python

           '''
           %(package)s: %(description)s
           %(copyright)s
           '''

           from _version import __version__
           """
    body = textwrap.dedent(body[1:]) % config 
    f.write(body)
  _unpack_skeleton(config)
  for dirname in ["_build", "_static", "_templates"]:
    pth = os.path.join("docs", dirname)
    if not os.path.exists(pth):
      os.mkdir(pth)
  doc_index_path = os.path.join("docs", "index.rst")
  preserve_original(doc_index_path)
  with open(doc_index_path, "w") as f:
    title_line = "%(package)s Documentation" % config
    title_underline = ("=" * len(title_line))
    body = """
           .. Created by phyles-quickstart.
              Add some items to the toctree.

           %s
           %s

           %s

           .. toctree::
              :maxdepth: 2
              :numbered:


           Indices and tables
           ==================

           * :ref:`genindex`
           * :ref:`modindex`
           * :ref:`search`
           """
    params = (title_line, title_underline, config['description'])
    body = textwrap.dedent(body) % params
    f.write(body[1:])

def _tag(tag):
  if tag in (None, "None", "none", "NONE"):
    tag = ''
  else:
    tag = str(tag)
  return tag

def _quickstart():
  program = "phyles-quickstart"
  spec = package_spec(Undefined, PACKAGE,
                      PACKAGE_DATA, QUICKSTART_SCHEMA)
  converters = {"tag" : _tag}
  setup = set_up(program, __version__, spec, converters=converters)
  config = setup['config']
  config['archive_dir'] = SKEL
  config['data_dir'] = get_data_path(PHYLES_DATA,
                                         PACKAGE, PACKAGE_DATA)
  config['extension'] = PHYLES_TEMPLATE
  run_main(_quickstart_main, config)

def zipdir(basedir, archivename):
    """
    Uses python zipfile package to create a zip archive of
    the directory `basedir` and store the archive to
    `archivename`.

    Virtually unmodified from http://goo.gl/Ty5k9
    except that empty directories aren't ignored.

    Args:
      - `basedir`: directory to zip as :class:`str`
      - `archivename`: name of zip archive a :class:`str`

    Returns: ``None``
    """

    if not os.path.isdir(basedir):
      tplt = "Can't zip a directory that isn't a directory:\n  %s"
      msg = tplt % basedir
      raise ArchiveError(msg)

    length_basedir = len(basedir)
    length_pfx = length_basedir + len(os.sep)
    with closing(ZipFile(archivename, "w", ZIP_DEFLATED)) as z:
      for root, dirs, files in os.walk(basedir):
        if files:
          for fn in files:
            absfn = os.path.join(root, fn)
            zfn = absfn[length_pfx:]
            z.write(absfn, zfn)
        else:
          zrn = root[length_basedir:]
          z.write(root, zrn)

def __make_license(license_tmplt, license_out, info_module):
  """
  UNSUPPORTED

  This seems like some pointless code that I wrote while
  carried away. I may find a use for it some time.

  Uses the information in the python module `info_module`
  to create a file named `license_out` from a file
  named `license_tmplt`.

  This is adapted somewhat from the python imp module
  documentation.

  >>> import os
  >>> os.remove('LICENSE.txt')
  >>> open('info.py', 'w').write('author = "James"')
  >>> open('LICENSE.tmplt', 'w').write('Author is %(author)s.\n')
  >>> make_license('LICENSE.tmplt', 'LICENSE.txt', 'info.py')
  >>> open('LICENSE.txt').read()
  'Author is James.\n'
  """
  path = os.path.dirname(info_module)
  if not path:
    path = '.'
  basename = os.path.basename(info_module)
  name = basename.rsplit('.')[0]
  if name in sys.modules:
    info = sys.modules[name]
  else:
    fp, pathname, description = imp.find_module(name, [path])
    try:
      info = imp.load_module(name, fp, pathname, description)
    finally:
      if fp:
        fp.close()

  
  with open(license_tmplt) as f:
    t = f.read()
  s = t % vars(info)
  with open(license_out, "w") as f:
    f.write(s)
