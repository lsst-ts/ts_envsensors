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

__all__ = ["CommandHandler"]

import asyncio
import logging
import platform
import time
from typing import Any, Callable, Dict, List, Optional, Union

from .command_error import CommandError
from .constants import Command, Key, DeviceType, SensorType
from .device import BaseDevice
from .response_code import ResponseCode
from .sensor import BaseSensor, TemperatureSensor, WindSensor


class CommandHandler:
    """Handle incoming commands and send replies. Apply configuration and read
    sensor data.

    Parameters
    ----------
    callback: `Callable`
        The callback coroutine handling the sensor telemetry. This can be a
        coroutine that sends the data via a socket connection or a coroutine in
        a test class to verify that the command has been handled correctly.
    simulation_mode: `int`
        Indicating if a simulation mode (> 0) or not (0) is active.

    The commands that can be handled are:

        configure: Load the configuration that is passed on with the command
        and connect to the devices specified in that configuration. This
        command can be sent multiple times before a start is received and only
        the last configuration is kept.
        start: Start reading the sensor data of the connected devices and send
        it as plain text via the socket. If no configuration was sent then the
        start command is ignored. Once started no configuration changes can be
        done anymore.
        stop: Stop sending sensor data and disconnect from all devices. Once
        stopped, configuration changes can be done again and/or reading of
        sensor data can be started again.

    """

    valid_simulation_modes = (0, 1)

    def __init__(self, callback: Callable, simulation_mode: int) -> None:
        self.log = logging.getLogger(type(self).__name__)
        if simulation_mode not in self.valid_simulation_modes:
            raise ValueError(
                f"simulation_mode={simulation_mode} "
                f"not in valid_simulation_modes={self.valid_simulation_modes}"
            )

        self.simulation_mode = simulation_mode

        self._callback = callback
        self._configuration: Optional[Dict[str, Any]] = None
        self._started = False
        self._devices: List[BaseDevice] = []

        self.dispatch_dict: Dict[str, Callable] = {
            Command.CONFIGURE: self.configure,
            Command.START: self.start_sending_telemetry,
            Command.STOP: self.stop_sending_telemetry,
        }

        # A set of required keys which will be used in the configuration
        # validation.
        self.required_keys = frozenset(
            (Key.NAME, Key.CHANNELS, Key.DEVICE_TYPE, Key.SENSOR_TYPE)
        )

    async def handle_command(self, command: str, **kwargs: Any) -> None:
        """Handle incomming commands and parameters.

        Parameters
        ----------
        command: `str`
            The command to handle.
        kwargs:
            The parameters to the command.
        """
        self.log.info(f"Handling command {command} with kwargs {kwargs}")
        func = self.dispatch_dict[command]
        try:
            await func(**kwargs)
            response = {Key.RESPONSE: ResponseCode.OK}
        except CommandError as e:
            self.log.exception("Encountered a CommandError.")
            response = {Key.RESPONSE: e.response_code}
        await self._callback(response)

    def _validate_configuration(self, configuration: Dict[str, Any]):
        """Validate the configuration.

        Parameters
        ----------
        configuration: `dict`
            A dict representing the configuration. The format of the dict
            follows the configuration of the ts_ess project.

        Raises
        ------
        `CommandError`:
            In case the provided configuration is incorrect.

        """
        # Key.DEVICES is mandatory.
        if Key.DEVICES not in configuration:
            raise CommandError(
                msg=f"Missing configuration key {Key.DEVICES}.",
                response_code=ResponseCode.INVALID_CONFIGURATION,
            )
        # Only one key allowed.
        if len(configuration.keys()) != 1:
            raise CommandError(
                msg=f"Expected one configuration key but got {len(configuration.keys())}.",
                response_code=ResponseCode.INVALID_CONFIGURATION,
            )
        # Validate the device configurations.
        device_configurations = configuration[Key.DEVICES]
        if not device_configurations:
            raise CommandError(
                msg=f"The configuration data for key {Key.DEVICES} is missing.",
                response_code=ResponseCode.INVALID_CONFIGURATION,
            )
        for device_configuration in device_configurations:
            self._validate_device_configuration(
                device_configuration=device_configuration
            )

    def _validate_device_configuration(self, device_configuration: Dict[str, Any]):
        """Validate the device configuration.

        Parameters
        ----------
        device_configuration: `dict`
            A dict representing the device configuration. The format of the
            dict follows the configuration of the ts_ess project.

        Raises
        ------
        `CommandError`:
            In case the provided configuration is incorrect.

        """
        # Key.NAME, Key.CHANNELS, Key.DEVICE_TYPE and Key.SENSOR_TYPE are
        # mandatory.
        missing_keys = self.required_keys - device_configuration.keys()
        if missing_keys:
            raise CommandError(
                msg=f"Missing required configuration keys {sorted(missing_keys)}",
                response_code=ResponseCode.INVALID_CONFIGURATION,
            )

        # Make sure that Key.DEVICE_TYPE has the correct value.
        if device_configuration[Key.DEVICE_TYPE] not in [
            DeviceType.FTDI,
            DeviceType.SERIAL,
        ]:
            raise CommandError(
                msg=f"The value {device_configuration[Key.DEVICE_TYPE]} for key"
                f" {Key.DEVICE_TYPE} must be either {DeviceType.FTDI}"
                f" or {DeviceType.SERIAL}",
                response_code=ResponseCode.INVALID_CONFIGURATION,
            )

        # Make sure that Key.SENSOR_TYPE has the correct value.
        if device_configuration[Key.SENSOR_TYPE] not in [
            SensorType.TEMPERATURE,
            SensorType.WIND,
        ]:
            raise CommandError(
                msg=f"The value {device_configuration[Key.SENSOR_TYPE]} for key"
                f" {Key.DEVICE_TYPE} must be "
                f"{SensorType.TEMPERATURE} or {SensorType.WIND}",
                response_code=ResponseCode.INVALID_CONFIGURATION,
            )

        # Make sure that Key.FTDI_ID is present for DeviceType.FTDI devices.
        if device_configuration[Key.DEVICE_TYPE] == DeviceType.FTDI:
            if Key.FTDI_ID not in device_configuration:
                raise CommandError(
                    msg=f"Missing configuration key {Key.FTDI_ID} for device of type {DeviceType.FTDI}",
                    response_code=ResponseCode.INVALID_CONFIGURATION,
                )
        # Make sure that Key.SERIAL_PORT is present for DeviceType.SERIAL
        # devices.
        if device_configuration[Key.DEVICE_TYPE] == DeviceType.SERIAL:
            if Key.SERIAL_PORT not in device_configuration:
                raise CommandError(
                    msg=f"Missing configuration key {Key.SERIAL_PORT} for device of type {DeviceType.SERIAL}",
                    response_code=ResponseCode.INVALID_CONFIGURATION,
                )

    async def configure(self, configuration: Dict[str, Any]) -> None:
        """Apply the configuration.

        Parameters
        ----------
        configuration: `dict`
            The contents of the dict depend on the type of sensor. See the
            ts_ess configuration schema for more details.

        Returns
        -------
        response_code: `ResponseCode`
            OK if the command handler was not started.
            ALREADY_STARTED if the command handler was started.

        """
        self.log.info(f"configure with configuration data {configuration}")
        if self._started:
            raise CommandError(
                msg="Ignoring the configuration because telemetry loop already running. Send a stop first.",
                response_code=ResponseCode.ALREADY_STARTED,
            )
        self._validate_configuration(configuration=configuration)

        self._configuration = configuration

    async def start_sending_telemetry(self) -> None:
        """Connect the sensors and start reading the sensor data.

        Returns
        -------
        response_code: `ResponseCode`
            OK if the command handler was configured.
            NOT_CONFIGURED if the command handler was not configured.

        """
        self.log.info("start_sending_telemetry")
        if not self._configuration:
            raise CommandError(
                msg="No configuration has been received yet. Ignoring start command.",
                response_code=ResponseCode.NOT_CONFIGURED,
            )
        await self.connect_devices()
        self._started = True

    async def connect_devices(self) -> None:
        """Loop over the configuration and start all devices."""
        self.log.info("connect_devices")
        device_configurations = self._configuration[Key.DEVICES]  # type: ignore
        self._devices = []
        for device_configuration in device_configurations:
            device = self._get_device(device_configuration)
            self._devices.append(device)
            await device.start()

    async def stop_sending_telemetry(self) -> ResponseCode:
        """Stop reading the sensor data.

        Returns
        -------
        response_code: `ResponseCode`
            OK if the command handler was started.
            NOT_STARTED if the command handler was not started.

        """
        self.log.info("stop_sending_telemetry")
        if not self._started:
            raise CommandError(
                msg="Not started yet. Ignoring stop command.",
                response_code=ResponseCode.NOT_STARTED,
            )
        self._started = False
        while self._devices:
            device = self._devices.pop(-1)
            await device.stop()
        return ResponseCode.OK

    def _get_device(self, device_configuration: dict) -> BaseDevice:
        """Get the device to connect to by using the configuration of the CSC
        and by detecting whether the code is running on an aarch64 architecture
        or not.

        Parameters
        ----------
        device_configuration: `dict`
            A dict representing the device to connect to. The format of the
            dict follows the configuration of the ts_ess project.

        Returns
        -------
        device: `TemperatureSensor` or `VcpFtdi` or `RpiSerialHat` or `None`
            The device to connect to.

        Raises
        ------
        RuntimeError
            In case an incorrect configuration has been loaded.
        """
        sensor = self._get_sensor(device_configuration=device_configuration)
        if self.simulation_mode == 1:
            from .device import MockDevice

            device: BaseDevice = MockDevice(
                name=device_configuration[Key.NAME],
                device_id=device_configuration[Key.FTDI_ID],
                sensor=sensor,
                callback_func=self._callback,
                log=self.log,
                disconnected_channel=None,
            )
            return device
        elif device_configuration[Key.DEVICE_TYPE] == DeviceType.FTDI:
            from .device import VcpFtdi

            device = VcpFtdi(
                name=device_configuration[Key.NAME],
                device_id=device_configuration[Key.FTDI_ID],
                sensor=sensor,
                callback_func=self._callback,
                log=self.log,
            )
            return device
        elif device_configuration[Key.DEVICE_TYPE] == DeviceType.SERIAL:
            # make sure we are on a Raspberry Pi4
            if "aarch64" in platform.platform():
                from .device import RpiSerialHat

                device = RpiSerialHat(
                    name=device_configuration[Key.NAME],
                    device_id=device_configuration[Key.SERIAL_PORT],
                    sensor=sensor,
                    callback_func=self._callback,
                    log=self.log,
                )
                return device
        raise RuntimeError(
            f"Could not get a {device_configuration[Key.DEVICE_TYPE]!r} device"
            f"on architecture {platform.platform()}. Please check the "
            f"configuration."
        )

    def _get_sensor(self, device_configuration: dict) -> BaseSensor:
        if device_configuration[Key.SENSOR_TYPE] == SensorType.TEMPERATURE:
            sensor: BaseSensor = TemperatureSensor(
                num_channels=device_configuration[Key.CHANNELS],
                log=self.log,
            )
            return sensor
        elif device_configuration[Key.SENSOR_TYPE] == SensorType.WIND:
            sensor = WindSensor(
                num_channels=device_configuration[Key.CHANNELS],
                log=self.log,
            )
            return sensor
        raise RuntimeError(
            f"Could not get a {device_configuration[Key.SENSOR_TYPE]!r} sensor"
            f"on architecture {platform.platform()}. Please check the "
            f"configuration."
        )
