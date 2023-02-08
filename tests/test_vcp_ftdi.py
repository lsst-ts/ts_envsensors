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

import logging
from unittest import mock

from lsst.ts.ess import common, controller

from .base_real_sensor_mock_test_case import BaseRealSensorMockTestCase

logging.basicConfig(
    format="%(asctime)s:%(levelname)s:%(name)s:%(message)s", level=logging.DEBUG
)


class VcpFtdiTestCase(BaseRealSensorMockTestCase):
    @mock.patch("lsst.ts.ess.controller.device.vcp_ftdi.Device")
    async def test_vcp_ftdi(self, mock_ftdi_device: mock.AsyncMock) -> None:
        name = "MockedVcpFtdi"
        self.num_channels = 2
        self.sensor.num_channels = self.num_channels
        device = controller.device.VcpFtdi(
            name=name,
            device_id="ABCDEF",
            sensor=self.sensor,
            baud_rate=19200,
            callback_func=self._callback,
            log=self.log,
        )

        type(device.vcp).closed = mock.PropertyMock(return_value=False)
        await device.open()

        type(device.vcp).read = self.read
        reply = await self.read_next()
        assert reply is not None
        reply_to_check = reply[common.Key.TELEMETRY]
        self.mtt.check_temperature_reply(
            reply=reply_to_check, name=name, num_channels=self.num_channels
        )

        reply = await self.read_next()
        assert reply is not None
        reply_to_check = reply[common.Key.TELEMETRY]
        self.mtt.check_temperature_reply(
            reply=reply_to_check, name=name, num_channels=self.num_channels
        )

        type(device.vcp).closed = mock.PropertyMock(return_value=True)
        await device.close()
