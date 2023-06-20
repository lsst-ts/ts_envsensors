.. py:currentmodule:: lsst.ts.ess.controller

.. _lsst.ts.ess.controller.version_history:

###############
Version History
###############

v0.8.2
======

* Fix write JSON.

Requires:

* ts_ess_common
* ts_tcpip 1.1
* ts_utils 1.0

v0.8.1
======

* Fix pytest import issue.

Requires:

* ts_ess_common
* ts_tcpip 1.1
* ts_utils 1.0

v0.8.0
======

* Move the sensor documentation to ts_ess_common.

Requires:

* ts_ess_common
* ts_tcpip 1.1
* ts_utils 1.0

v0.7.10
=======

* Use ts_pre_commit_conf.
* Modernize Jenkinsfile.
* Improve entry point.
  This includes removing it from `conda/meta.yaml` since having it in `pyproject.toml` is enough.
* Make the RpiSerialHat test work.

Requires:

* ts_ess_common
* ts_tcpip 1.1
* ts_utils 1.0

v0.7.9
======

* Remove scons support.
* Git hide egg info and simplify .gitignore.
* Further refinements for ts_pre_commit_config:

  * Stop running pytest linters in ``pyproject.toml``.
  * Delete ``setup.cfg``; it has been replaced by ``.flake8``.
  * ``conda/meta.yaml``: remove setup.cfg (and the obsolete script_env section).

Requires:

* ts_ess_common
* ts_tcpip 0.3
* ts_utils 1.0

v0.7.8
======

* Documentation changes:

  * Add Young weather station documentation.
  * Add missing Aurora Cloud Sensor documentation (it was present but not part of the built documentation).
  * Fix a sphinx error in Campbell Scientific CSAT3B Three-Dimensional Sonic Anemometer docs.
  * Add documentation for how to add a new sensor.

* git ignore built documentation files.

Requires:

* ts_ess_common
* ts_tcpip 0.3
* ts_utils 1.0

v0.7.7
======

* Clean up pyproject.toml dependencies.
* Remove `pip install` step since the dependencies were added to ts-develop.

Requires:

* ts_ess_common
* ts_tcpip 0.3
* ts_utils 1.0

v0.7.6
======

* Clean up conda recipe dependencies.
* Ignore decoding errors for serial device sensors for the first line of telemetry read from the sensor.

Requires:

* ts_ess_common
* ts_tcpip 0.3
* ts_utils 1.0

v0.7.5
======

* Remove root workaround from Jenkinsfile.

Requires:

* ts_ess_common
* ts_tcpip 0.3
* ts_utils 1.0

v0.7.4
======

* pre-commit: update mypy version

Requires:

* ts_ess_common
* ts_tcpip 0.3
* ts_utils 1.0

v0.7.3
======

* Switch from py.test to pytest.
* Add documentation for the Boltek lightning and electric field level sensors.

Requires:

* ts_ess_common
* ts_tcpip 0.3
* ts_utils 1.0

v0.7.2
======

* Use AioSerial for RPi Serial Hat serial devices.

Requires:

* ts_ess_common
* ts_tcpip 0.3
* ts_utils 1.0

v0.7.1
======

* Restore pytest config.
* Fix CSAT3B baud rate.

Requires:

* ts_ess_common
* ts_tcpip 0.3
* ts_utils 1.0

v0.7.0
======

* Add support for multiple Python versions for conda.
* Sort imports with isort.
* Install new pre-commit hooks.

Requires:

* ts_ess_common
* ts_tcpip 0.3
* ts_utils 1.0

v0.6.0
======

* Add baud_rate configuration key.
* Add support for the Campbell Scientific CSAT3B 3D anemometer.

Requires:

* ts_ess_common
* ts_tcpip 0.3
* ts_utils 1.0

v0.5.1
======

* Make the entry point synchronous (and rename it to match the bin script).

v0.5.0
======

* Modernize pre-commit config versions.
* Switch to pyproject.toml.
* Use entry_points instead of bin scripts.

Requires:

* ts_ess_common
* ts_tcpip 0.3
* ts_utils 1.0

v0.4.6
======

* Correct the spelling of the brand name 'GILL'.

Requires:

* ts_ess_common
* ts_tcpip 0.3
* ts_utils 1.0

v0.4.5
======

* Remove unnecessary code that checks for aarch64 architecture.
* Use a ThreadPool for reading the FTDI device.

Requires:

* ts_ess_common
* ts_tcpip 0.3
* ts_utils 1.0

v0.4.4
======

* Remove START and STOP commands.
* The sensor name, timestamp, response code and data are encoded as separate named entities.

Requires:

* ts_ess_common
* ts_tcpip 0.3
* ts_utils 1.0

v0.4.3
======

* Fix a new mypy error by not checking DM's `lsst/__init__.py` files.

Requires:

* ts_ess_common
* ts_tcpip 0.3
* ts_utils 1.0

v0.4.2
======

* Fixed setting the BAUD rate for FTDI devices.
* Added a reference to the documentation for the 3D Campbell Scientific anemometers to the documentation index.
* Ignoring 'doc/conf.py' for MyPy.

Requires:

* ts_ess_common
* ts_tcpip 0.3
* ts_utils 1.0

v0.4.1
======

* Fixed import for ESS Common MockTestTools.

Requires:

* ts_ess_common
* ts_tcpip 0.3
* ts_utils 1.0

v0.4.0
======

* Replaced the use of ts_salobj functions with ts_utils functions.
* Moved all device reply validating code to ts.ess.common.
* Moved all sensors code from ts.ess.controller to ts.ess.common.
* Moved code to determine what sensor is connected from ts.ess.controller to ts.ess.common.
* Moved BaseDevice and MockDevice from ts.ess.controller to ts.ess.common.
* Removed all obsolete schema related code since it also is in ts.ess.common.
* Updated the documentation to reflect all sensor and device code changes.
* Moved most of the command handler code and the socket server unit test from ts.ess.controller to ts.ess.common.
* Removed all Raspberry Pi specific code since setting the GPIO pins should be handled by the OS.
* Added unit tests for the FTDI and Raspberry Pi Serial Hat devices.
* Added location to the configuration of the devices.
* Fixed wrong baudrate values for serial and FTDI devices.

Requires:

* ts_ess_common
* ts_tcpip 0.3
* ts_utils 1.0

v0.3.0
======

* Added support for the Omega HX85A and HX85BA humidity sensors.
* Made the FTDI and RpiSerialHat devices work.
* Added exception handling in the sensors code.
* Cleaned up the Python modules.
* Added dcoumentation for the sensor protocols.
* Validating incoming configurations against a JSON schema instead of using very complicated custom code.
* Renamed the project to ts_ess_controller and extracted common code to ts_ess_common.

Requires:

* ts_ess_common
* ts_tcpip 0.3.1


v0.2.0
======

* Made the conda package `noarch`.

Requires:

* ts_tcpip 0.3.1


v0.1.0
======

First release of the Environmental Sensors Suite socket server and sensor reading code.

This version already includes many useful things:

* A functioning socket server (for which the ``ts_tcpip`` socket server is used).
* Code that reads the output of the connected sensors and sends the data via the socket server.
* Support for USB and FTDI sensors.
* Added support for connecting to and reading telemetry from multiple sensors.
* Added configuration error handling.

Requires:

* ts_tcpip 0.2.0
