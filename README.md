# Micropython fully-featured BMP3XX driver

The primary goals of this driver are:

1. Provide Micropython users with **each and every feature** the BMP3XX offers, on par with the C drivers provided by the OEM.
2. Provide the user a set of **tools** that allow him to tinker with the device and make it easy and fun to **discover** all its frequently unused features.
3. Provide a base code that can be **reused** to implement drivers for similar devices.

This driver **does not** intend to be small or super memory efficient. This doesn't mean that it's going to be inefficient on purpose, I'd like to gradually optimize it, but it will always favor the three primary goals. If you are working with a board with very limited resources or you know for sure that you'll be only using a small subset of the device features, there might be better options out there. In fact, it could be argued that this is not a bare driver, because it contains some tools that usually are outside the traditional scope of a driver.

📝 *At this moment, there is still debug code inside. It will be cleaned up in the near (?) future.*

## Driver features

- Complete control over any parameter of the device through the general methods `config_read()`, `config_write()` and `data_read()`. Configuration changes are displayed in a friendly form if needed. The user always interacts with the human-friendly values of the parameters.
- Complete FIFO support, with access to several levels of abstraction depending on the user needs, reaching up to a fully automated FIFO queue management. More on FIFO below.
- I2C and SPI support.
- Complete control over interrupts, including advanced configuration like latching and non-latching, level, etc.
- Access to basic info as properties for super easy usage and methods that simplify access to common tasks that could also be achieved through the general manipulation tools.
- Sane default values for all InfoUnits that let you focus on only the parameters you want to modify.
- Set of configuration templates for several applications that can be applied to the device with one command. The user can easily add more.
- Friendly error messages and parameters explanations when needed, for example, it indicates which values are available for a parameter when trying to configure it with an invalid value.

## Getting started

The driver is composed of three files: `sensor.py`, `bmp3xx.py` and `bmp3xx_data_structure.py`. All three must be copied to the board (`/` or `/lib`) in order for it to work.

The best way to start is by following the provided [tutorial](./tutorial.md) and [examples](./examples). Although it's still a work in progress, the code is also reasonably well documented, so it would be easy to take a look if you want to check out how it works or all available options that may not be covered in the examples.

## Driver structure

The driver is organized to try to reuse as much code (and tools) as possible for other drivers and separate the device data structures from the logic of the driver. This is why it's divided in three files with three different objectives:

### sensor.py

This file aims to be device agnostic. Theoretically, all it's code and tools for reading and writing configuration and data could be reused for another driver, or at least for similar devices.

This file contains all important functionality of the driver, leaving outside only specific aspects of the device that cannot be abstracted or features that are device specific.

There are several classes here:

- `Sensor`: Represents the sensor itself and provides most of the functionality that the user sees.
- `InfoUnit`: Represents the basic piece of information inside the driver, it can be data that can be read (like *pressure*), or some configuration that can be read or written (like *temperature oversampling*). All the tools for reading and writing data or configuration from/to the device, manipulate this `InfoUnits`. The `InfoUnits` of the device are defined in the `bmp3xx_data_structure.py` file and all have more or less friendly names that follows almost always the datasheet.
- `Container` and its subclasses `Register` and `Frame`. Represent the register, frame or whatever higher order data structure that contain the InfoUnit. While a Register can be exactly a register on the device, it might not. The class is a little bit more abstract concept than a physical register, and can, for example, span several registers if needed, depending on how the `InfoUnits` are stored.
- `BUS` and its subclasses `I2CBUS` and `SPIBUS` are a component of the `Sensor` class and provide actual read / write operations over the serial BUS. Ideally this could be expanded to other types of buses.

`data_read`, `config_read` and `config_write` can do all basic interfacing with the device. While it might look a little awkward for the main tools to receive kwargs and to return dictionaries from which you have to extract the actual data, it is indeed intentional. This scheme allow the driver and the user to manipulate any InfoUnit defined in the data_structure, and *any number* of them with the same tool. If you are implementing a small subset of the sensor features, one method for each is fine, but when you try to manipulate many parameters the proliferation of specific methods can become annoying, you quickly find yourself with methods like *'set_int_fifo_wtm'*.

The most used features can be easily wrapped in the driver (see `bmp3xx.py` for examples) or even by the user, but you are still able to manipulate any parameter of the device.

For example, you can set the data ready interrupt with `sensor.config_write(drdy_en=1)` or read it by `sensor.config_read('drdy_en')`, but if it's important to you, you can still wrap it with a few lines of code:

```python
def data_ready_int(sensor, value = None):
    if value is None:
        return sensor.config_read('drdy_en')['drdy_en']
    else:
       sensor.config_write(drdy_en=value) 
```

