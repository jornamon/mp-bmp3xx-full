"""
Information needed to build the BMP3XX data structure.

It contains the dicts with the args needed to create the 
Containers (Registers, Frames) and the InfoUnits of the Sensor.
These lists are imported at Sensor initialization.
Accurate information here is crucial for correct function of the driver.
The InfoUnits must have a ``container`` arg that is a string that 
*exactly* matches the string ``name`` of a Register or Frame, that 'points' 
to the container where the InfoUnit is.

The pack method of the InfoUnit translate de human-readable value of a InfoUnit into the value 
that needs to be stored in the Register. The unpack method does the reverse operation.
Most time the methods are simple an can be represented with lambda functions inside the dict.
Other times the conversion is a little more involved and the function needs to be
declared outside the dict and referenced.
Another reason to declare the function outside the the dict is it's shared among 
several InfoUnit and thus it can be reused.
In any case, these functions (including lambdas inside dicts) will behave like 
bound methods of the corresponding InfoUnit time and **must** be defined with
``self`` as the first argument, as any bound method.
The second argument passed is always the value of the Container where the InfoUnit lives.
The Container and Sensor attributes can be accessed by ``self.container`` and ``self.sensor``.

"""

import math
from micropython import const

try:
    from typing import Any
except ImportError:
    pass

#########################
###### REGISTERS
#########################

REGISTERS = (
    {
        "name": const("REG_CHIP_ID"),
        "container_type": const("data"),
        "address": const(0x00),
        "permission": const("RO"),
        "size_bytes": const(1),
        "help": const("chip id register, 1 byte"),
    },
    {
        "name": const("REG_REV_ID"),
        "container_type": const("data"),
        "address": const(0x01),
        "permission": const("RO"),
        "size_bytes": const(1),
        "help": const("ASIC revision, 1 byte"),
    },
    {
        "name": const("REG_ERR_REG"),
        "container_type": const("data"),
        "address": const(0x02),
        "permission": const("RO"),
        "size_bytes": const(1),
        "help": const("Error Register, 1 byte"),
    },
    {
        "name": const("REG_STATUS"),
        "container_type": const("data"),
        "address": const(0x03),
        "permission": const("RO"),
        "size_bytes": const(1),
        "help": const("Status Register (command, pressure and temp ready), 1 byte"),
    },
    {
        "name": const("REG_DATA_PRESS_AND_TEMP"),
        "container_type": const("data"),
        "address": const(0x04),
        "permission": const("RO"),
        "size_bytes": const(6),
        "help": const("ASIC revision, 1 byte"),
    },
    {
        "name": const("REG_SENSORTIME"),
        "container_type": const("data"),
        "address": const(0x0C),
        "permission": const("RO"),
        "size_bytes": const(3),
        "help": const("Sensortime register, 3 bytes"),
    },
    {
        "name": const("REG_EVENT"),
        "container_type": const("data"),
        "address": const(0x10),
        "permission": const("RO"),
        "size_bytes": const(1),
        "help": const("Event register, 1 byte"),
    },
    {
        "name": const("REG_INT_STATUS"),
        "container_type": const("data"),
        "address": const(0x11),
        "permission": const("RO"),
        "size_bytes": const(1),
        "help": const("Interruption status register, 1 byte"),
    },
    {
        "name": const("REG_FIFO_LENGTH"),
        "container_type": const("data"),
        "address": const(0x12),
        "permission": const("RO"),
        "size_bytes": const(2),
        "help": const("FIFO length register, 2 bytes"),
    },
    {
        "name": const("REG_FIFO_DATA"),
        "container_type": const("data"),
        "address": const(0x14),
        "permission": const("RO"),
        # Burst read of 7 bytes allows frame by frame access to FIFO dato, though not recommended as primary way to access FIFO
        "size_bytes": const(7),
        "help": const("FIFO data register, 1 byte"),
    },
    {
        "name": const("REG_FIFO_WTM"),
        "container_type": const("config"),
        "address": const(0x15),
        "permission": const("RW"),
        "size_bytes": const(2),
        "help": const("fifo watermark level, 2 bytes (only lower 9 bits in use)"),
    },
    {
        "name": const("REG_FIFO_CONFIG_1"),
        "container_type": const("config"),
        "address": const(0x17),
        "permission": const("RW"),
        "size_bytes": const(1),
        "help": const("fifo config 1, 1 bytes (only lower 5 bits in use)"),
    },
    {
        "name": const("REG_FIFO_CONFIG_2"),
        "container_type": const("config"),
        "address": const(0x18),
        "permission": const("RW"),
        "size_bytes": const(1),
        "help": const("fifo config 2, 1 byte"),
    },
    {
        "name": const("REG_INT_CTRL"),
        "container_type": const("config"),
        "address": const(0x19),
        "permission": const("RW"),
        "size_bytes": const(1),
        "help": const("Interrupt control, 1 byte"),
    },
    {
        "name": const("REG_IF_CONF"),
        "container_type": const("config"),
        "address": const(0x1A),
        "permission": const("RW"),
        "size_bytes": const(1),
        "help": const("Serial Interface configuration, 1 byte"),
    },
    {
        "name": const("REG_PWR_CTRL"),
        "container_type": const("config"),
        "address": const(0x1B),
        "permission": const("RW"),
        "size_bytes": const(1),
        "help": const("controls sensor mode (sleep, forced, normal) and enables/disables press and temp sensors"),
    },
    {
        "name": const("REG_OSR"),
        "container_type": const("config"),
        "address": const(0x1C),
        "permission": const("RW"),
        "size_bytes": const(1),
        "help": const("Oversampling register, 1 byte"),
    },
    {
        "name": const("REG_ODR"),
        "container_type": const("config"),
        "address": const(0x1D),
        "permission": const("RW"),
        "size_bytes": const(1),
        "help": const("Output Data Rate register, 1 byte"),
    },
    {
        "name": const("REG_CONFIG"),
        "container_type": const("config"),
        "address": const(0x1F),
        "permission": const("RW"),
        "size_bytes": const(1),
        "help": const("Config register, mainly IIR filter setting, 1 byte"),
    },
    {
        "name": const("REG_CMD"),
        "container_type": const("command"),
        "address": const(0x7E),
        "permission": const("WO"),
        "size_bytes": const(1),
        "help": const("Command register. NOP, FIFO_FLUSH, SOFTRESET"),
    },
)

