.. phyles documentation master file, created by
   sphinx-quickstart on Thu Jun 21 14:06:57 2012.

Phyles Documentation
====================

Phyles is a set of somewhat eclectic functions that makes the
implementation of utilities (little programs that can be controlled
by config files) easier. It started as a mass of boilerplate that I
would copy into almost every utility I wrote.  I finally decided to
consolidate this code into a package and add some schema-based
validation of config files and to document it fully.

Phyles provides support for `YAML`_-based
config files as well as a means for validating the config files.
Phyles also provides several facilities for making utilities
more user friendly, including automatically generated banners,
automatically documented configuration templates, and graceful
recovery from configuration errors.

The accompanying tutorial shows how phyles assists in
turning one-off python scripts into robust packages worthy of
distribution, or at least worthy of a permanent place in one's
work-flow.

Phyles can be obtained at https://pypi.python.org/pypi/phyles/\.

.. _`YAML`: http://www.yaml.org

.. toctree::
   :maxdepth: 3
   :numbered:

   intro
   tutorial
   phyles-api


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
