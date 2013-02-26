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