#########################
###### FRAMES
#########################

FRAMES = (
    {
        "name": const("FRAME_PRESS_AND_TEMP"),
        "header": const(0x94),
        "size_bytes": const(7),
        "representation": const("B"),
        "error_count": const(0),
        "container_type": const("data"),
        "help": "Frame containing pressure and temperature information",
    },
    {
        "name": const("FRAME_TEMP"),
        "header": const(0x90),
        "size_bytes": const(4),
        "representation": const("T"),
        "error_count": const(0),
        "container_type": const("data"),
        "help": "Frame containing temperature information",
    },
    {
        "name": const("FRAME_PRESS"),
        "header": const(0x84),
        "size_bytes": const(4),
        "representation": const("P"),
        "error_count": const(0),
        "container_type": const("data"),
        "help": "Frame containing pressure information",
    },
    {
        "name": const("FRAME_SENSORTIME"),
        "header": const(0xA0),
        "size_bytes": const(4),
        "representation": const("S"),
        "error_count": const(0),
        "container_type": const("data"),
        "help": "Frame containing sensortime information",
    },
    {
        "name": const("FRAME_CONFIG_CHANGE"),
        "header": const(0x48),
        "size_bytes": const(2),
        "representation": const("C"),
        "error_count": const(0),
        "container_type": const("data"),
        "help": "Frame inserted to indicate a change in FIFO configuration",
    },
    {
        "name": const("FRAME_ERROR"),
        "header": const(0x44),
        "size_bytes": const(2),
        "representation": const("X"),
        "error_count": const(1),
        "container_type": const("data"),
        "help": "Error frame",
    },
    {
        "name": const("FRAME_EMPTY"),
        "header": const(0x80),
        "size_bytes": const(2),
        "representation": const("0"),
        "error_count": const(0),
        "container_type": const("data"),
        "help": "Empty frame, inserted when burst read is longer than actual FIFO length",
    },
)

##############################
###### Pack/unpack methods for Info Units
##############################


def bypass(self, value):
    """Does nothing, human-readable value is same as InfoUnit content,
    can be used for both pack and unpack"""
    return value


def int_to_bytes(self, value: int):
    return value.to_bytes(self.size_bytes, self.sensor.endianness)


def bytes_to_int(self, content: bytes):
    return int.from_bytes(content, self.sensor.endianness)


def pack_log2(self, value: int) -> int:
    """Pack value into log2(value)"""
    return int(math.log2(value))


