"""Micropython generic sensor bases classes"""
try:
    from __future__ import annotations  # type: ignore
    from typing import Any, Callable, Literal, Iterable
except ImportError:
    pass

# DEBUG: Try to import loop profiler and set variable to control if it used
# Only to allow using the driver with or without de loop profiler
# Erase after complete debug
try:
    from loop_profiler import Profiler
except ImportError:
    profiler_debug = False
else:
    profiler_debug = True

import math
import time
from collections import OrderedDict
from machine import Pin


class SensorError(Exception):
    pass


class InfoUnit:
    """Represents basic unit of information inside a Container"""

    allowed_iu_types = ("config", "data", "frame", "command")

    # Additional to those enforced in __init__
    mandatory_parameters = {
        "data": (),
        "config": ("default", "allowed", "pack"),
        "frame": (),
        "command": ("pack"),
    }

    def unimplemented_pack(self, value):
        """Unimplemented pack method to catch some potential errors"""
        raise SensorError(
            f"Unexpected use of pack method for InfoUnit {self.name}, please check configuration of the InfoUnit or implement the correct pack method"
        )

    def __init__(
        self,
        *,
        name: str,
        iu_type: str,
        container: Container,
        size_bits: int,
        shift: int,
        pack: Callable = unimplemented_pack,
        unpack: Callable,
        default: Any = None,
        allowed: Any = None,
        help: str,
    ):
        """InfoUnit init.

        All arguments must be keyword arguments.

        Args:
            name: Name of the info unit, ideally same as datasheet.
            iu_type: Type of info unit, e.g. config, data.
            container: Container (Register, Frame, others?) object where the InfoUnit belongs.
                Updated later at sensor initialization.
            size_bits: Size of the info unit in bits
            shift: Possition respect to the container (left shift).
            pack: Function that translates or packs the human readable value into the actual content stored into the Container.
                First argument is always the InfoUnit, which needs to be passed explicitly in the call.
            unpack: Function that translates or unpacks the actual content stored into the Container into the human readable value.
                First argument is always the InfoUnit, which needs to be passed explicitly in the call.
            default: Default (human readable) value for the info unit.
            allowed: Human readable allowed values for this InfoUnit.
                Usually an iterable with allowed values, but depends on InfoUnit semantics.
            help: Help string explaining the info unit, useful for error messages.
        """

        self.name = name
        self.iu_type = iu_type
        self.container = container
        self.default = default
        self.size_bits = size_bits
        self.shift = shift
        self.allowed = allowed
        self.pack = lambda value: pack(self, value)
        self.unpack = lambda value: unpack(self, value)
        self.help = help

        # Updated in Sensor._init_data_structure(). Not strictly needed but makes code more readable
        self.sensor: Sensor
        # Mask, usually 0b111....1 size of the data for AND operations
        self.mask = int("1" * self.size_bits, 2) if self.size_bits > 0 else 1
        # Number of bytes that have to be read to access this InfoUnit
        self.size_bytes = math.ceil(self.size_bits / 8)

        # Some consistency checks
        if iu_type not in InfoUnit.allowed_iu_types:
            raise SensorError(
                f"Info unit type must be one of {InfoUnit.allowed_iu_types}"
            )

        # Check if mandatory arguments are provided
        for arg in InfoUnit.mandatory_parameters[self.iu_type]:
            if arg is None:
                raise SensorError(
                    f"{self.name} InfoUnit is defined as {self.iu_type}, and does not have {arg} argument defined. {self.iu_type} InfoUnits have these mandatory arguments: {InfoUnit.mandatory_parameters.get(self.iu_type)}"
                )
        # Check if pack and unpack methos are actually callable
        if not callable(pack) or not callable(unpack):
            raise SensorError(
                f"Info Unit {self.name} pack or unpack methods are not callable, please review config."
            )

    def read(self, reg_value: int) -> Any:
        """Returns the human readable content of the InfoUnit, given the register value.
        The reg_value is the register value in with the InfoUnit lives"""

        iu_content = reg_value >> self.shift & self.mask
        return self.unpack(iu_content)

    def write(self, iu_value: Any) -> int:
        """Returns the int value that need to be stored in the Container / Register for the requested InfoUnit human-readable value
        The returned value is ready to be ORed with the values from the other InfoUnits"""

        if iu_value is None or iu_value == "default":
            iu_value = self.default
        self._check_params(iu_value)
        iu_content = self.pack(iu_value)
        reg_iu_content = (iu_content & self.mask) << self.shift
        self.sensor._debug_print("IU.write",'iu_name', self.name, 'iu_value', iu_value,'iu_content',iu_content,'reg_iu_content',reg_iu_content)  # fmt: skip
        return reg_iu_content

    def _check_params(self, iu_value: Any) -> bool:
        """Checks requested value against allowed values. Raise exception if it fails"""
        if not iu_value in self.allowed:
            raise SensorError(
                f"Parameter '{self.name}' must be in {self.allowed}. Was '{iu_value}' \nParameter help: {self.help}"
            )
        return True

    def _pretty_print(self):
        """Human representation of info unit object"""

        print("\n *** Information Unit ***")
        print("- Name:", self.name)
        print("- Type:", self.iu_type)
        if self.allowed:
            print("- Allowed:", self.allowed)
        else:
            print("- Allowed: N/A")
        print("- Register:", self.container.name)
        print("- Help", self.help)


