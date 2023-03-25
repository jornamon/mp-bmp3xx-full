try:
    from __future__ import annotations  # type: ignore
    from typing import Any, Callable, Literal, Generator
except ImportError:
    pass

import time
import struct

from collections import OrderedDict, namedtuple
from micropython import const
from sensor import Sensor, SensorError


class RingBuffer:
    """RingBuffer to maintain FIFO queue data available for the BMP3XXFIFO.
    It discards old data when the buffer is full"""

    def __init__(self, max_size):
        self._max_size = max_size
        self._buffer = [None] * self._max_size
        self._read_index = 0
        self._write_index = 0
        self._discarded_samples = 0
        self._last_discarded = 0

    def full(self):
        result = ((self._write_index + 1) % self._max_size) == self._read_index
        return result

    def empty(self):
        result = self._read_index == self._write_index
        return result

    def size(self):
        result = (self._write_index - self._read_index) % self._max_size
        return result

    def put(self, data):
        self._buffer[self._write_index] = data
        self._write_index = (self._write_index + 1) % self._max_size
        if self._write_index == self._read_index:  # No more room in the queue
            self._read_index = (
                self._read_index + 1
            ) % self._max_size  # Discard old data increasing read pointer too
            self._discarded_samples += 1  # Keep track of the number of discarded samples
            self._last_discarded = time.ticks_ms()

    def get(self):
        if self.empty():
            return None
        data = self._buffer[self._read_index]
        self._read_index = (self._read_index + 1) % self._max_size
        return data

    def reset(self):
        """Resets the buffer deleting all samples"""
        self._read_index = 0
        self._write_index = 0

    def report_discarded(self):
        return (self._discarded_samples, self._last_discarded)

    def status(self):
        print(f"Max size: {self._max_size}")
        print(f"Queue current length (available data): {self.size()}")
        print(f"Read pointer: {self._read_index} Write pointer: {self._write_index}")
        print(f"Empty: {self.empty()} Full: {self.full()}")
        print(self._buffer)