def unpack_log2(self, value: int) -> int:
    """Unpacks value 2**value"""
    return 2**value


def compensate_readings(self, value: int) -> Any:
    """Sorts out the different ways in which adc values can arrive,
    calls the function that calculate compensated reading in the correct way
    and return the requested information.

    Although the way the compensating is done is always the same, the ADC
    values inside the InfoUnits do not come in the same position.

    Args:
        value (int): InfoUnit value

    Raises:
        Exception: If the InfoUnit in question is not supported by this method

    Returns:
        Any: (press, temp) tuple or press or temp alone depending on the InfoUnit
    """

    if self.name == "press_and_temp":
        adc_press = value & 0xFFFFFF
        adc_temp = value >> 24 & 0xFFFFFF
        return calculate_compensated_readings(self, (adc_press, adc_temp))
    elif self.name == "press":
        adc_press = value & 0xFFFFFF
        adc_temp = value >> 24 & 0xFFFFFF
        return calculate_compensated_readings(self, (adc_press, adc_temp))[0]
    elif self.name == "temp":
        adc_press = value & 0xFFFFFF
        adc_temp = value >> 24 & 0xFFFFFF
        return calculate_compensated_readings(self, (adc_press, adc_temp))[1]
    elif self.name == "frameiu_press_and_temp":
        # values come reversed in the frame
        adc_press = value >> 24 & 0xFFFFFF
        adc_temp = value & 0xFFFFFF
        return calculate_compensated_readings(self, (adc_press, adc_temp))
    elif self.name == "frameiu_temp":
        # only temperature, pass 0 as pressure and return only temp
        adc_press = 0.0
        adc_temp = value & 0xFFFFFF
        return calculate_compensated_readings(self, (adc_press, adc_temp))[1]
    elif self.name == "frameiu_press":
        # only pressure, pass 'standard temperature' and return only pressure
        # 8.43692e6 is just an approx. adc_temp value for ~25C,
        # needed for calculating pressure compensated value
        adc_press = value & 0xFFFFFF
        adc_temp = 8.43692e6
        return calculate_compensated_readings(self, (adc_press, adc_temp))[0]
    elif self.name == 'altitude':
        adc_press = value & 0xFFFFFF
        adc_temp = value >> 24 & 0xFFFFFF
        pressure = calculate_compensated_readings(self, (adc_press, adc_temp))[0]
        return 44307.69 * (1 - (pressure / self.sensor._sea_level_pressure) ** 0.190284)
    else:
        raise Exception(f"Unimplemented method for this type of InfoUnit: IU: {self.name}, Type: {self.iu_type}")


def calculate_compensated_readings(self, adc_values: tuple) -> tuple:
    """Resturns pressure (Pa) and temperature (C) compensated values from adc raw reads
    adc_values is a tuple containing pressure and temp adc values (adc_press, adc_temp)
    Needs to access calibration info stored in the sensor.

    Args:
        adc_values (tuple): (adc_press, adc_temp)

    Returns:
        tuple: compensated (press, temp), Pascals (Pa) and Celsius (C)
    """

    adc_press, adc_temp = adc_values

    # Datasheet 8.5
    T1, T2, T3 = self.sensor._temp_calib
    pd1 = adc_temp - T1
    pd2 = pd1 * T2

    temp = pd2 + (pd1 * pd1) * T3

    # Datasheet 8.6
    P1, P2, P3, P4, P5, P6, P7, P8, P9, P10, P11 = self.sensor._pressure_calib

    pd1 = P6 * temp
    pd2 = P7 * temp**2.0
    pd3 = P8 * temp**3.0
    po1 = P5 + pd1 + pd2 + pd3

    pd1 = P2 * temp
    pd2 = P3 * temp**2.0
    pd3 = P4 * temp**3.0
    po2 = adc_press * (P1 + pd1 + pd2 + pd3)

    pd1 = adc_press**2.0
    pd2 = P9 + P10 * temp
    pd3 = pd1 * pd2
    pd4 = pd3 + P11 * adc_press**3.0

    pressure = po1 + po2 + pd4

    return (pressure, temp)


def parse_single_fifo_frame(self, frame_content: int) -> Any:
    """
    Parses the content of a single FIFO frame and returns the corresponding values.
    Caller should carefully check returned values as they can change depending on the type of frame received
    """
    frame_header = frame_content & self.sensor.frame_header_mask
    frame_data = frame_content >> self.sensor.frame_header_size * 8
    sensor_frames = self.sensor._sensor_frames

    if frame_header in sensor_frames:
        frame = sensor_frames[frame_header]
        return frame.read(frame_data)
    else:
        return "Invalid header"