class Container:
    """Represents a container of basic InfoUnits.
    Register, Frame, and potentially other classes extend this one
    """

    # TODO See if some common functionality should be migrated to this class
    def __init__(self):
        self.name: str = ""


class Register(Container):
    """Represents a register inside the sensor, can be a single register or a group
    to facilitate addressing multi regiter values

    """

    # Allowed types of registers, checked at __init__
    allowed_types = (
        "config",
        "data",
        "command",
    )

    def __init__(
        self,
        name: str,
        container_type: str,
        address: int,
        permission: str,
        size_bytes: int,
        help: str,
    ):
        self.name = name  # Name of the register, ideally same as datasheet
        self.container_type = container_type  # Type of register e.g. config, data,
        self.address = address  # Base address of the register
        self.permission = permission  # Operations allowed on register: RO, WO, RW (Read Only, Write Only, Read/Write)
        self.size_bytes = size_bytes  # Size of the register usefull if you want to read/write several registers as one, like with values that span several registers
        self.help = help  # Help string explaining the register, useful for error messages
        # The sensor to which the register belongs, to facilitate drilling up/down. Updated later at sensor initialization
        self.sensor: Sensor
        # List of info units contained in this register. Updated later ar sensor initialization
        self.info_units: list[InfoUnit] = []

        # Consistency checks
        if container_type not in Register.allowed_types:
            raise SensorError(f"Register type must be one of {Register.allowed_types}")

    def read(self) -> dict:
        """Return a dict containing all InfoUnits in the register"""
        reg_value = self._read_raw()
        return OrderedDict({iu.name: iu.read(reg_value) for iu in self.info_units})

    def _read_raw(self) -> int:
        """Return de value contained in a register as int."""
        reg_content = self.sensor._bus._read_reg(self.address, self.size_bytes)
        return int.from_bytes(reg_content, self.sensor._endianness)

    def _pretty_print(self):
        """Human-readable representation of Register object"""
        print("\n *** Register ***")
        print("- Name:", self.name)
        print("- Type:", self.container_type)
        print("- Help:", self.help)
        print("- Info Units:", tuple(iu.name for iu in self.info_units))


