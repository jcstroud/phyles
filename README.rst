========
 phyles
========

Background
----------

Phyles is a set of somewhat eclectic functions that makes the
implementation of utilities (little programs that can be controlled
by config files) easier. It started as a mass of boilerplate that I
would copy into almost every utility I wrote.  I finally decided to
consolidate this code into a package and add some schema-based
validation of config files and to document it fully.

Features
--------

Phyles provides support for `YAML`_-based
config files as well as a means for validating the config files.
Phyles also provides several facilities for making utilities
more user friendly, including automatically generated banners,
automatically documented configuration templates, and graceful
recovery from configuration errors.

Home Page & Repository
----------------------

The phyles home page is http://phyles.bravais.net, and the source
code is maintained at github: https://github.com/jcstroud/phyles\.

Example
-------

About 90% of the convenience that phyles offers can
be summarized by a few lines of code. From the example
utility in the tutorial (http://pythonhosted.org/phyles):

.. code-block:: python

  1|  spec = phyles.package_spec(phyles.Undefined, "barbecue",
   |                             "schema", "barbecue-time.yml")
  2|  converters = {'celsius to farenheit':
   |                barbecue.celsius_to_farenheit}
  3|  setup = phyles.set_up(__program__, __version__,
   |                                    spec, converters)
  4|  phyles.run_main(main, setup['config'],
   |                   catchall=barbecue.BarbecueError)

These few lines find a schema specification from the package
contents (line 1), parses command line arguments (line 3),
validates a config file (lines 2 & 3), overrides configuration
settings therein (line 3), and runs the main function of the utility
in a try-except block that ensures graceful exit in the event that
an anticipated exception is raised (line 4).

Schema are specified in `YAML`_, terse, and hopefully intuitive.
Following is the example from the tutorial:

.. code-block:: yaml

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
         - width of report
         - 70

Phyles will automatically generate a documented sample
config files for users if they run the utility with
the ``--template`` (or ``-t``) command line option. In the
tutorial, calling the example script (``barbecue-time``) with::

      barbecue_time -t

produces the following output, which is valid for the above
schema:

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


As one final example, another valid config file for this schema is:

.. code-block:: yaml

      dish : smoked salmon
      doneness : medium
      temperature : 107
      width : 70

.. _`YAML`: http://www.yaml.org