##############################
###### Info units in Registers
##############################

INFO_UNITS = (
    {
        "name": const("chip_id"),
        "iu_type": const("data"),
        "container": "REG_CHIP_ID",
        "size_bits": const(8),
        "shift": const(0),
        "unpack": bypass,
        "help": const("Chip ID stored in NVM"),
    },
    {
        "name": const("rev_id"),
        "iu_type": const("data"),
        "container": "REG_REV_ID",
        "size_bits": const(8),
        "shift": const(0),
        "unpack": bypass,
        "help": const("ASIC mask revision (minor)"),
    },
    {
        "name": const("fatal_err"),
        "iu_type": const("data"),
        "container": "REG_ERR_REG",
        "size_bits": const(1),
        "shift": const(0),
        "unpack": bypass,
        "help": const("Fatal error bit"),
    },
    {
        "name": const("cmd_err"),
        "iu_type": const("data"),
        "container": "REG_ERR_REG",
        "size_bits": const(1),
        "shift": const(1),
        "unpack": bypass,
        "help": const("Command error bit"),
    },
    {
        "name": const("conf_err"),
        "iu_type": const("data"),
        "container": "REG_ERR_REG",
        "size_bits": const(1),
        "shift": const(2),
        "unpack": bypass,
        "help": const("Configuration error bit"),
    },
    {
        "name": const("cmd_rdy"),
        "iu_type": const("data"),
        "container": "REG_STATUS",
        "size_bits": const(1),
        "shift": const(4),
        "unpack": bypass,
        "help": const("Command ready bit, 1 if ready to accept new command"),
    },
    {
        "name": const("drdy_press"),
        "iu_type": const("data"),
        "container": "REG_STATUS",
        "size_bits": const(1),
        "shift": const(5),
        "unpack": bypass,
        "help": const("Pressure data ready bit, 1 if pressure data is ready to be read."),
    },
    {
        "name": const("drdy_temp"),
        "iu_type": const("data"),
        "container": "REG_STATUS",
        "size_bits": const(1),
        "shift": const(6),
        "unpack": bypass,
        "help": const("Temperature data ready bit, 1 if temperature data is ready to be read."),
    },
    {
        "name": const("press_and_temp"),
        "iu_type": const("data"),
        "container": "REG_DATA_PRESS_AND_TEMP",
        "size_bits": const(48),
        "shift": const(0),
        "unpack": compensate_readings,
        "help": const("Pressure (Pa) and temperature (C) compensated values."),
    },
    {
        "name": const("press"),
        "iu_type": const("data"),
        "container": "REG_DATA_PRESS_AND_TEMP",
        "size_bits": const(48),
        "shift": const(0),
        "unpack": compensate_readings,
        "help": const("Pressure (Pa) compensated value."),
    },
    {
        "name": const("temp"),
        "iu_type": const("data"),
        "container": "REG_DATA_PRESS_AND_TEMP",
        "size_bits": const(48),
        "shift": const(0),
        "unpack": compensate_readings,
        "help": const("Temperature (C) compensated value."),
    },
    {
        "name": const("press_and_temp_adc"),
        "iu_type": const("data"),
        "container": "REG_DATA_PRESS_AND_TEMP",
        "size_bits": const(48),
        "shift": const(0),
        "unpack": lambda self, content: (content & 0x000000FFFFFF, content >> 24 & 0x000000FFFFFF),
        "help": const("Pressure and temperature ADC raw values."),
    },
    {
        # Derivative InfoUnit, does not exist in the sensor
        "name": const("altitude"),
        "iu_type": const("data"),
        "container": "REG_DATA_PRESS_AND_TEMP",
        "size_bits": const(48),
        "shift": const(0),
        "unpack": compensate_readings,
        "help": const("Altitude in meters. Should calibrate sensor before reading altitude."),
    },
    {
        "name": const("sensortime"),
        "iu_type": const("data"),
        "container": "REG_SENSORTIME",
        "size_bits": const(24),
        "shift": const(0),
        "unpack": lambda self, content: content & 0xFFFFFF,
        "help": const("Sensor Time"),
    },
    {
        "name": const("por_detected"),
        "iu_type": const("data"),
        "container": "REG_EVENT",
        "size_bits": const(1),
        "shift": const(0),
        "unpack": bypass,
        "help": const("1 after device power up or softreset. Cleared on read"),
    },
    {
        "name": const("itf_act_pt"),
        "iu_type": const("data"),
        "container": "REG_EVENT",
        "size_bits": const(1),
        "shift": const(1),
        "unpack": bypass,
        "help": const(
            "1 when serial interface transaction occurs during a pressure or temperature conversion. Cleared on read"
        ),
    },
    {
        "name": const("fwm_int"),
        "iu_type": const("data"),
        "container": "REG_INT_STATUS",
        "size_bits": const(1),
        "shift": const(0),
        "unpack": bypass,
        "help": const("FIFO watermark interrupt status"),
    },
    {
        "name": const("ffull_int"),
        "iu_type": const("data"),
        "container": "REG_INT_STATUS",
        "size_bits": const(1),
        "shift": const(1),
        "unpack": bypass,
        "help": const("FIFO full interrupt status"),
    },
    {
        "name": const("drdy"),
        "iu_type": const("data"),
        "container": "REG_INT_STATUS",
        "size_bits": const(1),
        "shift": const(3),
        "unpack": bypass,
        "help": const("Data Ready interrupt status"),
    },
    {
        "name": const("fifo_length"),
        "iu_type": const("data"),
        "container": "REG_FIFO_LENGTH",
        "size_bits": const(9),
        "shift": const(0),
        "unpack": bypass,
        "help": const("FIFO length in bytes 0-511 (9-bits)"),
    },
    {
        "name": const("fifo_data"),
        "iu_type": const("data"),
        "container": "REG_FIFO_DATA",
        "size_bits": const(7 * 8),
        "shift": const(0),
        "unpack": parse_single_fifo_frame,
        "help": const("FIFO 7 bytes of raw data (frames), should not be primary FIFO data access"),
    },
    {
        "name": const("fifo_water_mark"),
        "iu_type": const("config"),
        "container": "REG_FIFO_WTM",
        "default": const(255),
        "size_bits": const(9),
        "shift": const(0),
        "allowed": range(512),
        "pack": bypass,
        "unpack": bypass,
        "help": const("FIFO watermark level in bytes 0-511 (9-bit)"),
    },
    {
        "name": const("fifo_mode"),
        "iu_type": const("config"),
        "container": "REG_FIFO_CONFIG_1",
        "default": const(0),
        "size_bits": const(1),
        "shift": const(0),
        "allowed": (0, 1),
        "pack": bypass,
        "unpack": bypass,
        "help": const("Enables/Disables (1/0) FIFO"),
    },
    {
        "name": const("fifo_stop_on_full"),
        "iu_type": const("config"),
        "container": "REG_FIFO_CONFIG_1",
        "default": const(0),
        "size_bits": const(1),
        "shift": const(1),
        "allowed": (0, 1),
        "pack": bypass,
        "unpack": bypass,
        "help": const("FIFO full behavior, 0: discard old samples, 1: discard new samples"),
    },
    {
        "name": const("fifo_time_en"),
        "iu_type": const("config"),
        "container": "REG_FIFO_CONFIG_1",
        "default": const(0),
        "size_bits": const(1),
        "shift": const(2),
        "allowed": (0, 1),
        "pack": bypass,
        "unpack": bypass,
        "help": const("Enable return of sensortime frames in FIFO reads"),
    },
    {
        "name": const("fifo_press_en"),
        "iu_type": const("config"),
        "container": "REG_FIFO_CONFIG_1",
        "default": const(1),
        "size_bits": const(1),
        "shift": const(3),
        "allowed": (0, 1),
        "pack": bypass,
        "unpack": bypass,
        "help": const("Enable return of pressure frames in FIFO reads"),
    },
    {
        "name": const("fifo_temp_en"),
        "iu_type": const("config"),
        "container": "REG_FIFO_CONFIG_1",
        "default": const(1),
        "size_bits": const(1),
        "shift": const(4),
        "allowed": (0, 1),
        "pack": bypass,
        "unpack": bypass,
        "help": const("Enable return of temperature frames in FIFO reads"),
    },
    {
        "name": const("fifo_subsampling"),
        "iu_type": const("config"),
        "container": "REG_FIFO_CONFIG_2",
        "default": const(1),
        "size_bits": const(3),
        "shift": const(0),
        "allowed": (1, 2, 4, 8, 16, 32, 64, 128),
        "pack": pack_log2,
        "unpack": unpack_log2,
        "help": const("FIFO subsampling factor (human readable). Datasheet 3.6.2"),
    },
    {
        "name": const("data_select"),
        "iu_type": const("config"),
        "container": "REG_FIFO_CONFIG_2",
        "default": const("unfiltered"),
        "size_bits": const(2),
        "shift": const(3),
        "allowed": ("filtered", "unfiltered"),
        "pack": lambda self, value: {"filtered": 1, "unfiltered": 0}.get(value),
        "unpack": lambda self, content: {
            1: "filtered",
            0: "unfiltered",
            2: "unfiltered",
            3: "unfiltered",
        }.get(content),
        "help": const("FIFO data source (human readable), filtered or unfiltered"),
    },
    {
        "name": const("int_od"),
        "iu_type": const("config"),
        "container": "REG_INT_CTRL",
        "default": const("push-pull"),
        "size_bits": const(1),
        "shift": const(0),
        "allowed": ("push-pull", "open-drain"),
        "pack": lambda self, value: {"push-pull": 0, "open-drain": 1}.get(value),
        "unpack": lambda self, content: {0: "push-pull", 1: "open-drain"}.get(content),
        "help": const("Interrupt output type (human readable), push-pull or open-drain"),
    },
    {
        "name": const("int_level"),
        "iu_type": const("config"),
        "container": "REG_INT_CTRL",
        "default": const(1),
        "size_bits": const(1),
        "shift": const(1),
        "allowed": (0, 1),
        "pack": bypass,
        "unpack": bypass,
        "help": const("Interrupt active level 1: high, 0: low"),
    },
    {
        "name": const("int_latch"),
        "iu_type": const("config"),
        "container": "REG_INT_CTRL",
        "default": const(0),
        "size_bits": const(1),
        "shift": const(2),
        "allowed": (0, 1),
        "pack": bypass,
        "unpack": bypass,
        "help": const("Enable interrupt latching for INT pin and INT_STATUS register. Datasheet 3.7.2"),
    },
    {
        "name": const("fwtm_en"),
        "iu_type": const("config"),
        "container": "REG_INT_CTRL",
        "default": const(0),
        "size_bits": const(1),
        "shift": const(3),
        "allowed": (0, 1),
        "pack": bypass,
        "unpack": bypass,
        "help": const("Enable FIFO watermark level reached interrupt (INT pin and INT_STATUS)"),
    },
    {
        "name": const("ffull_en"),
        "iu_type": const("config"),
        "container": "REG_INT_CTRL",
        "default": const(0),
        "size_bits": const(1),
        "shift": const(4),
        "allowed": (0, 1),
        "pack": bypass,
        "unpack": bypass,
        "help": const("Enable FIFO full interrupt (INT pin and INT_STATUS)"),
    },
    {
        "name": const("int_ds"),
        "iu_type": const("config"),
        "container": "REG_INT_CTRL",
        "default": const(0),
        "size_bits": const(1),
        "shift": const(5),
        "allowed": (0, 1),
        "pack": bypass,
        "unpack": bypass,
        "help": const("int_ds 0: low, 1: high"),
    },
    {
        "name": const("drdy_en"),
        "iu_type": const("config"),
        "container": "REG_INT_CTRL",
        "default": const(0),
        "size_bits": const(1),
        "shift": const(6),
        "allowed": (0, 1),
        "pack": bypass,
        "unpack": bypass,
        "help": const("Enable data ready interrupt (INT pin and INT_STATUS)"),
    },
    {
        "name": const("spi3"),
        "iu_type": const("config"),
        "container": "REG_IF_CONF",
        "default": const("spi4"),
        "size_bits": const(1),
        "shift": const(0),
        "allowed": ("spi3", "spi4"),
        "pack": lambda self, value: {"spi4": 0, "spi3": 1}.get(value),
        "unpack": lambda self, content: {0: "spi4", 1: "spi3"}.get(content),
        "help": const(
            "Configure spi interface mode (human readable), spi4 or spi3 for 4-wire and 3-wire configurations"
        ),
    },
    {
        "name": const("i2c_wdt_en"),
        "iu_type": const("config"),
        "container": "REG_IF_CONF",
        "default": const(0),
        "size_bits": const(1),
        "shift": const(1),
        "allowed": (0, 1),
        "pack": bypass,
        "unpack": bypass,
        "help": const("Enable i2c watchdog timer"),
    },
    {
        "name": const("i2c_wdt_sel"),
        "iu_type": const("config"),
        "container": "REG_IF_CONF",
        "default": const("wdt_short"),
        "size_bits": const(1),
        "shift": const(2),
        "allowed": ("wdt_short", "wdt_long"),
        "pack": lambda self, value: {"wdt_short": 0, "wdt_long": 1}.get(value),
        "unpack": lambda self, content: {0: "wdt_short", 1: "wdt_long"}.get(content),
        "help": const("I2c watchdog timer select (human readable): wdt_short: 1.25ms or wdt_long: 40ms"),
    },
    {
        "name": const("press_en"),
        "iu_type": const("config"),
        "container": "REG_PWR_CTRL",
        "default": const(1),
        "size_bits": const(1),
        "shift": const(0),
        "allowed": (0, 1),
        "pack": bypass,
        "unpack": bypass,
        "help": const("Enable/Disable (1/0) pressure sensor"),
    },
    {
        "name": const("temp_en"),
        "iu_type": const("config"),
        "container": "REG_PWR_CTRL",
        "default": const(1),
        "size_bits": const(1),
        "shift": const(1),
        "allowed": (0, 1),
        "pack": bypass,
        "unpack": bypass,
        "help": const("Enable/Disable (1/0) temperature sensor"),
    },
    {
        "name": const("mode"),
        "iu_type": const("config"),
        "container": "REG_PWR_CTRL",
        "default": const("sleep"),
        "size_bits": const(2),
        "shift": const(4),
        "allowed": ("sleep", "forced", "normal"),
        "pack": lambda self, value: {"sleep": 0, "forced": 1, "normal": 3}.get(value),
        "unpack": lambda self, content: {
            0: "sleep",
            1: "forced",
            2: "forced",
            3: "normal",
        }.get(content),
        "help": const("Controls sensor power mode: sleep, forced, normal"),
    },
    {
        "name": const("osr_p"),
        "iu_type": const("config"),
        "container": "REG_OSR",
        "default": const(2),
        "size_bits": const(3),
        "shift": const(0),
        "allowed": (1, 2, 4, 8, 16, 32),
        "pack": pack_log2,
        "unpack": unpack_log2,
        "help": const("Pressure oversampling (human readable). Datasheet 3.4.4"),
    },
    {
        "name": const("osr_t"),
        "iu_type": const("config"),
        "container": "REG_OSR",
        "default": const(1),
        "size_bits": const(3),
        "shift": const(3),
        "allowed": (1, 2, 4, 8, 16, 32),
        "pack": pack_log2,
        "unpack": unpack_log2,
        "help": const("Temperature oversampling (human readable). Datasheet 3.4.4"),
    },
    {
        "name": const("odr_sel"),
        "iu_type": const("config"),
        "container": "REG_ODR",
        "default": const(10),
        "size_bits": const(5),
        "shift": const(0),
        "allowed": (
            5,
            10,
            20,
            40,
            80,
            160,
            320,
            640,
            1280,
            5120,
            10240,
            20480,
            40960,
            81920,
            163840,
            327680,
            655360,
        ),
        "pack": lambda self, value: int(math.log2(value / 5)),
        "unpack": lambda self, content: 2**content * 5,
        "help": const(
            "Output data rate (human readable). Sampling period in ms, which is more natural for event loops. Datasheet 4.3.20"
        ),
    },
    {
        "name": const("short_in"),
        "iu_type": const("config"),
        "container": "REG_CONFIG",
        "default": const(0),
        "size_bits": const(1),
        "shift": const(0),
        "allowed": (0, 1),
        "pack": bypass,
        "unpack": bypass,
        "help": const("short_in"),
    },
    {
        "name": const("iir_filter"),
        "iu_type": const("config"),
        "container": "REG_CONFIG",
        "default": const(0),
        "size_bits": const(3),
        "shift": const(1),
        "allowed": (0, 2, 4, 8, 16, 32, 64, 128),
        "pack": lambda self, value: int(math.log2(value)) if value > 0 else 0,
        "unpack": lambda self, content: int(2**content) if content > 0 else 0,
        "help": const("IIR filter coefficient (human readable). Datasheet  3.4.3"),
    },
    {
        "name": const("cmd"),
        "iu_type": const("command"),
        "container": "REG_CMD",
        "default": const("nop"),
        "size_bits": const(8),
        "shift": const(0),
        "allowed": ("nop", "fifo_flush", "softreset"),
        "pack": lambda self, value: {
            "nop": 0,
            "fifo_flush": 0xB0,
            "softreset": 0xB6,
        }.get(value),
        # This register cannot be reliably read
        "unpack": lambda self, content: "nop",
        "help": const("Receives a command to execute"),
    },
    ##############################
    ###### Info units in Frames
    ##############################
    {
        "name": const("frameiu_press_and_temp"),
        "iu_type": const("frame"),
        "container": "FRAME_PRESS_AND_TEMP",
        "size_bits": const(48),
        "shift": const(0),
        "unpack": compensate_readings,
        "help": const("Pressure (Pa) and temperature (C) compensated values"),
    },
    {
        "name": const("frameiu_temp"),
        "iu_type": const("frame"),
        "container": "FRAME_TEMP",
        "size_bits": const(24),
        "shift": const(0),
        "unpack": compensate_readings,
        "help": const("Temperature (C) compensated value"),
    },
    {
        "name": const("frameiu_press"),
        "iu_type": const("frame"),
        "container": "FRAME_PRESS",
        "size_bits": const(24),
        "shift": const(0),
        "unpack": compensate_readings,
        "help": const("Temperature (C) compensated value"),
    },
    {
        "name": const("frameiu_sensortime"),
        "iu_type": const("frame"),
        "container": "FRAME_SENSORTIME",
        "size_bits": const(24),
        "shift": const(0),
        "unpack": lambda self, content: content & 0xFFFFFF,
        "help": const("Sensor Time"),
    },
    {
        "name": const("frameiu_empty"),
        "iu_type": const("frame"),
        "container": "FRAME_EMPTY",
        "size_bits": const(1),
        "shift": const(0),
        "unpack": lambda self, content: None,
        "help": const("Empty frame dummy response"),
    },
    {
        "name": const("frameiu_error"),
        "iu_type": const("frame"),
        "container": "FRAME_ERROR",
        "size_bits": const(1),
        "shift": const(0),
        "unpack": lambda self, content: None,
        "help": const("Error frame dummy response"),
    },
    {
        "name": const("frameiu_config_change"),
        "iu_type": const("frame"),
        "container": "FRAME_CONFIG_CHANGE",
        "size_bits": const(1),
        "shift": const(0),
        "unpack": lambda self, content: None,
        "help": const("Config frame dummy response, inserted when a change in FIFO config happens"),
    },
)