class Frame(Container):
    """
    Represents a data frame, contains information about the frame itself and InfoUnits
    """

    allowed_types = ("data",)  # Allowed types of frames

    def __init__(
        self,
        name: str,
        header: int,
        size_bytes: int,
        representation: str,
        error_count: int,
        container_type: str,
        help: str,
    ):
        self.name = name  # Name of the frame, ideally same as datasheet
        self.header = header  # Header that identifies this type of frame
        self.size_bytes = size_bytes  # Total size of the frame
        self.representation = representation  # Graphical representation of this kind of frame (for debug purposes)
        self.error_count = error_count  # If this type of frame counts as an error
        self.container_type = container_type  # Type of frame e.g. config, data,
        self.help = help
        self.sensor: Sensor  # The sensor to which the frame belongs, to facilitate drilling up/down. Updated later at sensor initialization
        self.info_units = (
            []
        )  # List of info units contained in this frame. Updated later ar sensor initialization
        # Some consistency checks
        if container_type not in Frame.allowed_types:
            raise SensorError(f"Frame type must be one of {Frame.allowed_types}")

    def read(self, content):
        """Returns a dict with all the InfoUnits in the frame in human readable format"""
        result = {}
        for iu in self.info_units:
            iu_content = content >> iu.shift & iu.mask
            result.update({iu.name: iu.unpack(iu_content)})
        return result

    def _pretty_print(self):
        """Human representation of Frame object"""
        print("\n *** Frame ***")
        print("- Name:", self.name)
        print("- Type:", self.container_type)
        print("- Help:", self.help)
        print("- Info Units:", tuple(iu.name for iu in self.info_units))


