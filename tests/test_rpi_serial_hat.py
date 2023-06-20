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

from unittest import mock

from lsst.ts.ess import common, controller


class RpiSerialHatTestCase(controller.BaseRealSensorMockTestCase):
    @mock.patch(
        "lsst.ts.ess.controller.device.rpi_serial_hat.AioSerial", new=mock.AsyncMock
    )
    async def test_rpi_serial_hat(self) -> None:
        self.return_as_plain_text = False
        name = "MockedRpiSerialHat"
        self.num_channels = 2
        self.sensor.num_channels = self.num_channels
        device = controller.device.RpiSerialHat(
            name=name,
            device_id="/dev/ttyAMA1",
            sensor=self.sensor,
            baud_rate=19200,
            callback_func=self._callback,
            log=self.log,
        )

        type(device.ser).is_open = mock.PropertyMock(return_value=False)
        type(device.ser).open = mock.PropertyMock()
        await device.open()

        type(device.ser).read = self.read
        type(device.ser).read_until_async = self.read_until_async
        await self.wait_for_read_event()
        assert self._reply is not None

        await self.wait_for_read_event()
        assert self._reply is not None
        reply_to_check = self._reply[common.Key.TELEMETRY]
        self.mtt.check_temperature_reply(
            reply=reply_to_check, name=name, num_channels=self.num_channels
        )

        type(device.ser).is_open = mock.PropertyMock(return_value=True)
        type(device.ser).close = mock.PropertyMock()
        await device.close()
