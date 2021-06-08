# This file is part of ts_envsensors.
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
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Implementation of SEL temperature instrument.

Read and perform protocol conversion for Straight Engineering Limited (SEL)
temperature measurement instrument.
SEL temperature instruments output serial data in lines terminated by '\r\n'.
There are multiple SEL temperature instruments with different numbers of
channels. The number of channels must be specified at instantiation.
The format of a 4-channel instruments output line is:

    'C00=snnn.nnnn,C01=snnn.nnnn,C02=snnn.nnnn,C03=snnn.nnnn\r\n'

where:

    'C00='      4-character preamble with Celcius ('C') and
                two digit channel number.

    'snnn.nnnn' 9-character decimal value with negative sign or positive value
                (s = '-' or '0..9') and decimal point in the fifth position.

    ','         Single character delimiter.

    '\r\n'      2-character terminator.
"""

__all__ = ["SelTemperature", "DELIMITER", "TERMINATOR"]

import asyncio
import logging
import math
import time
from typing import Any, Dict, List, Union

from .serial_reader import SerialReader

# Instrument serial parameters ....
BAUDRATE: int = 19200
"""BAUD for SEL temperature instrument communications ('int').
"""

READ_TIMEOUT: float = 1.5
"""Serial read timeout for SEL temperature instrument communications ('float').

The read timeout is set to allow a guaranteed timeout for the recurring
instrument channel serial reads. The number of channels varies between
SEL instruments (4, 5, 8 etc.). The default read timeout is chosen to
comfortably allow for up to eight channels at 19200 BAUD.
"""

# SEL Temperature Instrument serial data string ....
PREAMBLE_SIZE: int = 4
"""Serial data channel preamble size.
"""

VALUE_SIZE: int = 9
"""Serial data temperature value size.
"""

DELIMITER: str = ","
"""Serial data channel delimiter.
"""

TERMINATOR: str = "\r\n"
"""Serial data line terminator.
"""

DEFAULT_VAL: float = math.nan
"""Default value for unread or errored temperature channels.
"""


class SelTemperature(SerialReader):
    """SEL temperature instrument protocol converter object.

    Parameters
    ----------
    name : `str`
        Name of the SelTemperature instance.
    channels : `int`
        Number of temperature instrument channels.
    uart_device : `uart`
        Serial port instance.

    Raises
    ------
    IndexError if attempted multiple use of instance name.
    IndexError if attempted multiple use of serial device instance.
    """

    def __init__(self, name: str, uart_device, channels: int, log=None):
        super().__init__(name, uart_device, channels, log)
        if log is None:
            self.log = logging.getLogger(type(self).__name__)
        else:
            self.log = log.getChild(type(self).__name__)

        self.name: str = name
        self._channels: int = channels
        self.comport = uart_device

        self.temperature: List[float] = []
        self.output: List[Union[str, float]] = []

        self._preamble_str: List[str] = []
        self._old_preamble_str: List[str] = []
        self._tmp_temperature: List[float] = []
        for i in range(self._channels):
            self._tmp_temperature.append(DEFAULT_VAL)
            self.temperature.append(DEFAULT_VAL)
            self._preamble_str.append(f"C{i:02}=")
            self._old_preamble_str.append(f"C{i+1:02}=")

        self._read_line_size: int = (
            self._channels * (PREAMBLE_SIZE + VALUE_SIZE + len(DELIMITER))
            - (len(DELIMITER))
            + (len(TERMINATOR))
        )

        self.log.debug(
            f"SelTemperature:{name}: First instantiation "
            f"using serial device {uart_device.name!r}."
        )

    async def start(self):
        """Open the comport and set the connection parameters."""
        await self.comport.open()
        self.comport.line_size = self._read_line_size
        self.comport.terminator = TERMINATOR
        self.comport.baudrate = BAUDRATE
        self.comport.read_timeout = READ_TIMEOUT

    async def stop(self):
        """Close the comport."""
        await self.comport.close()

    async def _message(self, text: Any) -> None:
        # Print a message prefaced with the SEL_TEMPERATURE object info.
        self.log.debug(f"SelTemperature:{self.name}: {text}")

    def _test_val(self, preamble, sensor_str):
        """Test temperature channel data string.

        Parameters
        ----------
        preamble : 'str'
            Preamble string for channel data (eg."C01=").
        sensor_str : 'str'
            Sensor channel data string (eg."C01=0001.4500")

        Returns
        -------
        Status : 'bool'
            Return is True if sensor string is valid, False if not.
        """
        if sensor_str[0:PREAMBLE_SIZE] == preamble:
            try:
                float(
                    sensor_str[
                        PREAMBLE_SIZE : PREAMBLE_SIZE + VALUE_SIZE + len(DELIMITER) - 1
                    ]
                )
                return True
            except ValueError as e:
                self.log.exception(e)
                return False
                pass

    async def read(self) -> None:
        """Read temperature instrument.

        Read SEL instrument, test data and populate temperature channel data.

        The SEL instrument has a fixed line size (Depending upon number
        of channels). The read is invalid if the read line size is incorrect.
        If line size error is found, temperature data is populated with default
        value ('Nan').
        If sensor data (preamble and value) does not meet the instrument
        protocol, the read is invalidated.
        If protocol error is found, temperature data is populated with default
        value ('Nan').
        The timestamp is updated following conversion of the read line.
        The line error flag is updated with True if any error found and False
        if no error.
        """
        for i in range(self._channels):
            self._tmp_temperature[i] = DEFAULT_VAL
        err: str = ""
        ser_line: str = ""
        line: str = ""
        await self._message("Reading line from comport.")

        # Set up loop variable for async calls
        loop = asyncio.get_event_loop()

        device_name, err, ser_line = await loop.run_in_executor(
            None, self.comport.readline
        )
        await self._message("Done.")
        if err == "OK":
            if (
                ser_line[-len(TERMINATOR) :] == TERMINATOR
                and len(ser_line) == self._read_line_size
            ):
                line = ser_line[: -len(TERMINATOR)]
                temps = line.split(",", self._channels - 1)
                for i in range(self._channels):
                    if self._test_val(
                        self._preamble_str[i], temps[i]
                    ) or self._test_val(self._old_preamble_str[i], temps[i]):
                        try:
                            self._tmp_temperature[i] = float(temps[i][PREAMBLE_SIZE:])
                        except ValueError:
                            err = f"Temperature data error. Could not convert value(s) to float: {ser_line}"
                            await self._message(
                                f"Failed to convert temperature channel value to float: {ser_line}"
                            )
                    else:
                        err = f"Malformed response. Channel preamble or channel data incorrect: {ser_line}"
                    self.temperature[i] = self._tmp_temperature[i]
            else:
                err = (
                    f"Malformed response. Terminator or line size incorrect: {ser_line}"
                )

        self.output = []
        self.output.append(device_name)
        self.output.append(time.time())
        self.output.append(err)
        for i in range(self._channels):
            self.output.append(self.temperature[i])