class Sensor:
    """
    Represents a base sensor class, contains methods interact with the sensor.
    Should not be directly instantiated, a specific sensor subclass should be instead.
    """

    def __init__(self, bus, debug_print=False, **kwargs):
        self._check_class()
        self.name: str = ""
        self.help: str = ""
        self._sensor_registers: dict[str, Register] = OrderedDict()
        self._sensor_info_units: dict[str, InfoUnit] = OrderedDict()
        self._sensor_frames: dict[int, Frame] = OrderedDict()
        self._endianness: Literal["little", "big"]
        self._debug_print_enable = debug_print
        self._config_presets: dict[str, dict[str, Any]] = {}
        if profiler_debug:
            self.pfl = Profiler(active=True, name="sensor.py")  # DEBUG
        bus_name = bus.__class__.__name__
        if bus_name in ("I2C", "SoftI2C"):
            self._bus = I2CBUS(self, bus, **kwargs)
        elif bus_name in ("SPI", "SoftSPI"):
            try:
                spi_cs = kwargs["spi_cs"]
            except KeyError:
                raise SensorError(
                    "You must provide CS Pin (machine.Pin object) as `spi_cs` keyword argument "
                )
            self._bus = SPIBUS(self, bus, spi_cs=spi_cs)
        else:
            raise NotImplementedError(
                "Unrecognized bus type. This sensor must be initialized "
                "passing a bus object (machine.I2C, machine.SPI, etc.)"
            )

    def _init_data_structure(self):
        """
        Creates Sensor data structures and relationships.

        Sensor._sensor_registers dict is populated and the register get their Register.sensor parent Sensor reference.
        Sensor._sensor_info_units dict is populated. A dict with names as keys is used to facilitate lookups from kwargs strings.
        Sensor._sensor_frames dict is populated. A dict with the frame headers as key, to facilitate lookups.
        Container.info_units is populated (Register and Frame)
        """

        self._sensor_registers.clear()
        self._sensor_frames.clear()
        self._sensor_info_units.clear()
        name_to_header = {}

        #: Sensor data structure must be in a file named sensorname_data_structure.py
        ds = __import__(self.name.lower() + "_data_structure")

        for reg_dict in ds.REGISTERS:
            reg = Register(**reg_dict)
            reg.sensor = self
            self._sensor_registers[reg.name] = reg

        for frame_dict in ds.FRAMES:
            frame = Frame(**frame_dict)
            frame.sensor = self
            self._sensor_frames[frame.header] = frame
            name_to_header.update({frame.name: frame.header})

        for iu_dict in ds.INFO_UNITS:
            iu = InfoUnit(**iu_dict)
            iu.sensor = self
            if iu.iu_type == "frame":
                cont_dict = self._sensor_frames
                cont_key = name_to_header[iu.container]
            else:
                cont_dict = self._sensor_registers
                cont_key = iu.container

            try:
                # Replace str with reference to the Container
                iu.container = cont_dict[cont_key]  # type: ignore
            except KeyError:
                raise SensorError(
                    f"Sensor init failed with InfoUnit {iu.name} while trying to add it's container {iu.container}, which apparently was not declared as a Container previously"
                )
            iu.container.info_units.append(iu)
            self._sensor_info_units[iu.name] = iu

        try:
            self._config_presets = ds.CONFIG_PRESETS.copy()
        except AttributeError:
            pass

    def _pretty_print(self):
        """Human representation of Sensor object."""

        print("\n")
        print("**************")
        print("*** SENSOR ***")
        print("**************")
        print("- Name:", self.name)
        print("- Help:", self.help)
        print(
            "- Config registers:",
            tuple(
                reg.name
                for reg in self._sensor_registers.values()
                if reg.container_type == "config"
            ),
        )
        print(
            "- Data registers:",
            tuple(
                reg.name
                for reg in self._sensor_registers.values()
                if reg.container_type == "data"
            ),
        )
        print(
            "- Config Info units:",
            tuple(
                iu.name
                for iu in self._sensor_info_units.values()
                if iu.iu_type == "config"
            ),
        )
        print(
            "- Data Info units:",
            tuple(
                iu.name for iu in self._sensor_info_units.values() if iu.iu_type == "data"
            ),
        )
        print("- Frames:", tuple(frame.name for frame in self._sensor_frames.values()))

    def info(self, arg=None):
        """Prints sensor info"""
        if not arg or arg == "sensor":
            self._pretty_print()
            print(
                "To get info about Registers, Info Units or Frames use Sensor.info('registers'), Sensor.info('info_units') or Sensor.info('frames')"
            )
        elif arg == "registers":
            for reg in self._sensor_registers.values():
                reg._pretty_print()
        elif arg == "info_units":
            for iu in self._sensor_info_units.values():
                iu._pretty_print()
        elif arg == "frames":
            for frame in self._sensor_frames.values():
                frame._pretty_print()
        else:
            print(
                "Valid arguments for this function are: 'sensor', 'register', 'info_units', 'frames'"
            )

    def _check_class(self):
        """Raise error if Sensor class ir directly instantiated"""
        if self.__class__.__name__ == "Sensor":
            raise SensorError(
                "Sensor class should not be directly instantiated, a specific sensor subclass should be instead"
            )

    def _check_params(self, *args):
        """Checks if parameters passed through args are legal. Raise exception if not"""
        # TODO Should be a different check for config parameters or data
        self._debug_print("_check_params", "args:", args)  # fmt: skip
        for param in args:
            if not param in self._sensor_info_units:
                raise SensorError(
                    f"Parameter '{param}' is not legal.\nAllowed values are: {tuple(self._sensor_info_units.keys())}"
                )
        return True

    def _debug_print(self, *args) -> None:
        """Print statement for debugging purposes controlled by a variable"""
        if self._debug_print_enable:
            if isinstance(args[0], dict):
                self._print_configs(VALUE=args[0])
            else:
                print("[DEBUG]", *args)

    def _pack(self, info_unit: str, value) -> bytes:
        """Just for testing packing and unpacking, erase later"""
        iu = self._sensor_info_units[info_unit]
        content = iu.pack(value)
        print("Sensor._pack", "Value", value, "Packed content", content)
        return content

    def _unpack(self, info_unit: str, content: bytes):
        """Just for testing packing and unpacking, erase later"""
        iu = self._sensor_info_units[info_unit]
        value = iu.unpack(content)
        print("Sensor._unpack", "Content", content, "Unpacked value", value)
        return value

    def _read_register_list(self, reg_list: Iterable[Register]) -> dict:
        """Reads a register list and returns a dict with all info unit contents."""

        if profiler_debug:
            self.pfl.begin("_read_register_list")  # DEBUG
        result = OrderedDict()
        self._debug_print("_read_register_list:", "reg_list", tuple(reg.name for reg in reg_list))  # fmt: skip
        for reg in reg_list:
            if profiler_debug:
                self.pfl.begin("Each register read")  # DEBUG
            result.update(reg.read())
            if profiler_debug:
                self.pfl.end("Each register read")  # DEBUG
        if profiler_debug:
            self.pfl.end("_read_register_list")  # DEBUG
        return result

    def config_read(self, *params, print_result=False):
        """Read current configuration. Return a dict with requested values or all if none specified"""
        if not params:
            # No explicit parameter request, return all config
            affected_registers: set[Register] = set(
                reg
                for reg in self._sensor_registers.values()
                if reg.container_type == "config"
            )
            self._debug_print("config_read:", "aff_regs", tuple(r.name for r in affected_registers))  # fmt: skip
            result = self._read_register_list(affected_registers)
            self._debug_print("config_read:", "returned result dict")  # fmt: skip
            self._debug_print(result)  # fmt: skip
            return result
        else:
            # List of parameters requested, return only those
            self._check_params(*params)
            affected_registers: set[Register] = set(
                iu.container
                for iu in self._sensor_info_units.values()
                if iu.name in params and iu.iu_type == "config"
            )  # type: ignore
            all_results = self._read_register_list(affected_registers)
            requested_results = {
                key: value for key, value in all_results.items() if key in params
            }
            if print_result:
                self._print_configs(CURRENT=requested_results)

            return requested_results

    def data_read(self, *params, print_result=False) -> dict:
        """Reads an arbitrary list of data info units"""
        # TODO Consider allow reading data and config together. Would it be useful or confusing?

        if profiler_debug:
            self.pfl.begin("data_read")  # DEBUG

        self._debug_print("data_read:", "args", params)  # fmt: skip
        if not params:
            if profiler_debug:
                self.pfl.end("data_read")  # DEBUG
            return {}
        else:
            self._check_params(*params)
            affected_registers: set[Register] = set(
                iu.container
                for iu in self._sensor_info_units.values()
                if iu.name in params and iu.iu_type == "data"
            )  # type: ignore
            self._debug_print("data_read:", "aff_regs", affected_registers)  # fmt: skip
            if not affected_registers:
                print("Sensor.data_read(): No matching data")
                return {}
            all_results = self._read_register_list(affected_registers)
            self._debug_print("data_read:", "all_results")  # fmt: skip
            self._debug_print(all_results)  # fmt: skip
            requested_results = {
                key: value for key, value in all_results.items() if key in params
            }

            if print_result:
                self._print_configs(VALUE=requested_results)

            if profiler_debug:
                self.pfl.end("data_read")  # DEBUG

            return requested_results

    def _write_register_list(
        self,
        affected_registers: Iterable[Register],
        new_config: dict,
    ) -> None:
        """Write the info provided in new_config dict to a set of affected registers"""

        if profiler_debug:
            self.pfl.begin("_write_register_list")  # DEBUG
        self._debug_print("_write_register_list", "new_config", new_config)  # fmt: skip
        for reg in affected_registers:
            reg_value = 0
            for iu in reg.info_units:
                iu_value = new_config.get(iu.name)
                iu_content = iu.write(iu_value)
                reg_value |= iu_content
                self._debug_print("_write_register_list", "iu", iu.name, "iu_value", iu_value, "iu_content", iu_content, "reg_value", reg_value)  # fmt: skip

            reg_content = reg_value.to_bytes(reg.size_bytes, self._endianness)
            self._debug_print("_write_register_list reg_val", reg_value, "cont", reg_content)  # fmt: skip
            self._bus._write_reg(reg.address, reg_content)
        if profiler_debug:
            self.pfl.end("_write_register_list")  # DEBUG

    def config_write(
        self, *, update: bool = True, print_result: bool = True, **parameters
    ) -> dict:
        """
        Takes parameters (info units name strings) as kwargs and update config accordingly.
        update = True  -> Updates only the provided parameters, using current config as base.
        update = False -> Takes parameters defaults, updates it with provided parameters and applies it.
        Returns the applied config.
        """
        if profiler_debug:
            self.pfl.begin("config_write")  # DEBUG
        self._check_params(*parameters.keys())
        affected_registers: Iterable[Register] = set(
            iu.container
            for iu in self._sensor_info_units.values()
            if iu.name in parameters.keys() and iu.iu_type == "config"
        )  # type: ignore
        previous_config = self._read_register_list(affected_registers)  # type: ignore

        if update:
            # Current sensor configuration updated with provided parameters
            base_config = previous_config.copy()
            new_config = base_config.copy()
            new_config.update(parameters)
            self._write_register_list(affected_registers, new_config)
        else:
            # InfoUnit defaults updated with provided parameters
            base_config = {
                iu.name: iu.default
                for iu in self._sensor_info_units.values()
                if iu.container in affected_registers and iu.iu_type == "config"  # type: ignore
            }
            new_config = base_config.copy()
            new_config.update(parameters)
            self._write_register_list(affected_registers, new_config)

        if print_result:
            print("\nconfig_write update mode = ", update)
            self._print_configs(
                PREVIOUS=previous_config,
                BASE=base_config,
                NEW=new_config,
                REQUESTED=parameters,
            )
            print()

        time.sleep_ms(1)
        self._check_sensor_config(new_config)
        self._check_applied_config(new_config)

        if profiler_debug:
            self.pfl.end("config_write")  # DEBUG
        return new_config

    def softreset(self):
        """To be overwritten in subclass if softreset of the device is possible"""
        pass

    def apply_config_preset(self, preset: str) -> None:
        """Applies a preset configuration template.

        Configuration templates are defined in the sensor _data_structure file

        Args:
            preset (str): The preset name we want to apply
        Raises:
            SensorError: If config template is not found
        """
        if preset not in self._config_presets:
            raise SensorError(
                "The requested preset does not exist. Available presets are: \n"
                f"{tuple(self._config_presets.keys())}"
            )

        self.softreset()
        time.sleep_ms(5)
        self._debug_print("apply_config_preset: Applying", preset)
        preset_dict = self._config_presets.get(preset)
        self.config_write(print_result=False, **preset_dict)

    def _check_applied_config(self, requested: dict) -> None:
        """Read current config to check if the requested config was correctly applied"""
        # TODO consider delete after testing or at least make it optional
        error = False
        exceptions = ("forced",)  # Values that shouldn't be checked for some reason
        returned = self.config_read(*requested.keys())
        self._debug_print(f"_check_applied_config:")  # fmt: skip
        if self._debug_print_enable:
            self._print_configs(REQUESTED=requested, RETURNED=returned)
        for key, value in requested.items():
            if value != returned[key] and value not in exceptions:
                print(
                    f"ERROR: {key} Requested: {str(value)} || Sensor: {str(returned[key])}"
                )
                error = True
        if error:
            raise SensorError(
                "The requested configuration was not fully applied. "
                "Details should precede this Traceback"
            )

    def _print_configs(self, **configs: dict[str, dict]):
        """Pretty prints config(s).

        Only accepts config dicts as kwargs.
        The name of the parameter will be its column header, so it matters.
        Can print one configuration or several in adjacent columns, usefull to compare config changes.

        Example:
            `self._print_configs(PREVIOUS=prev_conf_dict, NEW=new_conf_dict)`
        """
        # Aesthetics variables
        col_width_first = 22
        col_width = 12

        # Print headers
        print()
        headers = [
            "PARAMETER",
        ]
        headers.extend(configs.keys())
        for i, header in enumerate(headers):
            if i == 0:
                print(f"{header:{col_width_first}}", end="")
            else:
                print(f"{header:^{col_width}}", end="")
        print()

        # Print content
        all_keys = set()
        for d in configs.values():
            all_keys.update(d.keys())

        for key in sorted(all_keys):
            print(f"{key:{col_width_first}}", end="")
            for d in configs.values():
                key_value = str(d.get(key, "-"))
                print(f"{key_value:^{col_width}}", end="")
            print()

    def _check_sensor_config(self, applied_config: dict):
        """Implements a sensor-specific config error check or other type of controls if exists.

        Subclass must implement this method to trigger appropriate measures"""
        print("WARNING: _check_sensor_config should be overwritten by Sensor subclasses")


