# This file is part of ts_ess_sensors.
#
# Developed for the Vera C. Rubin Observatory Telescope and Site Systems.
# This product includes software developed by the LSST Project
# (https://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

__all__ = ["MockTemperatureSensor", "MIN_TEMP", "MAX_TEMP"]

import asyncio
import logging
import random
import time

import numpy as np

from lsst.ts.ess.sensors.sel_temperature_reader import DELIMITER

# Minimum and maximum temperatures (deg_C) for creating random sensor data.
MIN_TEMP = 18.0
MAX_TEMP = 30.0


class MockTemperatureSensor:
    """Mock Temperature Sensor."""

    def __init__(
        self, name: str, channels: int, count_offset=0, nan_channel=None, log=None
    ):
        self.name = name
        self.channels = channels
        self.count_offset = count_offset
        self.nan_channel = nan_channel

        # Device parameters
        self.line_size = None
        self.terminator = None
        self.baudrate = None
        self.read_timeout = None

        if log is None:
            self.log = logging.getLogger(type(self).__name__)
        else:
            self.log = log.getChild(type(self).__name__)

        self.log.info("__init__")

    async def open(self) -> None:
        pass

    async def close(self) -> None:
        pass

    def format_temperature(self, i):
        """Creates a formatted string representing a temperature for the given
        channel.

        Parameters
        ----------
        i: `int`
            The temperature channel.

        Returns
        -------
        s: `str`
            A string represensting a temperature.

        """
        temp = random.uniform(MIN_TEMP, MAX_TEMP)
        s = f"C{i + self.count_offset:02d}={temp:09.4f}"
        if i == self.nan_channel:
            s = f"C{i + self.count_offset:02d}=9999.9990"
        if i == self.channels - 1:
            s += self.terminator
        else:
            s += DELIMITER
        return s

    def readline(self):
        """Creates a temperature readout response. The name of this function
        does not reflect what it does. But this is the name of the functions
        in the code that reads the real sensor data so I need to stick with it.

        Returns
        -------
        name, error, resp : `tuple`
        name : `str`
            The name of the device.
        error : `str`
            Error string.
            'OK' = No error
            'Non-ASCII data in response.'
            'Timed out with incomplete response.'
        resp : `str`
            Response read from the mock device.
            Includes terminator string.

        """
        self.log.info("read")
        time.sleep(1)
        err: str = "OK"
        resp = ""
        for i in range(0, self.channels):
            resp += self.format_temperature(i)
        return self.name, err, resp