### bmp3xx.py

This file contains all code and logic specific to the BMP3XX. A good deal of methods present in this file perform functions that can also be achieved through the general data and configuration manipulation tools present in `sensor.py` but make it easier for the user.

Examples are the properties `press`, `temp`, `alt` and `all`, that provide basic readings from the sensor. Methods like `calibrate_altimeter()` or `calc_odr()` provide tools that make the sensor easier to use.

One of the nicest (and less covered by drivers) features of this device is the 512-byte FIFO it has. The class `BMP3XXFIFO` and some helping methods are nice tools that make using the device FIFO a breeze. It's covered below.

### bmp3xx_data_structure.py

This file contains the data structure of the information contained in the BMP3XX. The information there basically represents what information is stored in the device, where it is stored, the allowed values and, very importantly, how to *pack* or *unpack* human readable values to/from the actual bytes that are stored in the device.

There is little logic in this file, apart from the methods that are used to convert human-friendly values for the parameter to/from the values that are actually stored in the device.

The information contained in this file is used at boot up to generate the data structures for the driver to function.

The configuration templates are also stored here.

## The BMP3XX FIFO

I wrote this driver mainly because I only found C drivers that truly covered this functionality, and I thought it was a pity because for me, it's the best feature of the device, so I wanted it to be available to all Micropython users.

There are many examples of underutilizing this device here and there, but with a driver that fully covers the device features (this one) and devoting some time to study the datasheet (something I strongly recommend to anyone wanting to go beyond basics with this device) you can do pretty nice things with this sensor.

The FIFO is highly configurable, and offers a lot of nice features: interrupts for FIFO full or reaching a certain watermark, deciding which information will go in the FIFO frames, FIFO subsampling, choosing the sample discarding policy, etc. I think **the FIFO is very interesting for Micropython users**. For example, in **high sampling rate applications**, ideally one wants to process every single sample, especially if you apply filters that rely on the samples to be equally spaced in time. In Micropython, processes like *file I/O* or *garbage collection* can take enough time to make you miss samples. Using the device FIFO almost guarantees that you will be able to process all the samples.

Another interesting use case is **ultra low power applications**. If the device acting as a weather station (usually very low rate sampling), one can leverage the device FIFO and store there samples and only wake up the main MCU when the FIFO is full or almost full, batch process all the samples and then go back to sleep. This way, depending on the application, you can go 1/100 times less through the wake-sleep cycle.

In general, it also offers you greater **flexibility** on how and when you want to process your samples in complex applications.

The FIFO can be accessed in several ways, depending on the needs of the user:

1. By simply reading the `fifo_data` InfoUnit, like `sensor.data_read('fifo_data')`. This may work because of how the device handles partial transmissions and retransmissions of frames, but this **should not be the primary way to access the FIFO**.
2. The driver has a fifo mirror where it dumps the contents of the device FIFO. The method `_fifo_sync()`, while not part of the public API, copies the contents of the driver FIFO to the mirror, which can be inspected to analyze the raw content. Again **this isn't the intended way to access the FIFO**.
3. `fifo_debug()`, while being for debugging, it can be very handy when learning how the FIFO works, especially to see how the device handles config changes, errors, partial transmissions and FIFO over reads. It shows a graphic representation of the type of frames inside the FIFO.
4. `fifo_read()` offers the first proper way to access the FIFO. It reads the FIFO frames, decodes them and offer them to the user as a generator. Each frame is yielded as a namedtuple with two fields: `type`, with the type of frame and `payload`, which contains the information available. The information available depends on the type of frame and the driver does not discard any frame, not even special frames, like empty frames or config change frames, so caller must check the type to interpret the information correctly. This method offers the user almost complete control of the frame processing while sparing him from the actual decoding, but the user must also actively manage the FIFO and decide what to do with each frame.
5. The `fifo_auto_queue()` method offers the highest level of abstraction, making it ultra simple for the user to use the device FIFO. It returns a `BMP3XXFIFO` object that handles the FIFO for the user.

This `BMP3XXFIFO` class is intended to allow the user to use the device FIFO from a high level, hiding all the details of frame decoding and queue management. The user should be able to simply gather continuous data from the device FIFO using the `get` method.

The `get()` method returns a `FrameData` named tuple that contains pressure, temperature
and altitude information when applicable or `None`. The named tuple elements can be
accessed like this:

```python
queue = sensor_instance.fifo_auto_queue()
data = queue.get()
data.press  # Pressure
data.temp  # Temperature
data.alt  # Altitude
```