class BUS:
    """The BUS class is a component of the Sensor class that provides the methods to
    communicate with the device through the serial bus.

    This base class must be extended by the specific bus subclass: I2C, SPI, UART, etc.
    where the real methods are implemented.
    """

    # TODO: Consider using a preallocated buffer for bus read operations

    def __init__(self, **kwargs):
        self._i2c_addr: int
        self._spi_cs: Pin

    def _write_reg(self, reg_address, data):
        """Writes data into register"""
        raise NotImplementedError(
            "Low level register operation, not implemented in base class"
        )

    def _read_reg(self, reg_address, length):
        """Reads from register n bytes and returns them"""
        raise NotImplementedError(
            "Low level register operation, not implemented in base class"
        )

    def _read_reg_into(self, reg_address, buf):
        """Reads register into existing buffer, returns bytes read"""
        raise NotImplementedError(
            "Low level register operation, not implemented in base class"
        )


class I2CBUS(BUS):
    """Provides the methods to write and read registers from the device using I2C."""

    def __init__(self, sensor: Sensor, i2c, **kwargs):
        super().__init__(**kwargs)
        self.sensor = sensor
        self.i2c = i2c  # I2C object
        self.i2c_addr: int  # Subclass must initialize this address

    def _write_reg(self, reg_address: int, data: int | bytes):
        """Writes data into register

        Accepts a bytes object or an int in range(0, 256)
        """
        if isinstance(data, int):
            self.i2c.writeto_mem(self._i2c_addr, reg_address, bytes(data,))  # fmt: skip
        else:
            for i, b in enumerate(data):
                self.i2c.writeto_mem(self._i2c_addr, reg_address + i, bytes((b,)))

    def _read_reg(self, reg_address, length):
        """Reads from register n bytes and returns them"""
        self.sensor._debug_print("_read_reg: addr", reg_address, "length", length)  # fmt: skip
        return self.i2c.readfrom_mem(self._i2c_addr, reg_address, length)

    def _read_reg_into(self, reg_address, buf):
        """Reads register into existing buffer, returns bytes read"""
        self.i2c.readfrom_mem_into(self._i2c_addr, reg_address, buf)
        self.sensor._debug_print("_read_reg_into: addr", reg_address, "buf length", len(buf))  # fmt: skip
        return len(buf)


