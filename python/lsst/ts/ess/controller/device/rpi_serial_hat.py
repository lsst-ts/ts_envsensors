# This file is part of ts_ess_controller.
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

__all__ = ["RpiSerialHat"]

import asyncio
import concurrent
import logging
from io import BytesIO
from typing import Callable

import serial

from lsst.ts.ess import common


class RpiSerialHat(common.device.BaseDevice):
    """Raspberry Pi serial device connected to the hat.

    Parameters
    ----------
    name : `str`
        The name of the device.
    device_id : `str`
        The hardware device ID to connect to. This needs to be a physical ID
        (e.g. /dev/ttyUSB0).
    sensor : `BaseSensor`
        The sensor that produces the telemetry.
    baud_rate : `int`
        The baud rate of the sensor.
    callback_func : `Callable`
        Callback function to receive the telemetry.
    log : `logging.Logger`
        The logger to create a child logger for.
    """

    def __init__(
        self,
        name: str,
        device_id: str,
        sensor: common.sensor.BaseSensor,
        baud_rate: int,
        callback_func: Callable,
        log: logging.Logger,
    ) -> None:
        super().__init__(
            name=name,
            device_id=device_id,
            sensor=sensor,
            baud_rate=baud_rate,
            callback_func=callback_func,
            log=log,
        )
        try:
            self.ser = serial.Serial(port=device_id, baudrate=self.baud_rate)
            self.log.debug(f"Port: {self.ser.port}")
        except serial.SerialException as e:
            self.log.exception(e)
            # Unrecoverable error, so propagate error
            raise e

    async def basic_open(self) -> None:
        """Open and configure serial port.
        Open the serial communications port and set BAUD.

        Raises
        ------
        IOError if serial communications port fails to open.
        """
        if not self.ser.is_open:
            try:
                self.ser.open()
                self.log.info("Serial port opened.")
            except serial.SerialException as e:
                self.log.exception("Serial port open failed.")
                raise e
        else:
            self.log.info("Port already open!")

    async def readline(self) -> str:
        """Read a line of telemetry from the device.

        Returns
        -------
        line : `str`
            Line read from the device. Includes terminator string if there is
            one. May be returned empty if nothing was received or partial if
            the readline was started during device reception.
        """
        buffer = BytesIO()
        terminator = self.sensor.terminator.encode(self.sensor.charset)
        # get running loop to run blocking tasks
        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            while not buffer.getvalue().endswith(terminator):
                buffer.write(await loop.run_in_executor(pool, self.ser.read, 1))
        return buffer.getvalue().decode(self.sensor.charset)

    async def basic_close(self) -> None:
        """Close the Sensor Device.

        Raises
        ------
        IOError if virtual communications port fails to close.
        """
        if self.ser.is_open:
            self.ser.close()
            self.log.exception("Serial port closed.")
        else:
            self.log.info("Serial port already closed.")