It builds on top of the lower level `fifo_read` method from the BMP3XX class and
performs automatic pulls from the device FIFO when needed. It also discard all special frames.

Note that it abstracts out some details from the user. If the user needs a more
precise control of what frames are being received and what to do with them, then
the `fifo_read` method should be directly used instead and frames processed one
by one.

The `BMP3XXFIFO` object keeps a basic record of discarded frames, in case the buffer overflows. Read the class docstrings for more details on how to use a `BMP3XXFIFO` object.

## Reusing this driver to expand it to other devices

This driver use written with reusability in mind. All the heavy lifting is done in the `sensor.py` file which is device agnostic and can be used with other devices. All enhancements to this file could be potentially shared by many drivers.

Building a driver for a new (similar enough) device would consist in:

1. Replicate the data structure of the device in the `newdevice_data_structure.py` file. While this might be a little bit tedious, it's quite methodic. The only thing needed is reading carefully the datasheet and translating it correctly to the file. Even someone with no programming experience could have a shot at doing this, being the methods to *pack* and *unpack* information the only coding needed, and many can be derived from the ones in the bmp3xx_data_structure.
2. Build the corresponding `newdevice.py` file and class, which inherits from the `Sensor` class. This file can be truly super basic for the driver to work, managing some basic specifics of the device. If you check the `bmp3xx.py` file you will see that, besides the FIFO management, the methods inside the `BMP3XX` class are mainly simplifying wrappers around things that can be also done using `data_read`, `config_read` and `config_write`.

## Available info Units

This is the complete list of available InfoUnits. Config InfoUnits can be read (`config_read`) or written (`config_write`). Data InfoUnits can only be read with `data_read`. A little bit further down the whole list with a brief description, allowed values (when applicable) and a some extra info. For further explanations check the device datasheet.

### Config Info units

```python
'fifo_water_mark', 'fifo_mode', 'fifo_stop_on_full', 'fifo_time_en', 'fifo_press_en', 'fifo_temp_en', 'fifo_subsampling', 'data_select', 'int_od', 'int_level', 'int_latch', 'fwtm_en', 'ffull_en', 'int_ds', 'drdy_en', 'spi3', 'i2c_wdt_en', 'i2c_wdt_sel', 'press_en', 'temp_en', 'mode', 'osr_p', 'osr_t', 'odr_sel', 'short_in', 'iir_filter'
```

### Data Info units

```python
'chip_id', 'rev_id', 'fatal_err', 'cmd_err', 'conf_err', 'cmd_rdy', 'drdy_press', 'drdy_temp', 'press_and_temp', 'press', 'temp', 'press_and_temp_adc', 'altitude', 'sensortime', 'por_detected', 'itf_act_pt', 'fwm_int', 'ffull_int', 'drdy', 'fifo_length', 'fifo_data'
```

 ***Information Unit***

- Name: chip_id
- Type: data
- Allowed: N/A
- Register: REG_CHIP_ID
- Help Chip ID stored in NVM

 ***Information Unit***

- Name: rev_id
- Type: data
- Allowed: N/A
- Register: REG_REV_ID
- Help ASIC mask revision (minor)

 ***Information Unit***

- Name: fatal_err
- Type: data
- Allowed: N/A
- Register: REG_ERR_REG
- Help Fatal error bit

 ***Information Unit***

- Name: cmd_err
- Type: data
- Allowed: N/A
- Register: REG_ERR_REG
- Help Command error bit

 ***Information Unit***

- Name: conf_err
- Type: data
- Allowed: N/A
- Register: REG_ERR_REG
- Help Configuration error bit

 ***Information Unit***

- Name: cmd_rdy
- Type: data
- Allowed: N/A
- Register: REG_STATUS
- Help Command ready bit, 1 if ready to accept new command

 ***Information Unit***

- Name: drdy_press
- Type: data
- Allowed: N/A
- Register: REG_STATUS
- Help Pressure data ready bit, 1 if pressure data is ready to be read.

 ***Information Unit***

- Name: drdy_temp
- Type: data
- Allowed: N/A
- Register: REG_STATUS
- Help Temperature data ready bit, 1 if temperature data is ready to be read.

 ***Information Unit***

- Name: press_and_temp
- Type: data
- Allowed: N/A
- Register: REG_DATA_PRESS_AND_TEMP
- Help Pressure (Pa) and temperature (C) compensated values.

 ***Information Unit***

- Name: press
- Type: data
- Allowed: N/A
- Register: REG_DATA_PRESS_AND_TEMP
- Help Pressure (Pa) compensated value.

 ***Information Unit***