class SPIBUS(BUS):
    """Provides the methods to write and read registers from the device using SPI."""

    # TODO Use Signal instead of Pin to allow CS active low or high
    def __init__(self, sensor: Sensor, spi, spi_cs: Pin | None = None, **kwargs):
        super().__init__(**kwargs)
        self.sensor = sensor
        self.spi = spi  # SPI object
        if not isinstance(spi_cs, Pin):
            raise SensorError(
                "Invalid or missing spi_cs Pin (must be a machine.Pin object)"
            )
        else:
            self.spi_cs = spi_cs
        spi_cs.value(1)  # Deactivate CS

    def _write_reg(self, reg_address: int, data: int | bytes):
        """Writes data into register

        Accepts a bytes object or an int in range(0, 256)
        """
        if isinstance(data, int):
            data = bytes((data,))
        self.spi_cs.value(0)  # Activate CS
        # Write byte per byte
        for i, b in enumerate(data):
            to_register = bytes(((reg_address + i) & 0x7F, b))
            self.spi.write(to_register)
        self.spi_cs.value(1)

    def _read_reg(self, reg_address, length):
        """Reads from register n bytes and returns them"""
        self.spi_cs.value(0)  # Activate CS
        # Write one extra byte to wait to pass the first dummy byte that the sensor sends on each read
        seven_addr = bytes((reg_address | 0x80, 0x00))
        self.spi.write(seven_addr)
        result = self.spi.read(length)
        self.spi_cs.value(1)
        _debug_object("SPIBUS._read_reg", "result", result, do_print=False)
        return result

    def _read_reg_into(self, reg_address, buf):
        """Reads register into existing buffer, returns bytes read"""
        print("_read_reg_into: reg_address", reg_address, "type:", type(reg_address))
        self.spi_cs.value(0)  # Activate CS
        self.spi.write(bytes((reg_address | 0x80, 0x00)))
        self.spi.readinto(buf)
        self.spi_cs.value(1)
        print("_read_reg_into: buf", buf, "type:", type(buf), "len", len(buf))


def _debug_object(func_str: str, obj_str: str, obj: Any, do_print: bool = True):
    """Prints information of an object for debug purposes"""
    if do_print:
        print("[DEBUG object]")
        print("Function:", func_str, "\tObject:", obj_str)
        print(
            "Type:", type(obj), "\tLength:", len(obj) if hasattr(obj, "__len__") else "--"
        )
        print("Value:", obj, "HEX: " + str(hex(obj)) if isinstance(obj, int) else "")
        print("[------------]")