class BMP3XXFIFO:
    """Represents a high level abstraction of the device FIFO.

    This class is intended to allow the user to use the device FIFO from a high level,
    hiding all the details of frame decoding and queue management. The user should be
    able to simple gather continuous data from the device FIFO using the `get` method.

    The `get`method returns a FrameData named tuple that contains pressure, temperature
    and altitude information when applicable or None. The named tuple elements can be
    accessed like this:

    ```
    queue = sensor_instance.fifo_auto_queue()
    data = queue.get()
    data.press  # Pressure
    data.temp  # Temperature
    data.alt  # Altitude
    ```

    It builds on top of the lower level `read_fifo` method from the BMP3XX class and
    performs automatic pulls from the device FIFO when needed.

    Note that it abstracts out some details from the user. If the user needs a more
    precise control of what frames are being received and what to do with them, then
    the `read_fifo`method should be directly used instead and frames processed one
    by one.
    """

    def __init__(self, sensor: BMP3XX, max_frames=100, enable_alt: bool = True) -> None:
        self._sensor = sensor
        self._max_frames = max_frames
        self._rb = RingBuffer(max_frames)
        self._feed_threshold = 10
        self._fifo_odr = self.get_odr_config()
        self._enable_alt = enable_alt
        self._discarded_frames = 0
        self._last_discarded_frame = 0
        # Update device config to be suitable for using auto_queue
        self._sensor.config_write(
            print_result=False,
            mode="normal",
            temp_en=1,
            press_en=1,
            fifo_mode=1,
            fifo_press_en=1,
            fifo_temp_en=1,
            fifo_time_en=0,
        )
        self._sensor._fifo_auto_queue = (
            self  # Update reference to this FIFO queue in the sensor
        )
        self._last_feed = time.ticks_ms()
        self.feed_queue()

    def size(self):
        return self._rb.size()

    def empty(self):
        return self._rb.empty()

    def full(self):
        return self._rb.full()

    def report_discarded(self, do_print=True):
        """Returns number of frames discarded since last report was given and the ticks_ms of the last discard.

        Note that this are discarded frames in the BMP2XXFIFO, not in the device FIFO, you can learn if device
        FIFO is full enabling the corresponding interrupts.

        If the BMP2XXFIFO is left to autofeed itself, it will never discard samples, but you might be loosing
        them in the device FIFO. This tool is useful when there is a mechanism other than autofeed is calling
        `feed_queue`, like interrupts or manual calls under some circumstances.
        """
        discarded = self._rb.report_discarded()
        self._rb._discarded_samples = self._rb._last_discarded = 0

        if not do_print:
            return discarded

        if discarded[0]:
            print(f"{discarded[0]} frames discarded since last report, last discarded {time.ticks_diff(time.ticks_ms(), discarded[1])}ms ago.")  # fmt: skip
        else:
            print("No frames discarded since last report")
        return discarded

    def flush(self):
        """Deletes both device FIFO and BMP3XXFIFO object"""
        self._sensor.fifo_flush()
        self._rb.reset()

    def get_odr_config(self):
        config = self._sensor.config_read("odr_sel", "fifo_subsampling")
        return config["odr_sel"] * config["fifo_subsampling"]

    def get(self):
        """Returns frame data and handles queue autofeed for the user"""
        current_size = self.size()
        time_since_last_feed = time.ticks_diff(time.ticks_ms(), self._last_feed)

        if (current_size == 0 and time_since_last_feed > self._fifo_odr) or (
            current_size < self._feed_threshold
            and time_since_last_feed > self._fifo_odr * self._feed_threshold / 2
        ):
            self.feed_queue()
            self._sensor._debug_print('Auto feeding queue')  # fmt: skip
        else:
            self._sensor._debug_print("Skip autofeeding", 'Size:', current_size, 'dt:', time_since_last_feed, 'FIFO ODR:', self._fifo_odr)  # fmt: skip

        if self.empty():
            self._sensor._debug_print('Queue definitely empty, returning None')  # fmt: skip
            return None
        else:
            return self._rb.get()

    def feed_queue(self):
        """Reads FIFO, decodes Frames and update FIFO QUEUE accordingly.

        Frames that are not useful are simply ignored.
        """
        for frame in self._sensor.fifo_read():
            if frame.type == "FRAME_PRESS_AND_TEMP":
                press = frame.payload[0]
                temp = frame.payload[1]
                alt = (
                    self._sensor.altitude_from_pressure(press)
                    if self._enable_alt
                    else None
                )
                self._rb.put(BMP3XX.sensor_data(press, temp, alt))
            elif frame.type == "FRAME_PRESS":
                press = frame.payload
                temp = None
                alt = (
                    self._sensor.altitude_from_pressure(press)
                    if self._enable_alt
                    else None
                )
                self._rb.put(BMP3XX.sensor_data(press, temp, alt))
            elif frame.type == "FRAME_TEMP":
                press = None
                temp = frame.payload
                alt = None
                self._rb.put(BMP3XX.sensor_data(press, temp, alt))
            elif frame.type == "FRAME_CONFIG_CHANGE":
                # Update FIFO ODR for autofeed calcs if FIFO CONFIG CHANGE is detected
                self._fifo_odr = self.get_odr_config()
                self._sensor._debug_print('feed_queue: * Config change detected, updating ODR to', self._fifo_odr)  # fmt: skip

        self._last_feed = time.ticks_ms()
        self._sensor._debug_print("feed_queue: Feeding queue")  # fmt: skip