- Name: temp
- Type: data
- Allowed: N/A
- Register: REG_DATA_PRESS_AND_TEMP
- Help Temperature (C) compensated value.

 ***Information Unit***

- Name: press_and_temp_adc
- Type: data
- Allowed: N/A
- Register: REG_DATA_PRESS_AND_TEMP
- Help Pressure and temperature ADC raw values.

 ***Information Unit***

- Name: altitude
- Type: data
- Allowed: N/A
- Register: REG_DATA_PRESS_AND_TEMP
- Help Altitude in meters. Should calibrate sensor before reading altitude.

 ***Information Unit***

- Name: sensortime
- Type: data
- Allowed: N/A
- Register: REG_SENSORTIME
- Help Sensor Time

 ***Information Unit***

- Name: por_detected
- Type: data
- Allowed: N/A
- Register: REG_EVENT
- Help 1 after device power up or softreset. Cleared on read

 ***Information Unit***

- Name: itf_act_pt
- Type: data
- Allowed: N/A
- Register: REG_EVENT
- Help 1 when serial interface transaction occurs during a pressure or temperature conversion. Cleared on read

 ***Information Unit***

- Name: fwm_int
- Type: data
- Allowed: N/A
- Register: REG_INT_STATUS
- Help FIFO watermark interrupt status

 ***Information Unit***

- Name: ffull_int
- Type: data
- Allowed: N/A
- Register: REG_INT_STATUS
- Help FIFO full interrupt status

 ***Information Unit***

- Name: drdy
- Type: data
- Allowed: N/A
- Register: REG_INT_STATUS
- Help Data Ready interrupt status

 ***Information Unit***

- Name: fifo_length
- Type: data
- Allowed: N/A
- Register: REG_FIFO_LENGTH
- Help FIFO length in bytes 0-511 (9-bits)

 ***Information Unit***

- Name: fifo_data
- Type: data
- Allowed: N/A
- Register: REG_FIFO_DATA
- Help FIFO 7 bytes of raw data (frames), should not be primary FIFO data access

 ***Information Unit***

- Name: fifo_water_mark
- Type: config
- Allowed: range(0, 512)
- Register: REG_FIFO_WTM
- Help FIFO watermark level in bytes 0-511 (9-bit)

 ***Information Unit***

- Name: fifo_mode
- Type: config
- Allowed: (0, 1)
- Register: REG_FIFO_CONFIG_1
- Help Enables/Disables (1/0) FIFO

 ***Information Unit***

- Name: fifo_stop_on_full
- Type: config
- Allowed: (0, 1)
- Register: REG_FIFO_CONFIG_1
- Help FIFO full behavior, 0: discard old samples, 1: discard new samples

 ***Information Unit***

- Name: fifo_time_en
- Type: config
- Allowed: (0, 1)
- Register: REG_FIFO_CONFIG_1
- Help Enable return of sensortime frames in FIFO reads

 ***Information Unit***

- Name: fifo_press_en
- Type: config
- Allowed: (0, 1)
- Register: REG_FIFO_CONFIG_1
- Help Enable return of pressure frames in FIFO reads

 ***Information Unit***

- Name: fifo_temp_en
- Type: config
- Allowed: (0, 1)
- Register: REG_FIFO_CONFIG_1
- Help Enable return of temperature frames in FIFO reads

 ***Information Unit***

- Name: fifo_subsampling
- Type: config
- Allowed: (1, 2, 4, 8, 16, 32, 64, 128)
- Register: REG_FIFO_CONFIG_2
- Help FIFO subsampling factor (human readable). Datasheet 3.6.2

 ***Information Unit***

- Name: data_select
- Type: config
- Allowed: ('filtered', 'unfiltered')
- Register: REG_FIFO_CONFIG_2
- Help FIFO data source (human readable), filtered or unfiltered

 ***Information Unit***

- Name: int_od
- Type: config
- Allowed: ('push-pull', 'open-drain')
- Register: REG_INT_CTRL
- Help Interrupt output type (human readable), push-pull or open-drain

 ***Information Unit***

- Name: int_level
- Type: config
- Allowed: (0, 1)
- Register: REG_INT_CTRL
- Help Interrupt active level 1: high, 0: low

 ***Information Unit***

- Name: int_latch
- Type: config
- Allowed: (0, 1)
- Register: REG_INT_CTRL
- Help Enable interrupt latching for INT pin and INT_STATUS register. Datasheet 3.7.2

 ***Information Unit***

- Name: fwtm_en
- Type: config
- Allowed: (0, 1)
- Register: REG_INT_CTRL
- Help Enable FIFO watermark level reached interrupt (INT pin and INT_STATUS)

 ***Information Unit***

