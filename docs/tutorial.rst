Tutorial
========

For the sake of a tutorial, lets assume that we need to calculate
cooking times for our barbecue. For this daunting task, we decide
we want a utility: a program that we can run from the command line
whenever we get the urge for a taste of smokey goodness.


The Calculation
---------------

.. note::

    This section isn't as much about using phyles as it is
    about framing the purpose of the example utility
    quantitatively (*i.e.* into numbers) and in a way that
    can be formulated as a python function. Hopefully
    the example is not too complicated. However, I have
    tried to make it just complicated enough to warrant
    a full-fledged utility.

Let's assume that we have three dishes we usually barbecue:

   ==================  ============
    Dish                Difficulty 
   ==================  ============
    vegetable kabobs       1 dc
    smoked salmon          2 dc
    brisket                3 dc
   ==================  ============

The numbers to the right of each dish gives the
**difficulty** of cooking (which we'll abbreviate as "dc"
to express its units).

As an example of difficulty, cooking a typical batch of vegetable
kabobs for 1 hour at some some temperature (say 200 °F) is
equivalent to cooking a typical brisket for 3 hours at that
temperature. Or stated another way, brisket cooks about three
times as slow as vegetable kabobs.

For the sake of this tutorial, cooking difficulty applies to
temperature as well.  For instance, cooking a typical batch of
vegetable kabobs at 200 °F for 2 hours is equivalent to cooking a
typical brisket at 600 °F for 2 hours:

.. math::

    \frac{200 \,^{\circ}\mathrm{F} \times 2 \,\mathrm{hr}}
         {1 \,\mathrm{dc}} =
    \frac{600 \,^{\circ}\mathrm{F} \times 2 \,\mathrm{hr}}
         {3 \,\mathrm{dc}}

Note how we divided both sides of the equation by
the difficulty of cooking for the respective dish
(1 dc for vegetable kabobs; 3 dc for brisket).
This calculation shows that we can quantify how
much we cook something by calculating what we'll call
the "doneness". Taking this example for brisket:

.. math::

    400 \,\text{doneness} =
    \frac{600 \,^{\circ}\mathrm{F} \times 2 \,\mathrm{hr}}
         {3 \,\mathrm{dc}}

Or, as a mathematical formula:

.. math::

    \text{doneness} =
    \displaystyle
         \frac
            {\text{temperature} \times \text{time}}
            {\text{difficulty}}