class BMP3XX(Sensor):
    """BMP3XX sensor, this class constructs the internal structure of the BMP3XX, no serial communication implemented"""

    STANDARD_SEA_LEVEL_PRESSURE_PA = const(101325)  # Standard sea level pressure
    frame_header_size = const(1)  # Size in bytes of a frame header
    frame_header_mask = const(0xFF)  # Mask the length of a frame header
    frame_content = namedtuple("Frame", ["type", "payload"])
    sensor_data = namedtuple("SensorData", ["press", "temp", "alt"])

    def __init__(self, bus, debug_print=False, **kwargs) -> None:
        super().__init__(bus, debug_print, **kwargs)

        # Finish serial bus setup
        if bus.__class__.__name__ in ("I2C", "SoftI2C"):
            self._bus._i2c_addr = kwargs.get("i2c_addr", 0x77)

        self.name = "BMP3XX"
        self.help = "BMP3XX pressure and temperature sensor"
        self._endianness: Literal[
            "big", "little"
        ] = "little"  # To pack and unpack bytes <-> ints

        # Calibrate later for better altitude accuracy
        self._sea_level_pressure = BMP3XX.STANDARD_SEA_LEVEL_PRESSURE_PA

        # Initializes a FIFO mirror buffer to dump sensor FIFO into during burst reads for later processing
        self._fifo_mirror = bytearray(512 + 4)
        self._fifo_auto_queue: BMP3XXFIFO | None = (
            None  # Reference to BMP3XXFIFO object if exists
        )

        # Call several methods to initialize the sensor correctly
        self._init_data_structure()
        self._check_sensor()  # Check for sensor presence reading the chip ID register
        self._get_calibration_data()  # Get and store calibration coefficients for future reading compensations
        self.apply_config_preset(
            "init"
        )  # Basic config, bmp3xx boots up with sensors disabled.

    # Some properties to allow ultra basic usage
    @property
    def press(self):
        return self.data_read("press").get("press")

    @property
    def temp(self):
        return self.data_read("temp").get("temp")

    @property
    def alt(self):
        return self.data_read("altitude").get("altitude")

    @property
    def all(self):
        """All available sensor data as a property"""
        return self._get_all()

    def _get_all(self, current_config: dict | None = None, enable_alt: bool = True):
        """Provides all available data as a SensorData named tuple.

        The result provided depend on the current sensor configuration (press_en and temp_en).

        Args:
            current_config (dict | None, optional): Current configuration passed by the caller to
                spare an additional config read. Defaults to None, which makes ir read the current config.
            enable_alt (bool, optional): Whether to calculate and provide the altitude. Defaults to True.

        Returns:
            SensorData: named tuple with fields `press`, `temp` and `alt`.
        """
        if current_config is None:
            current_config = self.config_read("press_en", "temp_en", "mode")

        press_and_temp = self.data_read("press_and_temp")["press_and_temp"]

        press = press_and_temp[0] if current_config["press_en"] else None
        temp = press_and_temp[1] if current_config["temp_en"] else None
        alt = (
            self.altitude_from_pressure(press)
            if press is not None and enable_alt
            else None
        )

        sd = BMP3XX.sensor_data(press, temp, alt)

        return sd

    def altitude_from_pressure(self, press):
        return 44307.69 * (1 - (press / self._sea_level_pressure) ** 0.190284)

    def _wait_data_ready(self, current_config: dict | None = None):
        """Waits until new sensor data is available.

        Args:
            current_config (dict | None, optional): Current configuration passed by the caller to
                spare an additional config read. Defaults to None, which makes ir read the current config.
        """
        if current_config is None:
            current_config = self.config_read("press_en", "temp_en", "mode")

        if current_config.get("mode") == "sleep":
            # Nothing to wait for
            return

        enabled = [current_config.get("press_en"), current_config.get("temp_en")]
        while True:
            drdy = [value for value in self.data_read("drdy_press", "drdy_temp").values()]
            # print('drdy', drdy)
            condition = [not enabled[0] or drdy[0], not enabled[1] or drdy[1]]
            # print('Condition', condition)  # DEBUG
            if all(condition):
                break
            time.sleep_ms(5)

    def forced_read(self):
        """Reads all available information from the sensor making sure it's a fresh sample.

        By default, sensor reads return the contents of the last sample available in the device.
        Usually this is what you want, specially if you are working in normal mode and and the
        sensor ODR is appropriate for the polling rate. In this case, the read is non-blocking
        and faster. It doesn't check if data is new and returns immediately. In some cases, this may
        lead to returning the same sample in consecutive sensor readings. If this is not acceptable
        for your application you can use this method to force the driver to return data from the
        last sample, doing a blocking wait until fresh data is available.

        This method should also be used when working in forced mode (the device sleeps until it's
        asked for another forced measure) unless you plan to handle manually the transitions
        between forced and sleep modes. See Datasheet 3.3 Power Modes for details.

        Returns:
            SensorData: Named tuple with all available information from the sensor.
                Fields are: press, temp, alt
        """
        current_config = self.config_read("press_en", "temp_en", "mode")
        # print('Entering forced_read with config', current_config)  # DEBUG
        if current_config["mode"] in ("normal", "forced"):
            # print('forced_read mode', mode)  # DEBUG
            self._wait_data_ready(current_config)
            return self._get_all(current_config=current_config)
        else:
            # print('forced_read mode', mode)  # DEBUG
            self.config_write(mode="forced", print_result=False)
            self._wait_data_ready(current_config=current_config.update(mode="forced"))
            return self._get_all(current_config=current_config)

    def softreset(self):
        """Resets de device, user config is overwritten with default state"""
        self._bus._write_reg(0x7E, 0xB6)

    def fifo_flush(self):
        """Clears all data in FIFO, but does not change FIFO CONFIG"""
        self._bus._write_reg(0x7E, 0xB0)

    def fifo_length(self) -> int:
        """Returns current FIFO length in bytes (0-511)"""
        data = self.data_read("fifo_length")
        return data["fifo_length"]

    def _fifo_sync(self, num_bytes: int = 0) -> int:
        """Reads FIFO content and places it into the fifo_mirror buffer to be processed.

        This low level function is not part of the API and it's supposed to be used by other higher level
        functions that process fifo content and return useful data, but if the user is interested in
        reading raw fifo content, he can use this functions and inspect `self._fifo_mirror`.

        Args:
            num_bytes (int, optional): number of bytes to be read from FIFO. Defaults to 0,
                which means reading all bytes available in the fifo.

        Returns:
            int: Number of bytes read from fifo and written to fifo_mirror.

        """
        if num_bytes == 0:
            # Read all FIFO
            bytes_to_read = self.fifo_length() + 4
        else:
            bytes_to_read = num_bytes + 4

        buffer = memoryview(self._fifo_mirror)[0:bytes_to_read]
        self._bus._read_reg_into(0x14, buffer)
        return bytes_to_read

    def fifo_debug(self, num_bytes: int = 0) -> None:
        """Reads FIFO parses the frames and print results and stats for debugging purposes

        Args:
            num_bytes (int, optional): _description_. Defaults to 0, which means reading all available
                data in the FIFO
        """
        legend = OrderedDict()
        stats = OrderedDict()
        legend.update(
            {
                d[0]: d[1]
                for d in (
                    (frame.name, frame.representation)
                    for frame in self._sensor_frames.values()
                )
            }
        )
        stats.update(
            {key: 0 for key in (frame.name for frame in self._sensor_frames.values())}
        )
        last_byte = self._fifo_sync(num_bytes)
        stats.update(
            {"INVALID": 0, "TOTAL ERRORS": 0, "TOTAL FRAMES": 0, "TOTAL BYTES": last_byte}
        )
        i = 0
        print("FIFO frames representation (see legend below):")
        while i < last_byte:
            header = self._fifo_mirror[i]
            if header in self._sensor_frames:
                frame = self._sensor_frames[header]
                print(frame.representation, end="")
                stats[frame.name] += 1
                stats["TOTAL FRAMES"] += 1
                stats["TOTAL ERRORS"] += frame.error_count
                i += frame.size_bytes
            else:
                # Unrecognized frame
                print("!", end="")
                stats["TOTAL ERRORS"] += 1
                stats["INVALID"] += 1
                i += 1

        print()
        self._print_configs(FIFO_STATS=stats, LEGEND=legend)

    def fifo_read(self, num_bytes: int = 0) -> Generator:
        """Read device FIFO and process the data, returning a generator with the decoded frames to be consumed.

        Args:
            num_bytes (int, optional): Number of bytes to be read. Defaults to 0, which means reading all FIFO
            available content.

        Yields:
            Generator: a Named Tuple containing two fields:
                `type`: with the type of frame which coincides with the `name` field of the Frame class instance.
                `payload`: the information available. The information available depends on the type of frame
                    so caller must check the type to interpret the information correctly.
        """
        last_byte = self._fifo_sync(num_bytes)
        i = 0

        while i < last_byte:
            header = self._fifo_mirror[i]
            if header in self._sensor_frames:
                frame = self._sensor_frames[header]
                frame_content = self._fifo_mirror[i + 1 : i + frame.size_bytes]
                frame_value = int.from_bytes(frame_content, self._endianness)
                # print('frame_content', frame_content, len(frame_content), 'value', frame_value)
                # frame._pretty_print()
                frame_payload = frame.read(frame_value)
                fc = BMP3XX.frame_content(
                    frame.name, frame_payload.popitem()[1]
                )  # Just take the value, not the dict
                i += frame.size_bytes
            else:
                # Unrecognized frame
                fc = BMP3XX.frame_content("FRAME_INVALID", None)
                i += 1
            # print('fc',fc)
            yield fc

    def fifo_auto_queue(self, max_frames=100):
        """Returns new or existing  BMP3XXFIFO object.

        This object allows the user to get info from the FIFO without dealing with any details.
        See BMP3XXFIFO for more information.
        """
        if self._fifo_auto_queue:
            return self._fifo_auto_queue
        else:
            return BMP3XXFIFO(self, max_frames)

    def calc_odr(self, explain=True, **kwargs) -> tuple[float, Any]:
        """Calculates measure conversion time in ms.

        With no args, calculates it from current sensor config.
        With args provided, it calculates it from them (as an estimation tool for the user).

        This can be usefull to see if certain configuration is compatible with
        a desired Output Data Rata (ODR) or to estimate the conversion time
        in forced mode.
        """
        mandatory_args = ("press_en", "temp_en", "osr_p", "osr_t")
        if not kwargs:
            config = self.config_read(
                "press_en", "temp_en", "osr_p", "osr_t", "odr_sel", "fifo_subsampling"
            )
            press_en = config["press_en"]
            temp_en = config["temp_en"]
            osr_p = config["osr_p"]
            osr_t = config["osr_t"]
            odr_sel = config["odr_sel"]
            fifo_subsampling = config["fifo_subsampling"]
        else:
            if not all(arg in kwargs for arg in mandatory_args):
                raise SensorError(
                    "Not enough argument provided to calculate ODS. "
                    "This function must be called without arguments, to calculate ODR from current Sensor config "
                    "or with all of this kwargs: 'press_en', 'temp_en', 'osr_p', 'osr_t'"
                )
            else:
                press_en = kwargs["press_en"]
                temp_en = kwargs["temp_en"]
                osr_p = kwargs["osr_p"]
                osr_t = kwargs["osr_t"]
                odr_sel = None
                fifo_subsampling = None

        conversion_time_ms = (
            0.234 + press_en * (0.392 + osr_p * 2.020) + temp_en * (0.163 + osr_t * 2.020)
        )
        allowed_odr = self._sensor_info_units["odr_sel"].allowed
        min_odr = next((x for x in filter(lambda x: x > conversion_time_ms, allowed_odr)))

        if explain:
            print(f"Calculated conversion time is {conversion_time_ms:.3f} ms")
            print(f"Minimum ODR selected for this config should be {min_odr}")
            print(f"Current ODR is {odr_sel}")
            if odr_sel is not None:
                print(f"Current FIFO ODR {odr_sel * fifo_subsampling}")

        return (conversion_time_ms, odr_sel)

    def calibrate_altimeter(self, **calib_info) -> None:  # type: ignore
        """Calibrates the altimeter based in known local altitude or sea level pressure.

        Needs one and only one of the arguments to use one of the two calibration methods
        (known local altitude or known local sea level pressure).
        Usually local altitude is easier to know.
        Note that local sea level pressure is NOT the local pressure at current altitude,
        but the pressure that would be measured at sea level. It can be obtained in some weather sites.
        Units are meters or Pascals (carful, most weather sites provide hPa or mbar)

        Args:
            local_alt (float, optional): the known local altitude in meters. Defaults to None.
            local_press (float, optional): the known local *sea level* pressure in Pascals. Defaults to None.

        Raises:
            SensorError: If wrong argument are provided.
        """
        if len(calib_info) == 1 and any(
            ("local_alt" in calib_info, "local_press" in calib_info)
        ):
            if "local_press" in calib_info:
                self._sea_level_pressure = calib_info["local_press"]
                self._debug_print(f"calibrate_altimeter: Updating local sea level pressure with {calib_info['local_press']} Pa")  # fmt: skip
            else:
                pressure = self.data_read("press").get("press")
                local_slp = pressure / (1 - calib_info["local_alt"] / 44307.69) ** (
                    5.2553
                )
                self._sea_level_pressure = local_slp
                self._debug_print(f"calibrate_altimeter: Updating local sea level pressure with {local_slp}Pa, based in local known altitude {calib_info['local_alt']}m")  # fmt: skip
        else:
            raise SensorError(
                "To calibrate the altimeter you must provide one and only one of these keyword arguments: \n"
                "local_alt = the known local altitude in meters.\n"
                "local_press = the known local *sea level* pressure in Pascals.\n"
                "(local sea level pressure is NOT the local pressure at current altitude.\n"
                "Example: `Sensor.calibrate_altimeter(local_alt=450)`"
            )

    def _check_sensor(self):
        """Checks for BMP3XX sensor presence"""
        chip_id = self.data_read("chip_id").get("chip_id")
        if chip_id not in (0x50, 0x60):
            raise SensorError(
                f"No BMP3XX sensor detected (chips IDs 0x50 or 0x60), found {chip_id}. "
                "Review cabling and Pin assignments"
            )

    def _get_calibration_data(self):
        """Gets calibration data stored in the BMP390 to translate adc valued into actual pressure and temperature. Datasheet 8.4, 8.5 and 8.6"""
        coeffs = self._bus._read_reg(0x31, 21)
        coeffs = struct.unpack("<HHbhhbbHHbbhbb", coeffs)
        self._temp_calib = (
            coeffs[0] / 2**-8.0,  # T1
            coeffs[1] / 2**30.0,  # T2
            coeffs[2] / 2**48.0,  # T3
        )
        self._pressure_calib = (
            (coeffs[3] - 2**14.0) / 2**20.0,  # P1
            (coeffs[4] - 2**14.0) / 2**29.0,  # P2
            coeffs[5] / 2**32.0,  # P3
            coeffs[6] / 2**37.0,  # P4
            coeffs[7] / 2**-3.0,  # P5
            coeffs[8] / 2**6.0,  # P6
            coeffs[9] / 2**8.0,  # P7
            coeffs[10] / 2**15.0,  # P8
            coeffs[11] / 2**48.0,  # P9
            coeffs[12] / 2**48.0,  # P10
            coeffs[13] / 2**65.0,  # P11
        )

    def _check_sensor_config(self, applied_config: dict):
        """Implements BMP3XX config error check."""

        conf_err = self.data_read("conf_err").get("conf_err")
        self._debug_print("_check_sensor_config:", conf_err)  # fmt: skip
        if conf_err:
            raise SensorError(
                "The requested configuration has triggered an error in the Sensor. "
                "Consider applying config parameter in smaller groups to detect the conflicting values. "
                "Most common cause is selecting temp and press oversampling config that takes more time "
                "than the selected Output Data Rate (ODR). You can use the method `calc_odr` to check beforehand."
            )
