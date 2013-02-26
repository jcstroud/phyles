Introduction to Phyles
======================

About 90% of the convenience that phyles offers can
be summarized by a few lines of code. From the example
utility in the tutorial:

.. code-block:: python
   :linenos:

    spec = phyles.package_spec(phyles.Undefined, "barbecue",
                               "schema", "barbecue-time.yml")
    converters = {'celsius to farenheit':
                  barbecue.celsius_to_farenheit}
    setup = phyles.set_up(__program__, __version__,
                                      spec, converters)
    phyles.run_main(main, setup['config'],
                    catchall=barbecue.BarbecueError)

These few lines find a schema specification from the package
contents (line 1), parses command line arguments (line 5),
validates a config file (lines 3 & 5), overrides configuration
settings therein (line 5), and runs the main function of the utility
in a try-except block that ensures graceful exit in the event that
an anticipated exception is raised (line 5).

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