Using algebra [#alg]_, we can rearrange this equation to calculate
cooking times:

.. math::

     \text{time} = 
     \displaystyle
          \frac
             {\text{doneness} \times
              \text{difficulty}}
             {\text{temperature}}

In other words, if we know the amount we need to cook
a dish (doneness), how difficult the dish
is to cook (difficulty), and the temperature that
we can achieve with our grill, then we can calculate
the cooking time.

So, how much do we want to cook an dish? This table
quantifies doneness for several common
cooking terms:

  ===========  ==========
   Term         Doneness
  ===========  ==========
   Rare           200
   Medium         350
   Well-Done      500
  ===========  ==========

Let's try a calculation for smoked salmon (difficulty of 2) cooked
medium (doneness of 350) at 225 °F (which is about 107 °C):

.. math::

    \text{time} = 
    \displaystyle
         \frac
            {350 \,\text{doneness} \times
             2 \,\mathrm{dc}}
            {225 \,^{\circ}\mathrm{F}} \approx 3.11 \,\mathrm{hr}

Thus it takes about 3.11 hr to cook a smoked salmon
to medium at 225 °F.

As a python function, this calculation might take the form:

.. code-block:: python

    def cooking_time(doneness, difficulty, temperature):
      """
      Return then cooking time given the desired `doneness`
      cooking, the `difficulty` of cooking,
      and the `temperature`.

       Args:
         - `doneness`: desired doneness (hr•°F/dc)
         - `difficulty`: difficulty of cooking for the dish (dc)
         - `temperature`: cooking temperature (°F)

       Returns: cooking time in hours (``float``)

       Raises: ``ValueError`` if the `temperature` is <= 120 °F

       >>> round(cooking_time(350, 2, 225), 2)
       3.11
       """
       if T <= 120:
         msg = "%s °F is too cold to cook!" % T
         raise ValueError(msg)
       return float(doneness * difficulty) / T



The Config Format
-----------------

Assuming that we have a utility that calulates cooking times based
on a config file, the file for this example might take the
following form:

.. code-block:: yaml

    dish : smoked salmon
    doneness : medium
    temperature : 225

This config format is convenient for a user who doesn't care that
smoked salmon has a difficulty of 1 dc or that medium corresponds
to a doneness of 350. However, it places a burden on the programmer
to read the file, ensure that "smoked salmon" and "medium" are
spelled correctly, and convert these string values into numbers.

That's where phyles comes in!


Conversion
----------

Dictionary-Based Conversion
~~~~~~~~~~~~~~~~~~~~~~~~~~~

We'll tackle these tasks in steps, first finding a way to
convert specific strings into numbers. Python provides a convenient
way to do this conversion using its :class:`dict` class:

.. code-block:: python

    doneness_dict = {'rare': 200,
                     'medium': 350,
                     'well-done': 500}

Getting a value from a dictionary using a key is called
"item-getting". Python item-getting raises a :class:`KeyError`
when it fails:

.. code-block:: python

    >>> doneness_dict['raw']
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
    KeyError: 'raw'

As we'll see, phyles allows for the creation of a converter
dictionary directly in `the schema specification`_.


Type-Based Conversion
~~~~~~~~~~~~~~~~~~~~~

When a YAML config file is parsed by a YAML parser, literals
like ``225`` evaluate to integers. However, a cooking
temperature may often be more useful as a :class:`float`, as when it serves in the denominator of a fraction,
for example. In cases where a YAML literal evaluates to a python
type (*e.g.* :class:`int`, :class:`float`, :class:`str`) that is
different from the type desired, the desired python type can be
used to to perform the conversion:

.. code-block:: python

    >>> float(225)
    225.0

Like the :class:`dict` item-getting, python types provide
error checking, raising exceptions upon failure:

.. code-block:: python

    >>> float([2, 2, 5])
    Traceback (most recent call last):
      File "<stdin>", line 1, in ?
    TypeError: float() argument must be a string or a number

.. code-block:: python

    >>> float("twotwentyfive")
    Traceback (most recent call last):
      File "<stdin>", line 1, in ?
    ValueError: could not convert string to float: twotwentyfive


Conversion by User-Defined Functions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There is nothing particularly special about
:func:`dict.__getitem__` or python types.
They are simply functions (or more preciesly, "callables")
that take a single value as a parameter
and return possibly different values. In cases where they fail,
:func:`dict.__getitem__` and python types raise three
kinds of exceptions:

    =====================  ============================
     Exception              Raised By
    =====================  ============================
     :class:`KeyError`      :class:`dict` item-getting
     :class:`TypeError`     python types
     :class:`ValueError`    python types
    =====================  ============================

Thus, any python function that takes one and only one parameter
and raises either a :class:`KeyError`, :class:`TypeError`,
or :class:`ValueError` upon failure, can serve as a converter.

For example, say we want to release a European version of
our barbecue utility, we could write a function to convert
temperature in °C into temperature in °F:

.. code-block:: python
   :linenos:

    def celsius_to_farenheit(c):
      """
      Returns the temperature in Farenheit given temperature
      in Celsius.

      Args:
        - c: temperature in Celsius

      Returns: temperature in Farenheit (float)

      >>> celsius_to_farenheit(107.222)
      224.9996
      """
      c = float(c)
      if c < -273.15:
        raise ValueError("Impossibly cold (%s °C)!" % c)
      else:
        return (1.8 * c) + 32

Notice that on line 16, :func:`clesius_to_farenheit` raises
a :class:`ValueError` if the temperature supplied to the function
is lower than the thermodynamic legal limit of -273.15 °C.


Choices
~~~~~~~

In some cases, no conversion is required but it is desirable
to check an option value against a list of choices. As shown
below, phyles allows the creation of lists of choices within
the schema specification. If choices are given in this way,
phyles creates a sensible error message if the value for
the option is not within the list of choices.


The Schema Specification
------------------------

A schema in phyles (encapsulated by the :class:`phyles.Schema`
class), contains information to validate a configuration
as well as produce a sample configuration, complete with
documentation in comments. A schema is specified by a
"schema specification".  

The schema specification (often shortened to "spec")
can take several forms, as fully explained in the documentation
to the :func:`phyles.load_schema` function.


Example Schema Specification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For our barbecue example, we'll use a schema specification
written as a `YAML omap`_:

.. code-block:: yaml
    :linenos:

    !!omap
    - dish : 
        - - vegetable kabobs
          - smoked salmon
          - brisket
        - smoked salmon
        - Dish to cook
    - doneness :
        - rare : 200
          medium : 350
          well-done : 500
        - medium
        - How much to cook the dish
    - temperature :
        - celsius to farenheit
        - 105
        - Cooking temperature in °C
        - 105


Required Elements of a Specification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The sequence value for each parameter (*e.g.* ``dish``,
``doneness``, and ``temperature``) in the schema
specification has three required elements (and a fourth
optional element, described below in the section
titled `Optional Default Values`_):

  1. converter as either
      a. a YAML string object of the name of the converter
         function as keyed in the `converters` argument to
         :func:`phyles.Schema.load_schema`
         (as with ``temperature`` above, and discussed in the
         section titled `Dictionary of Converter Functions`_)
      b. a YAML sequence object with a list of acceptable
         choices (as with ``dish`` above)
      c. or a YAML mapping object that maps choices to
         converted values (as with ``doneness`` above)
  2. an example value (for sample config files)
  3. documentation (which can be set to ``null``
     for no documentation; see `YAML null`_)

For ``temperature``, these elements are

  1. converter: ``celsius to farenheit``
  2. example: ``105``
  3. documentation: ``Cooking temperature in °C``


Dictionary of Converter Functions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

One question is how a *name* that evaluates to a
python :class:`str` (*e.g.* ``doneness``) translates
into a converter, which must be a function. As explained
more thoroughly in the discussion of `schema`_ below,
this translation is achieved using a :class:`dict`. For
this barbecue example, we construct this :class:`dict`
in the following way:

.. code-block:: python

    converters = {'celsius to farenheit': celsius_to_farenheit}

We'll see exactly how to use the ``converters`` :class:`dict`
in the `example utility`_.

.. note::

    The :func:`celsius_to_farenheit` function is defined
    in the section titled
    `Conversion by User-Defined Functions`_


Phyles Standard Converters
~~~~~~~~~~~~~~~~~~~~~~~~~~

There are several python types for which it is not
necessary to add entries to the
``converters`` :class:`dict`. The reason is that phyles
provides a set of built-in converters. For example, if a
:class:`float` converter were needed, then the following
would be implicit and **not required** from the programmer:

.. code-block:: python

    converters = {'float': float}  #  <-- NOT necessary!!


These built-in converters provided by phyles are:

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

.. note::

    Except where indicated, these types are encoded
    according to the `YAML types`_ specification
    in a YAML representation of a config.


.. _`schema`: `The Schema`_


List-Optional Converters
~~~~~~~~~~~~~~~~~~~~~~~~

Any converter that is specified as a YAML string object
can be specified as "list-optional" by enclosing the string
in angle brackets (``"<"`` and ``">"``).
For example, the barbecue program
might take one or more temperatures instead of just a
single temperature.

.. code-block:: yaml
    :linenos:

    - temperature :
        - <celsius to farenheit>
        - 105
        - Cooking temperature in °C, or list thereof
        - 105

In such a case, the following would both be valid key-value
pairs for ``temperature``.

.. code-block:: yaml

    temperature : 105

.. code-block:: yaml

    temperature : [105, 120]

Note that a converter specified as list-optional will produce a
list for the key in the configuration, even if the value given in the
config file not a list. In the former example (``temperatreu : 105``),
the config would have the value ``[105]`` for the
key ``"temperature"``.  Thus, the list-optional angle
brackets can be thought of as meaning "make the value into a list
if it is not already".

The capability to specify list-optional converters
does not limit the converter dictionary
from having keys that are enclosed by angle brackets:

.. code-block:: python

     converters = {'<some converter>': some_converter}

Even a converter named in this way could be list-optional
in the schema specification:

.. code-block:: yaml

   - a_parameter :
       - <<some converter>>
       - value
       - A particular paramter or list thereof


Optional Default Values
~~~~~~~~~~~~~~~~~~~~~~~

Additional to the three required elements of a specification
parameter, an optional default value may  be specified as a
fourth element. In the `example schema specification`_ the
default for the ``temperature`` parameter is ``105``.  If a
default value is missing, as in ``dish`` and ``doneness``, then
the parameter is required in the config file.

For example, the following config will fail vailidation
by a schema from the `example schema specification`_ because
the specification requires a value for ``doneness`` (by
virtue of the specification's missing a default value
for ``doneness``):

.. code-block:: yaml

    dish : smoked salmon
    temperature : 107


The Schema
----------

Loading Schema
~~~~~~~~~~~~~~

To validate a config file, the information in `the schema
specification`_ must be converted into a
functional schema, a conversion accomplished by the
:func:`phyles.load_schema` function.

Validating Configs
~~~~~~~~~~~~~~~~~~

Although the :func:`phyles.set_up` function automates
these steps, it is useful to see how a schema is
constructed from a specification and further how the
schema validates a config. Using the running example
(*i.e.* with ``converters`` defined in the section titled
`Dictionary of Converter Functions`_):

.. code-block:: python

    import phyles
    import yaml

    spec = """
           !!omap
           - dish : 
               - - vegetable kabobs
                 - smoked salmon
                 - brisket
               - smoked salmon
               - Dish to cook
           - doneness :
               - rare : 200
                 medium : 350
                 well-done : 500
               - medium
               - How much to cook the dish
           - temperature :
               - celsius to farenheit
               - 105
               - Cooking temperature in °C
               - 105
           """

    cfg = yaml.load("""
                    dish : smoked salmon
                    doneness : medium
                    temperature : 107
                    """)

    schema = phyles.load_schema(spec, converters)
    config = schema.validate_config(cfg)

The behavior of the resulting ``config``, which is an instance
of :class:`phyles.Configuration`, will be discussed in more
detail in the section titled `The Configuration`_.

.. note::

    The ``cfg`` could have just as easily
    been created directly as a :class:`dict`:

    .. code-block:: python

       cfg = {"dish": "smoked salmon",
              "doneness": "medium",
              "temperature": 107}

    However, YAML is used here for consistency
    with earlier parts of this example and to
    emphasize the point that the files
    wherein configurations are stored are YAML files.
    Phyles facilitates using YAML files for configurations.
    For example the opening, reading, and validating
    of which are automated by the
    :func:`phyles.Schema.read_config` function.


Creating a Sample Config
~~~~~~~~~~~~~~~~~~~~~~~~

An instance of :class:`phyles.Schema` is capable of
producing a sample config file using the
:func:`phyles.Schema.sample_config`. For example
given the ``schema`` we just created:


.. code-block:: python

    >>> print schema.sample_config()
    %YAML 1.2
    ---
    <BLANKLINE>
    # Dish to cook
    # One of: vegetable kabobs, smoked salmon, brisket
    dish : smoked salmon
    <BLANKLINE>
    # How much to cook the dish
    # One of: well-done, medium, rare
    doneness : medium
    <BLANKLINE>
    # Cooking temperature in °C
    temperature : 105


The Configuration
-----------------

Instances of :class:`phyles.Configuration` are simply
ordered mappings. By virture of their ``original`` attribute,
:class:`phyles.Configuration` objects also retain memory
of the configuration before conversion (as with the
temperature, which was converted from Celsius to Farenheit):

.. code-block:: python

    >>> for i in config.items():
    ...   print i
    ('dish', 'smoked salmon')
    ('doneness', 350)
    ('temperature', 107.0)
    >>> config['temperature']
    225.0
    >>> config.original['temperature']
    107

Instances of :class:`phyles.Configuration` are useful inside a
utility, potentially being the sole parameter that needs to be
passed to functions. The following example assumes that the
function :func:`cooking_time` is defined as in the section titled
`The Calculation`_:

.. code-block:: python
    :linenos:
 
    difficulties = {'vegetable kabobs': 1,
                    'smoked salmon': 2,
                    'brisket': 3}

    def report_cooking(config):
      t = cooking_time(config['doneness'], config['difficulty'],
                       config['temperature'])
      message = "Cooking time is %5.2f hr." % t
      message = message.center(70)
      config['outlet'](message)

    def main(config):
      ...
      config['difficulty'] = difficulties[config['dish']]
      config['outlet'] = lambda s: sys.stdout.write(s + "\n")
      report_cooking(config)

While bundling arguments within a :class:`Configuration`
may seem a little cumbersome at first, it facilitates the
adding of new configuration-based behaviors deep within a
utility and without the need to modify functions to accommodate additional parameters.

.. note::

    Not all functions of the utility need to take
    a :class:`Configuration` object as an argument. Here
    :func:`cooking_time` still takes three distinct
    arguments, but the "higher-level"
    :func:`report_cooking` function takes config.
    Such design considerations are left to the programmer.

As an example of the utility of a :class:`Configuration` object,
notice that the message width above is hard-coded to 70 in line 9
above. In principle, this width could be user-configurable:

.. code-block:: python

    spec = """
           !!omap
           - dish :
               - - vegetable kabobs
                 - smoked salmon
                 - brisket
               - smoked salmon
               - Dish to cook
           - doneness :
               - rare : 200
                 medium : 350
                 well-done : 500
               - medium
               - How much to cook the dish
           - temperature :
               - celsius to farenheit
               - 105
               - Cooking temperature in °C
               - 105
           - width :
               - int
               - 70
               - width of messages
               - 70
           """

    cfg = yaml.load("""
                    dish : smoked salmon
                    doneness : medium
                    temperature : 107
                    """)

    schema = phyles.load_schema(spec, converters)
    config = schema.validate_config(cfg)
 
Now, the message width needs not be hard-coded, which is
a bane of maintenance:

.. code-block:: python

    def report_cooking(config):
      t = cooking_time(config['doneness'], config['difficulty'],
                       config['temperature'])
      message = "Cooking time is %s hr." % t
      message = message.center(config['width'])
      config['outlet'](message)

This enhanced functionality is essentially transparent
to the user because a default value (70) is provided for
the ``width`` option, rendering ``width`` optional in
the config file.


Example Utility
---------------

We now have all of the pieces we need to make a utility
package, complete with its own library module and
scripts (also called "executable programs", or just
"programs").  As part of the phyles source, an example
called "barbecue" is included in the directory
called "examples".


Running the Example
~~~~~~~~~~~~~~~~~~~

Assuming phyles and its dependencies are installed,
the barbecue example is fully functioning in-place. For
example, try one of the following commands (depending
on your shell) from the ``examples/barbecue`` directory:

  bash-type shell::

      PYTHONPATH=".:${PYTHONPATH}" bin/barbecue-time -t

  csh/tcsh shell::

      env PYTHONPATH=".:${PYTHONPATH}" bin/barbecue-time -t

.. note::

    The part of the command that modifies ``$PYTHONPATH``
    allows for running the ``barbecue-time`` executable
    in-place. Were the barbecue package installed as with
    ``python setup.py install`` this modificaiton of
    ``$PYTHONPATH`` would not be necessary.

These commands should produce the following output:

.. code-block:: yaml

    %YAML 1.2
    ---

    # Dish to cook
    # One of: vegetable kabobs, smoked salmon, brisket
    dish : smoked salmon

    # How much to cook the dish
    # One of: well-done, medium, rare
    doneness : medium

    # Cooking temperature in °C
    temperature : 105

    # width of report
    width : 70

.. note::

    The example barbecue package can even be installed with
    ``python setup.py install``, althought it isn't
    necessary.

Within the ``examples/barbecue/test-data`` directory is also a
config file called ``time-config.yml``. This config file can
be used without installing the barbecue package:

  bash-type shell::

      PYTHONPATH=".:${PYTHONPATH}" \
          bin/barbecue-time -c test-data/time-config.yml

  csh/tcsh shell::

      env PYTHONPATH=".:${PYTHONPATH}" \
         bin/barbecue-time -c test-data/time-config.yml


These commands should produce the following output::

 ======================================================================
                         barbecue-time v.0.1b1                            
 ======================================================================
                       Cooking time is  3.12 hr.                       
   ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  
                        Done with smoked salmon!                       
   ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


It is possible to override configuration settings on the command
line with the ``--override`` (or ``-o``) argument:

  bash-type shell::

      PYTHONPATH=".:${PYTHONPATH}" \
            bin/barbecue-time -c test-data/time-config.yml \
                              -o 'temperature : 120'

  csh/tcsh shell::

      env PYTHONPATH=".:${PYTHONPATH}" \
            bin/barbecue-time -c test-data/time-config.yml \
                              -o 'temperature : 120'

Here, the command line temperature of 120 °C (248 °F) overrides the
temperature in the config (107 °C), reducing the cooking time.
These commands should produce the following output::

 ======================================================================
                         barbecue-time v.0.1b1                            
 ======================================================================
                       Cooking time is  2.82 hr.                       
   ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  
                        Done with smoked salmon!                       
   ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


Before looking deeper into the barbecue example, let's see how
phyles gracefully handles an error that can not be found at the
time when the config is validated because it potentially
depends on the state of the system while the program is running:

   bash-type shell::

       PYTHONPATH=".:${PYTHONPATH}" \
             bin/barbecue-time -c test-data/time-config.yml \
                               -o 'width : 10000'

   csh/tcsh shell::

       env PYTHONPATH=".:${PYTHONPATH}" \
             bin/barbecue-time -c test-data/time-config.yml \
                               -o 'width : 10000'

Here, a message width of 10000 overrides the config file
width of 70. This width is much too large to be displayed on any
normal terminal. The barbecue-time script uses the
:func:`phyles.get_terminal_size` function to catch the problem
and raise an exception that is itself caught, resulting
in a sensible error message being sent to the user with a graceful
exit from the program::

 ======================================================================
                         barbecue-time v.0.1b1                            
 ======================================================================

   ############################# ERROR ##############################  
     Formatting 'width' (10000) bigger than window (78)
   ################################################################## 

Inspection of the contents of the barbecue utility will reveal
how these features of phyles can be used with a small amount of
code.


Barbecue Example Directory Structure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The barbecue example is structured as a typical python package,
serving as a template for most needs:

  - **barbecue/** -- top-level directory for package

    - `CHANGES.txt`
         contains version-by-version information about the
         evolution of the package [#hitch]_

    - `LICENSE.txt`
         contains the text of the license [#hitch]_

    - `MANIFEST.in`
         tells the setup script which extra files
         to include in a distribution [#hitch]_

    - `README.rst`
         contains broad information about the package [#hitch]_
         

    - **barbecue/** -- package directory, holding the library code

        - `__init__.py`
             init module for the package

        - `_barbecue.py`_
             module holding the library code

        - **schema/** -- directory holding schema for configs

             - `barbecue-time.yml`
                  the schema for the `barbecue-time`_ program

    - **bin/** -- a directory holding executable programs

         - `barbecue-time`_
              an example program that calculates cooking times

    - `setup.py`_
         a script for distribution and installation

    - **test-data/** -- directory that holds test-data

         - `time-config.yml`
              a test configuration file for
              the `barbecue-time`_ program

Let's look at some of the key files in the hierarchy and examine
salient features of each, starting first with the
`barbecue-time`_ program because it shows most directly how to
use phyles.

barbecue-time
~~~~~~~~~~~~~

.. code-block:: python
   :linenos:

    import sys
    import phyles
    import barbecue

    __program__ = "barbecue-time"
    __version__ = "0.1b1"

    def output_message(message, config):
      console_width = phyles.get_terminal_size()[0]
      if config['width'] > console_width:
        tplt = "Formatting 'width' (%s) bigger than window (%s)"
        message = tplt % (config['width'], console_width)
        raise barbecue.FormatError(message)

      message = message.center(config['width'])
      config['outlet'](message)

    def report_cooking(config):
      t = barbecue.cooking_time(config['doneness'],
                                config['difficulty'],
                                config['temperature'])

      message = "Cooking time is %5.2f hr." % t
      output_message(message, config)

    def finish_up(config):
      hline = "~" * (config['width'] - 4)
      output_message(hline, config)
      message = "Done with %s!" % config['dish']
      output_message(message, config)
      output_message(hline, config)

    def main(config):
      config['difficulty'] = barbecue.difficulties[config['dish']]
      config['outlet'] = lambda s: sys.stdout.write(s + "\n")
      report_cooking(config)
      finish_up(config)

    if __name__ == "__main__":
      spec = phyles.package_spec(phyles.Undefined, "barbecue",
                                 "schema", "barbecue-time.yml")
      converters = {'celsius to farenheit':
                         barbecue.celsius_to_farenheit}
      setup = phyles.set_up(__program__, __version__, spec, converters)
      phyles.run_main(main, setup['config'],
                      catchall=barbecue.BarbecueError)


In terms of interacting with phyles, the most critical part of
`barbecue-time`_ is in lines 40-46: 

  - Lines 40-41
       The :func:`phyles.package_spec` function is used to
       retrieve the schema from the package.
  - Lines 42-43
       The converters :class:`dict` is created as in the
       section title `Dictionary of Converter Functions`_.
  - Line 44
       The :func:`phyles.set_up` function is used to parse
       command line arguments, load the schema from the spec,
       validate the config, and override any config setting
       from the command line option ``--override`` (``-o``).
  - Lines 45-46
       The :func:`phyles.run_main` function is used to run
       the main function inside a try-except block that
       catches any exceptions assigned by the ``catchall``
       keyword argument, and exits gracefully if such
       exceptions arise.

.. note::

    These few lines (40-46), along with specifying a schema,
    are all that is truely needed to interface with phyles
    and take advantage of the mose useful parts of its
    functionality.

Like any good program, `barbecue-time`_ has a :func:`main` function:

  - Lines 34-35
       The ``config`` is used as a global state, defining
       new items called ``'difficulty'`` and ``'outlet'``,
       that will be used in other parts of the program.
       Such use of a :class:`phyles.Configuration` object
       is convenient, but left to the discretion of the
       programmer.

Using a :class:`phyles.Configuration` object allows for
abstraction of functionality that depends on the configuration.

  - Line 9
       The :func:`phyles.get_terminal_size` function is
       used to determine the width of the console.
  - Lines 10-13
       The message width from the config file (keyed by
       ``'width'``) is checked against the console width.
       If the message width is to large, then a
       :class:`FormatError` exception is raised. As we'll
       see upon inspection of the file `_barbecue.py`_,
       :class:`FormatError` is a subclass of
       :class:`BarbecueError`, which is the catchall exception
       for graceful exit (see line 45). 
  - Lines 26-31
       The :func:`finish_up` function further demonstrates
       the utility of :class:`Configuration` objects and the
       abstraction they allow. Note that the
       :func:`output_message` function does not care how the
       message is displayed--except that it is unfortunately
       tied to the console width. Even this dependencey can
       be remedied by further abstraction. For example, ``config``
       could have the item:

       .. code-block:: python

          config['canv_width'] = lambda: phyles.get_terminal_size()[0]

       And then :func:`output_message` could be changed
       accordingly:

       .. code-block:: python

          def output_message(message, config):
            max_width = config['canv_width']()
            if config['width'] > max_width:
              tplt = "Formatting 'width' (%s) bigger than window (%s)"
              message = tplt % (config['width'], max_width)
              raise barbecue.FormatError(message)

            message = message.center(config['width'])
            config['outlet'](message)

       Now, since ``config['canv_width']`` can
       be any function (or "callable"), the backend to which the
       message is sent can be anything, including a console
       or gui element like a :class:`Tkinter.Label`.


_barbecue.py
~~~~~~~~~~~~

The `_barbecue.py`_ file holds the main library code for
the barbecue package.

.. code-block:: python
   :linenos:

    #! /usr/bin/env python
    # -*- coding: utf-8 -*-

    difficulties = {'vegetable kabobs': 1,
                    'smoked salmon': 2,
                    'brisket': 3}

    class BarbecueError(Exception):
      pass

    class FormatError(BarbecueError):
      pass

    class TemperatureError(BarbecueError):
      pass

    def cooking_time(doneness, difficulty, T):
        """
        Return the cooking time given the desired doneness
        cooking, the difficulty of cooking, and the temperature.

        Args:
          - doneness: desired doneness (hr•°F/dc)
          - difficulty: difficulty of cooking for the dish (dc)
          - T: cooking temperature (°F)

        Returns: cooking time in hours (float)

        Raises: ``ValueError`` if the `temperature` is <= 120 °F

        >>> round(cooking_time(350, 2, 225), 2)
        3.11
        """
        if T <= 120:
          msg = "%s °F is too cold to cook!" % T
          raise TemperatureError(msg)
        return float(doneness * difficulty) / T

    def celsius_to_farenheit(c):
      """
      Returns the temperature in Farenheit given temperature
      in Celsius.

      Args:
        - c: temperature in Celsius

      Returns: temperature in Farenheit (float)

      >>> celsius_to_farenheit(107.222)
      224.9996
      """
      c = float(c)
      if c < -273.15:
        raise ValueError("Impossibly cold (%s °C)!" % c)
      else:
        return (1.8 * c) + 32

Most of `_barbecue.py`_ documents its functionality. However,
it does have some key parts:

  - Line 2
      This line designates the optional encoding for the file (see
      http://www.python.org/dev/peps/pep-0263/). The UTF-8
      encoding allows for display of the ubiquitous units
      "°C" and "°F" in the docstrings and error messages.
  - Lines 6-8
      Some data is kept in the module, namely the conversions
      from dish to cooking difficulty. If larger amounts of
      data are needed, then it is better to include these
      as so-called "package data" and use the
      :func:`pkg_resources.resource_string` function from the
      `distribute`_ package or, failing that, the
      :func:`phyles.get_data_path` function, which tries to
      find package data with every trick in the book.

      .. note::

          With proper utilization of `python eggs`_, a
          programmer should find that use of the
          :func:`pkg_resources.resource_string` function
          is failsafe.

  - Lines 10-17
      As seen in the `barbecue-time`_ file (lines 45-46), the
      :class:`BarbecueError` is used as a catchall for anticipated
      errors, allowing the program to exit gracefully if
      any are raised while executing the :func:`main` function.

      Created here are the :class:`BarbecueError` and a couple of
      decendants, corresponding to problems with formatting
      and nonsensical cooking temperatures (lines 34-36).
      Since these exceptions are :class:`BarbecueError`
      or inherit from it, then they fall under the catchall
      and trigger graceful exit.

      .note::

        The `catchall` can also be a tuple of exceptions.
        See :func:`phyles.run_main`.


MANIFEST.in
~~~~~~~~~~~

To ensure that files get included in source distributions
(i.e. ``python setup.py sdist``), it is important to specify
them in `MANIFEST.in`_.

.. code-block:: console
   :linenos:

   include *.txt
   include *.rst
   recursive-include barbecue *.yml

- Line 3 means to include all files matching the pattern ``*.yml``
  in the directory ``barbecue`` and all directories therein,
  recursively. To ensure these files are installed from the
  source distribution, they should also be specified in `setup.py`_.


setup.py
~~~~~~~~

The `setup.py`_ script directs the distribution and installation
of python packages. See
http://guide.python-distribute.org/creation.html for a complete
discussion.

Below is a partial (acutally, almost complete) listing of
`setup.py`_ mainly to (1) show the minimal required keyword
arguments and (2) show how to use the following keyword
arguments of the :func:`setup` function:

   - ``packages``
   - ``include_package_data``
   - ``package_data``
   - ``scripts``

.. code-block:: python
   :linenos:

    import os
    import glob

    from setuptools import setup, find_packages

    setup(name='barbecue',
          version='0.1b1',
          author='James C. Stroud',
          author_email='jstroud@mbi.ucla.edu',
          description='Utilities for cooking barbecue.',
          url='http://phyles.bravais.net/barbecue',
          classifiers =[
                  'Programming Language :: Python :: 2',
             ],
          install_requires=["distribute", "phyles >= 0.2.0"],
          license='LICENSE.txt',
          long_description=open('README.rst').read(),
          packages=find_packages(),
          include_package_data=True,
          package_data={'': [os.path.join('*', '*.yml')]},
          scripts=glob.glob(os.path.join('bin', '*')))

- ``packages`` -- line 18
      It is notable that the keyword argument ``package_dir``
      is not required, nor is it necessary to specify the
      package manually names because they are found automatically
      by :func:`distribute.find_packages` imported on
      line 4. Here, ``find_packages()`` evaluates to
      ``['barbecue']``.

- ``include_package_data`` -- line 19
      This keyword argument ensures that the files found
      by the ``package_data`` keyword argument will be included
      upon installation (not just packaging for distribution).

- ``package_data`` -- line 20
      The empty string (``''``) means to include files that
      match the corresponding patterns (``['*/*.yml']`` for
      unix-like systems) for **all** packages listed for the
      ``packages`` keyword argument. Here, these packages are
      found automatically.  In this barbecue example
      ``{'': [os.path.join('*', '*.yml')]}`` matches
      ``barbecue/schema/barbecue-time.yml``.

      Thus, the pattern ``os.path.join('*', '*.yml')`` means to
      match every file ending with ``.yml`` in every sub-directory
      of the **package** directory (containing the ``__init__.py``
      file; here ``barbecue``). In other words, the pattern is
      matched as if it were evaluated from the package directory
      that contains the ``__init__.py`` file.

      A simple way to check what the pattern will match is
      to change to the package directory and then
      execute the ``ls`` command with the pattern, as in
      the final command here:

      .. code-block:: shell-session

           [command@prompt]% ls barbecue/
           __init__.py  _barbecue.py  schema
           [command@prompt]% cd barbecue/
           [command@prompt]% ls schema/
           barbecue-time.yml
           [command@prompt]% ls */*.yml
           schema/barbecue-time.yml

- ``scripts`` -- line 21
      The value to ``scripts`` says to include all files
      (``'*'``) in the ``bin`` directory, using the 
      :func:`glob.glob` function from the python standard
      library, imported on line 2.  Here,
      ``glob.glob(os.path.join('bin', '*'))`` evaluates to
      ``[barbecue-time]``.


Phyles and Entry Points
-----------------------

Compared to ``scripts``, a more robust way to implement programs
from a python package is to use `entry points`_, which are
perfectly compatible with phyles:

   - somewhere in **setup.py**

       .. code-block:: python

          # somewhere in call to setuptools.setup()
          entry_points = {
             'console_scripts' : [
                'some_program = my_package:_some_program']}

   - somewhere in **__init__.py**

       .. code-block:: python

          from _my_module import _some_program

   - somewhere in **_my_module.py**

       .. code-block:: python

          class AnticipatedError(Exception):
            pass

          def some_function(config):
            # do stuff with config,
            # interact with user, produce output,
            # raise AnticipatedError when appropriate, etc.
            ...

          def _some_program():
            spec = """
                   !!omap
                   - param1 : [str, example 1, parameter 1]
                   - param2 : [int, 42, parameter 2]
                   """
            setup = phyles.set_up('some_program', '0.1.0' spec)
            phyles.run_main(some_function, setup['config'],
                                     catchall=AnticipatedError)

       .. note::

            As in the barbecue example, the specification
            (``spec``) is probably better included as a
            separate file in the package data.

.. rubric:: Footnotes

.. [#alg] The rule of algebra used here can be stated like this:
          if a quantity is on top of the fraction on one side of
          the equals sign, then it can be moved to the bottom of the
          fraction on the other side of the equals sign,
          and vice versa.
.. [#hitch] http://guide.python-distribute.org/creation.html


.. _`YAML omap`: http://yaml.org/type/omap.html
.. _`YAML null`: http://yaml.org/type/null.html
.. _`YAML dict`: http://yaml.org/type/dict.html
.. _`YAML int`: http://yaml.org/type/int.html
.. _`YAML timestamp`: http://yaml.org/type/timestamp.html
.. _`YAML types`: http://yaml.org/type/
.. _`distribute`: http://pypi.python.org/pypi/distribute
.. _`python eggs`: http://goo.gl/9dQEK
.. _`Sphinx`: http://sphinx-doc.org/
.. _`reStructuredText`: http://docutils.sourceforge.net/rst.html
.. _`entry points`: http://goo.gl/Ss8dr