- Name: ffull_en
- Type: config
- Allowed: (0, 1)
- Register: REG_INT_CTRL
- Help Enable FIFO full interrupt (INT pin and INT_STATUS)

 ***Information Unit***

- Name: int_ds
- Type: config
- Allowed: (0, 1)
- Register: REG_INT_CTRL
- Help int_ds 0: low, 1: high

 ***Information Unit***

- Name: drdy_en
- Type: config
- Allowed: (0, 1)
- Register: REG_INT_CTRL
- Help Enable data ready interrupt (INT pin and INT_STATUS)

 ***Information Unit***

- Name: spi3
- Type: config
- Allowed: ('spi3', 'spi4')
- Register: REG_IF_CONF
- Help Configure spi interface mode (human readable), spi4 or spi3 for 4-wire and 3-wire configurations

 ***Information Unit***

- Name: i2c_wdt_en
- Type: config
- Allowed: (0, 1)
- Register: REG_IF_CONF
- Help Enable i2c watchdog timer

 ***Information Unit***

- Name: i2c_wdt_sel
- Type: config
- Allowed: ('wdt_short', 'wdt_long')
- Register: REG_IF_CONF
- Help I2c watchdog timer select (human readable): wdt_short: 1.25ms or wdt_long: 40ms

 ***Information Unit***

- Name: press_en
- Type: config
- Allowed: (0, 1)
- Register: REG_PWR_CTRL
- Help Enable/Disable (1/0) pressure sensor

 ***Information Unit***

- Name: temp_en
- Type: config
- Allowed: (0, 1)
- Register: REG_PWR_CTRL
- Help Enable/Disable (1/0) temperature sensor

 ***Information Unit***

- Name: mode
- Type: config
- Allowed: ('sleep', 'forced', 'normal')
- Register: REG_PWR_CTRL
- Help Controls sensor power mode: sleep, forced, normal

 ***Information Unit***

- Name: osr_p
- Type: config
- Allowed: (1, 2, 4, 8, 16, 32)
- Register: REG_OSR
- Help Pressure oversampling (human readable). Datasheet 3.4.4

 ***Information Unit***

- Name: osr_t
- Type: config
- Allowed: (1, 2, 4, 8, 16, 32)
- Register: REG_OSR
- Help Temperature oversampling (human readable). Datasheet 3.4.4

 ***Information Unit***

- Name: odr_sel
- Type: config
- Allowed: (5, 10, 20, 40, 80, 160, 320, 640, 1280, 5120, 10240, 20480, 40960, 81920, 163840, 327680, 655360)
- Register: REG_ODR
- Help Output data rate (human readable). Sampling period in ms, which is more natural for event loops. Datasheet 4.3.20

 ***Information Unit***

- Name: short_in
- Type: config
- Allowed: (0, 1)
- Register: REG_CONFIG
- Help short_in

 ***Information Unit***

- Name: iir_filter
- Type: config
- Allowed: (0, 2, 4, 8, 16, 32, 64, 128)
- Register: REG_CONFIG
- Help IIR filter coefficient (human readable). Datasheet  3.4.3

 ***Information Unit***

- Name: cmd
- Type: command
- Allowed: ('nop', 'fifo_flush', 'softreset')
- Register: REG_CMD
- Help Receives a command to execute

 ***Information Unit***

- Name: frameiu_press_and_temp
- Type: frame
- Allowed: N/A
- Register: FRAME_PRESS_AND_TEMP
- Help Pressure (Pa) and temperature (C) compensated values

 ***Information Unit***

- Name: frameiu_temp
- Type: frame
- Allowed: N/A
- Register: FRAME_TEMP
- Help Temperature (C) compensated value

 ***Information Unit***

- Name: frameiu_press
- Type: frame
- Allowed: N/A
- Register: FRAME_PRESS
- Help Temperature (C) compensated value

 ***Information Unit***

- Name: frameiu_sensortime
- Type: frame
- Allowed: N/A
- Register: FRAME_SENSORTIME
- Help Sensor Time

 ***Information Unit***

- Name: frameiu_empty
- Type: frame
- Allowed: N/A
- Register: FRAME_EMPTY
- Help Empty frame dummy response

 ***Information Unit***

- Name: frameiu_error
- Type: frame
- Allowed: N/A
- Register: FRAME_ERROR
- Help Error frame dummy response

 ***Information Unit***

- Name: frameiu_config_change
- Type: frame
- Allowed: N/A
- Register: FRAME_CONFIG_CHANGE
- Help Config frame dummy response, inserted when a change in FIFO config happens
