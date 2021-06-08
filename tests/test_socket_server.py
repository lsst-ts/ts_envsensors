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

import asyncio
import json
import logging
import unittest

from lsst.ts.envsensors import SocketServer, ResponseCode, Command, DeviceType, Key
from lsst.ts.envsensors.mock.mock_temperature_sensor import MockTemperatureSensor
from lsst.ts import tcpip

logging.basicConfig(
    format="%(asctime)s:%(levelname)s:%(name)s:%(message)s", level=logging.DEBUG
)

TIMEOUT = 5
"""Standard timeout in seconds."""


class SocketServerTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.ctrl = None
        self.writer = None
        self.mock_ctrl = None
        self.data = None
        self.srv = SocketServer(host="0.0.0.0", port=0, simulation_mode=1)

        self.log = logging.getLogger(type(self).__name__)

        await self.srv.start_task
        self.assertTrue(self.srv.server.is_serving())
        self.reader, self.writer = await asyncio.open_connection(
            host=tcpip.LOCAL_HOST, port=self.srv.port
        )

    async def asyncTearDown(self):
        await self.srv.disconnect()
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
        await self.srv.exit()

    async def read(self):
        """Utility function to read a string from the reader and unmarshal it

        Returns
        -------
        data : `dict`
            A dictionary with objects representing the string read.
        """
        read_bytes = await asyncio.wait_for(
            self.reader.readuntil(tcpip.TERMINATOR), timeout=TIMEOUT
        )
        data = json.loads(read_bytes.decode())
        return data

    async def write(self, **data):
        """Write the data appended with a TERMINATOR string.

        Parameters
        ----------
        data:
            The data to write.
        """
        st = json.dumps({**data})
        self.writer.write(st.encode() + tcpip.TERMINATOR)
        await self.writer.drain()

    async def test_disconnect(self):
        self.assertTrue(self.srv.connected)
        await self.write(command=Command.DISCONNECT, parameters={})
        # Give time to the socket server to clean up internal state and exit.
        await asyncio.sleep(0.5)
        self.assertFalse(self.srv.connected)

    async def test_exit(self):
        self.assertTrue(self.srv.connected)
        await self.write(command=Command.EXIT, parameters={})
        # Give time to the socket server to clean up internal state and exit.
        await asyncio.sleep(0.5)
        self.assertFalse(self.srv.connected)

    async def test_full_command_sequence(self):
        name = "Test1"
        channels = 1
        configuration = {
            Key.DEVICES: [
                {
                    Key.NAME: name,
                    Key.CHANNELS: channels,
                    Key.TYPE: DeviceType.FTDI,
                    Key.FTDI_ID: "ABC",
                }
            ]
        }
        await self.write(
            command=Command.CONFIGURE, parameters={Key.CONFIGURATION: configuration}
        )
        self.data = await self.read()
        self.assertEqual(ResponseCode.OK, self.data[Key.RESPONSE])
        await self.write(command=Command.START, parameters={})
        self.data = await self.read()
        self.assertEqual(ResponseCode.OK, self.data[Key.RESPONSE])
        self.data = await self.read()
        telemetry = self.data[Key.TELEMETRY]
        self.assertEqual(telemetry[0], name)
        self.assertEqual(telemetry[2], ResponseCode.OK.name)
        assert (
            MockTemperatureSensor.MIN_TEMP
            <= telemetry[3]
            <= MockTemperatureSensor.MAX_TEMP
        )

        await self.write(command=Command.STOP, parameters={})
        self.data = await self.read()
        self.assertEqual(ResponseCode.OK, self.data[Key.RESPONSE])
        await self.write(command=Command.DISCONNECT, parameters={})
        await self.write(command=Command.EXIT, parameters={})