# Configuration presets
# Most come from the manufacturer (datasheet section 3.5)
# You can add more for different use cases
CONFIG_PRESETS = {
    "handheld_dev_low_power": {
        "press_en": 1,
        "temp_en": 1,
        "mode": "normal",
        "osr_p": 8,
        "osr_t": 1,
        "iir_filter": 2,
        "odr_sel": 80,
    },
    "handheld_dev_dynamic": {
        "press_en": 1,
        "temp_en": 1,
        "mode": "normal",
        "osr_p": 4,
        "osr_t": 1,
        "iir_filter": 4,
        "odr_sel": 20,
    },
    "weather_monitoring": {
        "press_en": 1,
        "temp_en": 1,
        "mode": "forced",
        "osr_p": 1,
        "osr_t": 1,
        "iir_filter": 0,
    },
    "drop_detection": {
        "press_en": 1,
        "temp_en": 1,
        "mode": "normal",
        "osr_p": 2,
        "osr_t": 1,
        "iir_filter": 0,
        "odr_sel": 10,
    },
    "indoor_navigation": {
        "press_en": 1,
        "temp_en": 1,
        "mode": "normal",
        "osr_p": 16,
        "osr_t": 2,
        "iir_filter": 4,
        "odr_sel": 40,
    },
    "drone": {
        "press_en": 1,
        "temp_en": 1,
        "mode": "normal",
        "osr_p": 8,
        "osr_t": 1,
        "iir_filter": 2,
        "odr_sel": 20,
    },
    "indoor_localization": {
        "press_en": 1,
        "temp_en": 1,
        "mode": "normal",
        "osr_p": 1,
        "osr_t": 1,
        "iir_filter": 4,
        "odr_sel": 1280,
    },
    "init": {
        "press_en": 1,
        "temp_en": 1,
        "mode": "normal",
        "osr_p": 1,
        "osr_t": 1,
        "odr_sel": 40,
    },
}
