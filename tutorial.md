# Introduction

This tutorial will show you all the basic and some of the less well known features of the BMP3XX and how they can be accessed using this driver. We will use simple examples for each feature or group of features. You can then use and combine them to create your own application.

The examples have been tested with an ESP32-S3 board and an Adafruit BMP390 breakout board, but everything should work with other boards and sensors as well. Just watch out for the pin numbers and change them for the correct ones for your setup.

The examples are embedded in this tutorial along with the explanations, but they are also available in the [examples](./examples/) folder as separate python files.

# Contents

- [Introduction](#introduction)
- [Contents](#contents)
- [Installation](#installation)
- [Initialization](#initialization)
  - [I2C](#i2c)
  - [SPI](#spi)
- [Basic Usage](#basic-usage)
- [Getting information and help](#getting-information-and-help)
- [General Use (read and write generic InfoUnits)](#general-use-read-and-write-generic-infounits)
  - [Reading data](#reading-data)
  - [Reading configuration](#reading-configuration)
  - [Writing configuration](#writing-configuration)
- [Custom Wrappers for Enhanced Usability](#custom-wrappers-for-enhanced-usability)
  - [Wraping data\_read](#wraping-data_read)
  - [Wraping config\_read](#wraping-config_read)
  - [Wraping config\_write](#wraping-config_write)
  - [But those names for the InfoUnits....why?](#but-those-names-for-the-infounitswhy)
- [Configuration presets](#configuration-presets)
- [Measuring altitude](#measuring-altitude)
- [Output Data Rate (ODR)](#output-data-rate-odr)
- [Forced read and forced mode](#forced-read-and-forced-mode)
- [IIR filter](#iir-filter)
- [FIFO](#fifo)
  - [General description](#general-description)
  - [Configuration parameters](#configuration-parameters)
  - [FIFO frames](#fifo-frames)
  - [Accessing the FIFO](#accessing-the-fifo)
    - [fifo\_data InfoUnit (not recommended)](#fifo_data-infounit-not-recommended)
    - [Inspect RAW FIFO content (not recommended)](#inspect-raw-fifo-content-not-recommended)
    - [fifo\_debug()](#fifo_debug)
    - [fifo\_read()](#fifo_read)
    - [Use fifo\_auto\_queue() to automatically process the FIFO](#use-fifo_auto_queue-to-automatically-process-the-fifo)

# Installation

The driver is composed of three files: `sensor.py`, `bmp3xx.py` and `bmp3xx_data_structure.py`. To make it work, just copy those three files with your favorite tool to the board (`/` or `/lib`) folders.

There are no other dependencies.

[↺ Back to contents](#contents)

# Initialization

Initializing the device is easy, you just have to import the BMP3XX class and instantiate the sensor providing a valid BUS object, which can be a I2C object or an SPI object.

In some examples or code blocks, I'll include the sensor initialization code, but sometimes I'll omit it to make code blocks shorter, just remember to initialize the sensor before using it.

## I2C

```python
from bmp3xx import BMP3XX
from machine import Pin, I2C

# I2C, use correct pins for your board and wiring
i2c = I2C(0, scl=Pin(9), sda=Pin(8))
sensor = BMP3XX(i2c)

print("\n" + "-" * 20 + "\n")
print(sensor.all)
```

[→ 00-initialization_i2c.py](./examples/00-initialization_i2c.py)

This uses the default BMP3XX I2C address 0x77.
If you need to provide a different one, you must pass it
as a keyword argument, like so:

`sensor = BMP3XX(i2c, i2c_addr=0x76)`

## SPI

In the case of SPI you must supply the Chips Select (CS) pin as the spi_cs keyword argument, which must be a machine.Pin object.

```python
from bmp3xx import BMP3XX
from machine import Pin, SPI

# SPI, chose correct pins for your board and wiring
SCK = Pin(36)
MOSI = Pin(35)
MISO = Pin(37)
CS = Pin(12)
SPI_N = 2
spi = SPI(SPI_N, sck=SCK, mosi=MOSI, miso=MISO)

sensor = BMP3XX(spi, spi_cs=CS)

print("\n" + "-" * 20 + "\n")
print(sensor.all)
```

[→ 00-initialization_spi.py](./examples/00-initialization_spi.py)

[↺ Back to contents](#contents)

# Basic Usage

The driver offers four properties that can be directly read from the sensor:

- `press`: atmospheric pressure in Pascals (Pa)
- `temp`: temperature in degrees Celsius (C)
- `alt`: altitude in meters (m)
- `all`: all of the above inside a named tuple with fields: press, temp and alt

```python
import time
from bmp3xx import BMP3XX
from machine import Pin, I2C

# I2C, use correct pins for your board and wiring
i2c = I2C(0, scl=Pin(9), sda=Pin(8))
sensor = BMP3XX(i2c)

print("\n" + "-" * 20 + "\n")
print(f"The pressure is {sensor.press} Pascals")
print(f"The temperature is {sensor.temp} Degrees Celsius")
print(f"The altitude is {sensor.alt} meters")
print("\n" + "-" * 20 + "\n")

time.sleep_ms(100)
sd = sensor.all  # Get all available readings
print(f"All data can be pulled together as a SensorData namedtuple:\n{sd}")
print(f"Access each field: press: {sd.press}, temp: {sd.temp}, alt: {sd.alt}")
print("\n" + "-" * 20 + "\n")
```

[→ 01-basic_usage.py](./examples/01-basic_usage.py)

[↺ Back to contents](#contents)

# Getting information and help

This driver allows you to read and write every piece of meaningful information on the device.

There are lots of information you can read and write from/to the device. The absolute best place to know want can you read and write from/to the device is the datasheet, which I recommend you to read if you want to go beyond the basics.

Nonetheless, you can check from the REPL (or from your script) for basic info about what pieces of information (InfoUnits) are available on the device.

`sensor.info()` or `sensor.info('sensor')` give you general information about the Sensor, providing the names of available config and data registers and config and data InfoUnits.

InfoUnits are what you read or write to get readings, current config or change the configuration of the device. We will see how to do that in the next example. In general, config InfoUnits can be read or written, data InfoUnits can be read.

```python
import time
from bmp3xx import BMP3XX
from machine import Pin, I2C

# I2C, use correct pins for your board and wiring
i2c = I2C(0, scl=Pin(9), sda=Pin(8))
sensor = BMP3XX(i2c)

# General info
print()
print("-" * 50)
sensor.info()
print("-" * 50)
print()
```

[→ 02-getting_info.py](./examples/02-getting_info.py)

You can get a little bit more detailed information about Registers, Frames and InfoUnits by executing `sensor.info('registers')`, `sensor.info('frames')` or `sensor.info('infounits')` respectively.

```python
# More detailed info
print()
print("-" * 50)
sensor.info("registers")
print("-" * 50)
print()

print()
print("-" * 50)
sensor.info("frames")
print("-" * 50)
print()

print()
print("-" * 50)
sensor.info("infounits")
print("-" * 50)
print()
```

[→ 02-getting_info.py](./examples/02-getting_info.py)

Finally, the driver will try to show you helpful information when an error occurs. For example, if you try to use a InfoUnit that doesn't exist, it will show you available InfoUnits. If you try to configure one with a value that is not allowed, the driver will try to show you what are the valid values for that InfoUnit.

```python
# Helpful error messages
print()
print("-" * 50)

try:
    sensor.data_read("config_error")
except Exception as e:
    print(e)

print()
print("-" * 50)

try:
    sensor.config_write(iir_filter=45)
except Exception as e:
    print(e)
```

[→ 02-getting_info.py](./examples/02-getting_info.py)

The last block outputs this:

```output
--------------------------------------------------
Parameter 'config_error' is not legal.
Allowed values are: ('chip_id', 'rev_id', 'fatal_err', 'cmd_err', 'conf_err', 'cmd_rdy', 'drdy_press', 'drdy_temp', 'press_and_temp', 'press', 'temp', 'press_and_temp_adc', 'altitude', 'sensortime', 'por_detected', 'itf_act_pt', 'fwm_int', 'ffull_int', 'drdy', 'fifo_length', 'fifo_data', 'fifo_water_mark', 'fifo_mode', 'fifo_stop_on_full', 'fifo_time_en', 'fifo_press_en', 'fifo_temp_en', 'fifo_subsampling', 'data_select', 'int_od', 'int_level', 'int_latch', 'fwtm_en', 'ffull_en', 'int_ds', 'drdy_en', 'spi3', 'i2c_wdt_en', 'i2c_wdt_sel', 'press_en', 'temp_en', 'mode', 'osr_p', 'osr_t', 'odr_sel', 'short_in', 'iir_filter', 'cmd', 'frameiu_press_and_temp', 'frameiu_temp', 'frameiu_press', 'frameiu_sensortime', 'frameiu_empty', 'frameiu_error', 'frameiu_config_change')

--------------------------------------------------
Parameter 'iir_filter' must be in (0, 2, 4, 8, 16, 32, 64, 128). Was '45' 
Parameter help: IIR filter coefficient (human readable). Datasheet  3.4.3
```

[↺ Back to contents](#contents)

# General Use (read and write generic InfoUnits)

Besides basic use, you can use three powerful method to read/write
any InfoUnit you wish from the device.

This tools are:

- `data_read('InfoUnit1', 'InfoUnit2',...)` returns a dictionary with the values of all requested data InfoUnits.
- `config_read('InfoUnit1', 'InfoUnit2',...)` returns a dictionary with the values of all requested config info units.
- `config_write(InfoUnit1=value1, InfoUnit2=value2,...)` returns a dictionary with the values of all requested config info units.

The names of the InfoUnits are the same as the ones you can see in the datasheet, so you can search for them there.

The parameters that you can read/write are **not** the ones you can see in the datasheet. They are always as human-readable and intuitive as possible. The driver will try to convert the values you pass to the correct values for the device. For example, if you want to set the IIR filter to 4, you can pass `iir_filter=4` to `config_write` and the driver will convert it to the correct value for the device.

You can check available values for a given InfoUnit in the bmp3xx_data_structure.py file, along with the `pack` and `unpack` methods used to convert the human-readable values to the values used by the device.

Also, if you try to read/write a InfoUnit that doesn't exist, the driver will try to show you available values for that InfoUnit.

Let's see some examples.

## Reading data

Read *pressure* information (`press`) and the *power-on-or-reset flag* (`por-detected`), which informs you if the device has been rebooted since the last time you checked this flag. We will use `sensor.softreset()` to force a reset of the device. `por_detected` can be a useful InfoUnit to detect device reboots.

```python
import time
from bmp3xx import BMP3XX
from machine import Pin, I2C

# I2C, use correct pins for your board and wiring
i2c = I2C(0, scl=Pin(9), sda=Pin(8))
sensor = BMP3XX(i2c)

# Read some arbitrary data from the device
print("\n" + "-" * 20 + "\n")
for i in range(5):
    data = sensor.data_read("press", "por_detected", "mode")
    print()
    print(f"Current pressure = {data['press']}")
    print(f"Device restarted since last checked = {bool(data['por_detected'])}")
    time.sleep_ms(100)
    if i == 2:
        # Reset the device to notice the change in por_detected flag
        sensor.softreset()
```

[→ 03-general_use.py](./examples/03-general_use.py)

## Reading configuration

Now let's do it with some configuration options. Let's read the following device
config parameters:

- Pressure Oversampling
- Temperature Oversampling
- Power mode
- IIR filter coefficient

You can enable or disable printing the results in a nice tabulated way with the
argument `print_result=True`

```python
# Read some configuration parameters from the device
print("\n" + "-" * 20 + "\n")
print("\nRead some config parameters")
config = sensor.config_read("osr_p", "osr_t", "mode", "iir_filter", print_result=True)
```

[→ 03-general_use.py](./examples/03-general_use.py)

`config_read()` and `data_read()` return a dictionary with the requested InfoUnits as keys and their values as values. You can also use `config_read()` to read all the configuration parameters at once, without specifying any parameter.

You can use `print_result=True` as above to print the results in a nice tabulated way.

## Writing configuration

You can alter the device confituration with `config_write`. It takes parameters (InfoUnits name strings) as kwargs and update config accordingly.

- update = True  -> Updates only the provided parameters, using current config as base. This is the default.
- update = False -> Takes parameters defaults, updates it with provided parameters and applies it. Returns the applied config.

For example, we can update current configuration to set IIR filter order to 32 and
pressure oversampling to 4:

```python
# Writing configuration parameters
print("\n" + "-" * 20 + "\n")
print("\nSet iir and press oversampling with update=True (default)")
sensor.config_write(iir_filter=32, osr_p=4, osr_t=2)
```

[→ 03-general_use.py](./examples/03-general_use.py)

Unless you suppress printing with print_result=False, `config_write` will show you the previous configuration (config on the device before this change), the base configuration (which can be the current config or the InfoUnit defaults depending ont the `update` parameter,
which defaults to True), the requested config and the new config.

This allows you to easily spot if the command is having the effects you want.

`config_read` without parameters returns complete current sensor config. Lets run it,
apply the same config change with the `update` parameter set to False (takes InfoUnit
defaults instead of current config), run `config_read` again and compare the results.
`config_write` only changes the configuration of the affected Registers (those that
contain the InfoUnits you are changing), so the rest of the config remains the same.

The default value for the InfoUnits is in the `bmp3xx_data_structure.py` file.

```python
# update = True vs update = False
print("\n" + "-" * 20 + "\n")
print("\nComplete config")
sensor.config_read(print_result=True)
print("\nSet iir and press oversampling again but with update=False")
sensor.config_write(iir_filter=32, osr_p=4, update=False)
print("\nComplete config")
sensor.config_read(print_result=True)
```

[→ 03-general_use.py](./examples/03-general_use.py)

Check how `osr_t` has changed from 2 to 1, as it is the default value, even if we didn't change it. This InfoUnit is in the same Register as `osr_p`, so it is affected by the change.

update=True works for incremental changes from your current configuration. update=False works for setting a new configuration from scratch without having to take care of the values for InfoUnits you are not changing.

[↺ Back to contents](#contents)

# Custom Wrappers for Enhanced Usability

The tools that allow you to read and write information from the device are very flexible and powerful, but they can be a bit cumbersome to use. You have to remember the name of the InfoUnit you want to read or write, and you have to know if it is a data or a config InfoUnit.

Also, returned data is a dictionary, which is not always the most convenient, especially if you are only interested in one of the values.

All this is intentional, to be able to use only one set of tools to manipulate and read anything on the device (and potentially other devices), but if it doesn't feel confortable to you, you can write some user wrappers around those tools to make your life easier. Each one will take you just a few seconds and a couple of lines of code.

## Wraping data_read

The following method acts as a wrapper around the InfoUnit `drdy_press`, a flag that indicates that a fresh new pressure sample is available for reading. Writing this method will take about ten seconds, but it will save you a lot of time in the future if you plan to use it frequently.

```python
def press_data_ready(sensor: BMP3XX):
    return sensor.data_read("drdy_press", print_result=False)["drdy_press"]
```

[→ 04-user_wrappers.py](./examples/04-user_wrappers.py)

Now you can use `press_data_ready(sensor)` to check if there is new pressure data available instead of `sensor.data_read("drdy_press")["drdy_press"]` if you prefer.

## Wraping config_read

We can do the same with `config_read`. The following method wrappers around the InfoUnit `osr_p` which is the pressure oversampling. It returns the current pressure oversampling value.

```python
def get_press_oversampling(sensor: BMP3XX):
    return sensor.config_read("osr_p", print_result=False)["osr_p"]
```

[→ 04-user_wrappers.py](./examples/04-user_wrappers.py)

Now you can use `get_press_oversampling(sensor)` to check the current pressure oversampling instead of `sensor.config_read("osr_p")["osr_p"]` if you prefer.

## Wraping config_write

We can do the same with `config_write`. The following method wrappers around the InfoUnit `osr_p` which is the pressure oversampling. It sets the pressure oversampling to the provided value.

```python
def set_press_oversampling(sensor: BMP3XX, value: int):
    sensor.config_write(osr_p=value, print_result=False)
```

[→ 04-user_wrappers.py](./examples/04-user_wrappers.py)

Now you can use `set_press_oversampling(sensor, value)` to set the pressure oversampling instead of `sensor.config_write(osr_p=value)` if you prefer.

You can build custom wrappers to suit your needs if you are going to use some InfoUnits a lot.

If you prefer to use them as bound methods, you can add your custom wrappers to the `BMP3XX` class inside `bmp3xx.py` and use them as `sensor.press_data_ready()` instead of `press_data_ready(sensor)`.

In fact, most of the methods in `bmp3xx.py` are just that, custom wrappers around the tools in `sensor.py` and the `Sensor` class.

Some obvious needs are already covered, like `sensor.pressure` which is a wrapper around `sensor.data_read("pressure")["pressure"]`, but you can add your own if you have special needs.

## But those names for the InfoUnits....why?

Not all InfoUnit names are the best, but they are the ones used in the datasheet, so it is easier to find the relevant information there when needed. Sorry.

[↺ Back to contents](#contents)

# Configuration presets

The BMP3XX has a lot of parameters to configure. If you want to understand all the possibilities the device has to offer, you should read the datasheet, or at least the relevant parts and manipulate them with `config_write`. But if you just want to get started, you don't really need to.

If you don't want to decide each relevant parameter, you can use the available config presents (templates).

Config templates are defined in `bmp3xx_data_structure.py module`. Most are recommended configs by the manufacturer for certain applications, but you can also define your own.

To apply one, you just use the `apply_config_preset` method.
To see the available presets, you can inspect the bmp3xx_data_structure` module. If you call the method without arguments, it will print the available presets.

```python
# This throws an exception, but offers a list of available presets
print("Available templates:")
sensor.apply_config_preset()
```

At the moment of writing the available presets are:

- handheld_dev_low_power
- handheld_dev_dynamic
- indoor_navigation
- indoor_localization
- drop_detection
- init
- weather_monitoring
- drone

Most are self-explanatory, but *init* which is the basic config that is applied by default when you initialize the device. This is donee because, by default, the bmp3xx starts in sleep mode and with both sensors disabled.

You can find what parameters are set by each preset in the `bmp3xx_data_structure.py` module (or in the datasheet). For example, the *indoor_navigation* preset sets the following parameters:

```python
"indoor_navigation": {
        "press_en": 1,
        "temp_en": 1,
        "mode": "normal",
        "osr_p": 16,
        "osr_t": 2,
        "iir_filter": 4,
        "odr_sel": 40,
        "data_select": "filtered",
    },
```

This presets or config templates are nothing more than a dictionary with the parameters you want to set.

We can apply for example the `indoor_navigation` preset and check the resulting config. Now the parameters are set to the recommended values for indoor navigation.

```python
print("\n" + "-" * 20 + "\n")
print("Applying indoor_navigation preset")
sensor.apply_config_preset("indoor_navigation")
sensor.config_read()
```

[→ 05-config_presets.py](./examples/05-config_presets.py)

[↺ Back to contents](#contents)

# Measuring altitude

Based on the current barometric pressure and a standard sea level pressure, the current altitude can be calculated.

As seen in the 01-basic_usage.py example, the altitude can be requested by simply accessing the *alt* property `sensor.alt`.

This will return the altitude in meters (m), and will work fine for relative altitude measurements, but if you want to get an accurate absolute altitude, you need to calibrate the sensor.

This can be done using the `calibrate_altimeter` method, which calibrates the altimeter based on known local altitude **or** sea level pressure.

To calibrate the altimeter you can use either the correct local sea level pressure or the correct local altitude. Note that local sea level pressure is NOT the local pressure at current altitude, but the pressure that would be measured at sea level. It can be obtained in some weather sites. Units are meters (for altitude) or Pascals (carful, most weather sites provide hPa or mbar).

I find easier to use the local altitude, which is usually easier to know and does not vary with the weather. Use it whenever you can.

Either way, you must provide *one and only one* of the arguments to use one of the two calibration methods:

- local_alt (float, optional): the known local altitude in meters.
- local_press (float, optional): the known local *sea level* pressure in Pascals.

```python
print("\n" + "-" * 20 + "\n")
print(f"Altitude before calibration {sensor.alt} m")
print("\n" + "-" * 20 + "\n")
print("Now let's calibrate the altimeter using the local altitude")
# Use your real local altitude here
sensor.calibrate_altimeter(local_alt=900)
print(f"Altitude after calibration {sensor.alt} m")
print("\n" + "-" * 20 + "\n")
print("Now let's calibrate the altimeter using the local sea level pressure")
# Use your real local sea level pressure here
sensor.calibrate_altimeter(local_press=90750)
print(f"Altitude after calibration {sensor.alt} m")
```

[→ 06-altitude.py](./examples/06-altitude.py)

Now the sensor can provide accurate absolute altitude measurements.

➜ **TIP**: Even if you are only interested in relative altitude measurements, you can still make use of this method. Simply calibrate the altimeter to 0m and all subsequent measurements will be relative to this altitude.

```python
# Relative altitude calibrating at 0m
print("\n" + "-" * 20 + "\n")
print("Calibrating to 0m")
sensor.calibrate_altimeter(local_alt=0)
for _ in range(5):
    print(f"Relative altitude {sensor.alt} m")
    time.sleep(3)
```

[→ 06-altitude.py](./examples/06-altitude.py)

You will see that the altitude is not exactly 0m. This is due to the sensor's noise.
If you move the sensor vertically during this phase you will see more change.

[↺ Back to contents](#contents)

# Output Data Rate (ODR)

By default, the driver put the sensor in normal mode. In that mode, the sensor takes measurements at a fixed rate (Output Data Rate, ODR) and the driver returns the contents of the last sample when asked for a read.

The ODR can be configured in the `odr_sel` InfoUnit, using the  `config_write` method. It must be one of 5, 10, 20, 40, 80, 160, 320, 640, 1280, 5120, 10240, 20480, 40960, 81920, 163840, 327680, 655360 milliseconds.

There is a limit on how fast can the sensor take measurements. Depending on the oversampling that you set for pressure and temperature. Simplifying, the higher the oversampling, the more accurate the measurement, but the longer it takes. The ODR must be equal or greater than the time it takes to take a measurementin order for the sensor to be able to keep up with the ODR. In other words, osp_p, osp_t and odr_sel must be compatible. See Datasheet 3.9.2 for details.

If you set an ODR that is too fast for the oversampling, the driver will through an Exception, but if osr_p, osr_t, and odr_sel change dinamically during your program execution, you may want to check the compatibility beforehand. Also this only works in normal mode, if you input a potentially invalid config while in sleep mode neither the device nor the driver will raise any error, so it's not fool proof. If at the moment of applying the new configuration the sensor is in forced/sleep mode, the driver will not catch the error and it will pop up later if you switch to normal. After an error, the drivers enters *sleep mode* and depending on how are you trying to use it, you can get inconsistent and puzzling results. Be careful.

You can use the `calc_odr` helper method to check this beforehand. It calculates measure conversion time in ms.

With no args, calculates it from current sensor config.

With args provided, it calculates it from them (as an estimation tool for the user).

This can be usefull to see if certain configuration is compatible with
a desired Output Data Rata (ODR) or to estimate the conversion time
in forced mode.

Lets see all this in action:

```python
sensor.calc_odr()
```

[→ 07-Output_Data_Rate.py](./examples/07-Output_Data_Rate.py)

Will output something like this (depends on the current config of the device):

```
PARAMETER               CURRENT   
fifo_subsampling           1      
odr_sel                    40     
osr_p                      1      
osr_t                      1      
press_en                   1      
temp_en                    1      
Calculated conversion time is 4.829 ms
Minimum ODR selected for this config should be 5
Current ODR is 40
Current FIFO ODR 40
```

Let's say we now want to know the conversion time for a different config. We need to provide the args to the method as keyword arguments:

- press_en: Pressure enabled (1) or disabled (0)
- temp_en: Temperature enabled (1) or disabled (0)
- osr_p: Pressure oversampling (1, 2, 4, 8, 16, 32)
- osr_t: Temperature oversampling (1, 2, 4, 8, 16, 32)
  
In this case, the method will output the calculated for the provided arguments, along with the current ODR and the minimum ODR that should be selected for this config. You can easily check with this if the ODR you want to set is compatible with the current config.

```python
sensor.calc_odr(
    press_en=1,
    temp_en=1,
    osr_p=16,
    osr_t=2,
)
```

[→ 07-Output_Data_Rate.py](./examples/07-Output_Data_Rate.py)

Will output something like this:

```output
Calculated conversion time is 69.469 ms
Minimum ODR selected for this config should be 80
Current ODR is 40
Current FIFO ODR 40
```

Here we can see that the current ODR is 40, but the minimum ODR for this config is 80, so this configuration is invalid and will fail.

You can suppress the verbose output from `calc_odr` by setting the argument explain=False. The method always returns a tuple with the calculated conversion time, the current ODR and the minimum ODR for the requested config to be valid (`return (conversion_time_ms, odr_sel, min_odr)`). You can use the returned values inside your logic to decide whether to apply the config or not.

Just for fun let's see how conversion time and minimum ODR increase when we use osr_t=2 and we gradually increase osr_p:

```python
print("OSR_P       Conv. Time       min ODR")
for osr_p in (1, 2, 4, 8, 16, 32):
    res = sensor.calc_odr(press_en=1, temp_en=1, osr_t=2, osr_p=osr_p, explain=False)
    print(f"{osr_p:5d}    {res[0]:10.2f} ms    {res[2]:7d} ms")
```

[→ 07-Output_Data_Rate.py](./examples/07-Output_Data_Rate.py)

outputs:

```output
OSR_P       Conv. Time       min ODR
    1          6.85 ms         10 ms
    2          8.87 ms         10 ms
    4         12.91 ms         20 ms
    8         20.99 ms         40 ms
   16         37.15 ms         40 ms
   32         69.47 ms         80 ms
```

Finally, let's take a look at what happens when we try to set a configuration where the conversion time is incompatible with the ODR. Thanks to the previous table, we know that for osr_t=2 and osr_p=32, the conversion time is 69.47ms and the min ODR should be 80ms, but we are asking for an ODR of 5ms.

```python
sensor.softreset()
time.sleep_ms(5)
sensor.config_write(odr_sel=5, osr_p=16, osr_t=16, mode="normal")
time.sleep_ms(10)
sensor.press
```

[→ 07-Output_Data_Rate.py](./examples/07-Output_Data_Rate.py)

While I cannot promise, this should trigger a `SensorError` exception. Try to avoir this situations by using `calc_odr` to make sure your config is valid before applying it.

We will talk more about FIFO ODR later.

[↺ Back to contents](#contents)

# Forced read and forced mode

By default, the driver reads return the contents of the last sample available in the device. Usually this is what you want, specially if you are working in normal mode and and the sensor Output Data Rate (ODR) is appropriate for the polling rate.

By reading that way, the read is non-blocking and faster. It doesn't check if data is new and returns immediately. In some cases, this may lead to returning the same sample in consecutive sensor readings. If this is not acceptable for your application you can use `forced_read` method to force the driver to return data from the last sample, doing a blocking wait until fresh data is available.

This method should also be used when working in forced mode (the device sleeps until it's
asked for another forced measure) unless you plan to handle manually the transitions
between forced and sleep modes. See Datasheet 3.3 Power Modes for details.

Note that in forced mode, the IIR filter does not work.

First, we will set up the device with a ODR and other parameters that allows us to notice the difference. ODR is the time  between measurements, in milliseconds. It must be one of the following values: 5, 10, 20, 40, 80, 160, 320, 640, 1280, 5120, 10240, 20480, 40960, 81920, 163840, 327680, 655360.

If we take several fast measures this happens:

```python
print("\n" + "-" * 20 + "\n")
print("Taking several fast consecutive measurements in normal mode")
sensor.config_write(odr_sel=160, osr_p=16, osr_t=2, print_result=False)
start = time.ticks_ms()
for _ in range(10):
    print(sensor.press)
stop = time.ticks_ms()
elapsed = time.ticks_diff(stop, start)
print(f"Elapsed time: {elapsed} ms")
```

[→ 08-forced_read.py](./examples/08-forced_read.py)

My output:

```output
90987.65
90987.65
90988.66
90988.66
90988.66
90988.66
90988.66
90988.66
90988.66
90988.66
Elapsed time: 42 ms
```

Here you can notice that very little time has passed between measurements. The return is non-blocking and fast (42ms for 10 measurements in my case). But you will probably see that many (probably all) measurements are the same. This is because we are polling the sensor much faster than the ODR (160ms in this case).

Now we will repeat the same measurements but using forced_read".

```python
print("\n" + "-" * 20 + "\n")
print("Now we will repeat the same measurements but using forced_read")
start = time.ticks_ms()
for _ in range(10):
    print(sensor.forced_read().press)
stop = time.ticks_ms()
elapsed = time.ticks_diff(stop, start)
print(f"Elapsed time: {elapsed} ms")
```

[→ 08-forced_read.py](./examples/08-forced_read.py)

My output:

```output
90996.02
90995.98
90996.55
90994.17
90995.4
90995.19
90996.41
90995.91
90996.27
90995.76
Elapsed time: 1520 ms
```

Now all measurements are different. This is because the driver is waiting for new data to be available. It also took much longer (1520ms in my case) to take 10 measurements. The time between measurements is now limited by the conversion time of the sensor for the provided parameters. Oversampling pressure and temperature (osr_p and osr_t) are the main factors here. See Datasheet 3.9.2.

This method will work in both *normal* and *forced* mode. In normal mode, it will do a blocking wait until new data is available. In forced mode, it will do a blocking wait until the sensor has finished the conversion and is ready to be read.

In both cases, it will return the contents of the last new reading. After a measurement in forced mode, the sensor will go back to sleep. `forced_read()` method changes the mode again to forced whenever you use it, so you don't have to worry about it.

Understand the difference between normal and forced mode. In normal mode, the sensor is always measuring, while in forced mode it sleeps until you ask for a measurement. In normal mode, the ODR is the time between measurement. This guarantees that measurements are taken at regular intervals, which is **very important if you plan to apply any kind of digital filtering to the received samples**.

In normal mode (without using forced_read), the driver will return the contents of the last sample immediately, even if it's the same data. If in doubt, use normal mode with an adequate ODR for the application, but forced mode may be useful in some cases. If you need to take measurements at irregular intervals, you can use forced mode and let the sensor sleep between measurements making it more energy efficient. Also ODR is limited to 655360ms (10.9 minutes) so if you need to take measurements  at longer intervals, you can use forced mode too.

[↺ Back to contents](#contents)

# IIR filter

The BMP3XX incorporates a configurable IIR recursive filter that smooths the output data stream. This allows you to filter out temporary disturbances in the output data, like sudden changes in pressure due to wind gusts, a slamming door, etc.

Since the filter is in the BMP3XX itself, you get this post processing for free, without needing to implement this into your code, consuming MCU resources.

The filter is configured with the `iir_filter` InfoUnit, which can be set to one of this values: 0, 2, 4, 8, 16, 32, 64, 128. 0 means the output is unfiltered and any other value will indicate the order of the filter, the higher the order the smoother the output, but also the slower the response to real changes in temperature or pressure.

The filter only works in **normal mode**, and gets cleared every time the config changes because it doesn't make sense to keep adding samples to the filter that are not related to each other (for example if you change filter order or activate/deactivate the pressure or temperature sensor). You need to wait for the number of samples indicated by the filter order to get a stable output.

See section 3.4.3 of the Datasheet for details on the implementation of the filter.

Output noise should be reduced when incrementing the IIR filter order, but the response time will also increase. Let's see how the filter order affects the output noise to see the filter in action.

```python
def calculate_noise(samples):
    n = len(samples)
    mean = sum(samples) / n
    variance = sum((xi - mean) ** 2 for xi in samples) / n
    noise = variance**0.5
    return noise


iir_values = (0, 2, 4, 8, 16, 32, 64, 128)
samples = []
N = 256

sensor.config_write(
    osr_p=1,
    osr_t=1,
    odr_sel=5,
    iir_filter=0,
)

print("IIR      noise")
for iir in iir_values:
    sensor.config_write(iir_filter=iir, print_result=False)
    samples.clear()
    # Stabilize filter output
    for i in range(iir + 10):
        sensor.forced_read().press
    # Actual measures to be analyzed
    for i in range(N):
        samples.append(sensor.forced_read().press)
    print(f"{iir:3d} {calculate_noise(samples):10.2f}")
```

[→ 09-iir_filter.py](./examples/09-iir_filter.py)

In my case it gives the following out, that more or less matches the noise values in the datasheet:

```output
IIR      noise
  0       3.45
  2       1.98
  4       1.50
  8       0.87
 16       0.72
 32       0.41
 64       0.35
128       0.19
```

Remember that it take longer to the output to catch up with real changes in pressure as the filter order increases. This is because the filter is recursive, so it depends on previous values to calculate the current output. A nice experiment could be to measure the response time of the filter to a sudden change in pressure (move the sensor vertically and measure how much time take the output to catch up) for different filter orders.

[↺ Back to contents](#contents)

# FIFO

## General description

The integrated FIFO buffer is one of my favorite features of the BMP3XX. It's a highly configurable 512-byte buffer that stores sensor readings to be processed by the main script at a later time.

This effective isolates the sampling rate from the processing rate, allowing you to sample at a high rate and process later. This avoids blocking operations in the main script / MCU to affect your sampling rate, guaranteeing a constant sampling rate, which is critical to applications where samples are processed with **digital filters**.

There might be much more reasons, but at least for me, there are two big winners here:

- **Avoid disruption of your sampling rate by blocking operations**. MicroPython users sometimes have to deal with blocking operations that can take longer than one sampling period, such as synchronous I/O operations, garbage collection (especially on boards with a substantial amount of PSRAM, where garbage collection can take a considerable amount of time), or any other blocking routine. Using the device's FIFO can "protect" your sampling process from being affected by these blocking processes.
- **Ultra Low power applications**. In normal mode, the BMP sleeps between samples to save power. You can combine this feature with the FIFO to store samples in it while the main MCU is in a deep sleep mode, only waking up to process a batch of samples in the FIFO from time to time. For example, if you are sampling at 10.24s and only storing pressure information in the FIFO frames (more on that later), you can store more than 100 samples in the FIFO before the MCU wakes up to process them. This allows you to have a very low power consumption, while still sampling at a higher rate than the MCU need to process them. In this example you could wake the MCU every 15min and still maintain a 10.24s sampling rate.

## Configuration parameters

The FIFO con be configured to suit your specific needs. Here are the most importante InfoUnits that control FIFO behavior and their descriptions:

- `fifo_mode`. Enables or disables de FIFO (1 or 0).
- `fifo_press_en`. Enables or disables including pressure data in the FIFO frames (1 or 0).
- `fifo_temp_en`. Enables or disables including temperature data in the FIFO frames (1 or 0).
- `fifo_time_en`. Enables or disables including time data in the FIFO frames (1 or 0).
- `data_select`. Selects whether the samples stored in the FIFO come from the raw samples ('unfiltered') or from the output of the IIR filter ('filtered').
- `fifo_subsampling`. Controls FIFO subsampling. If deactivated (1), every new sample is stored in the FIFO. If other value is selected (N), only one out of every N samples is stored in the FIFO. For example, if you select 2, only one out of every two samples will be stored in the FIFO. This is useful to reduce the FIFO size and increase the effective sampling rate. Allowed values are 1, 2, 4, 8, 16, 32, 64, 128.
- `fifo_stop_on_full`. Controls whether the FIFO stops storing new samples (preserving the old ones) when it is full (1) or if it overwrites the oldest samples with the new ones (0).
- `fifo_water_mark`. This parameter sets a watermark level in bytes (0-511) that will trigger a FIFO watermark interrupt when the FIFO is filled above this level. This is useful to wake up the MCU when the FIFO is almost full to process the samples before the FIFO overflows.
- `fwtm_en`. Enables or disables an interrupt when the FIFO watermark level is reached (1 or 0).
- `ffull_en`. Enables or disables an interrupt when the FIFO is full (1 or 0).

## FIFO frames

When reading from the FIFO, information comes in frames. There are data several type of frames:

- Pressure: contains pressure information.
- Temperature: contains temperature information.
- Pressure and temperature: contains both pressure and temperature information.
- Sensor time: contains the time since the last reset of the sensor in sensor 'ticks'. *I haven't found any reference in the documentation, but I measured a tick to be about 39us*.
- Empty: contains no information. This is used to indicate that the FIFO is empty.
- Error: contains no information. This is used to indicate an error in the FIFO configuration.
- Config change: contains no information. This is used to indicate that the FIFO configuration has changed.

If you plan to process the FIFO frames manually, I suggest you learn a little bit more about them reading the Datasheet (section 3.6.5) and also play a bit with different situations and use the `fifo_debug` method to analyze at a glance the FIFO content.

But it's not needed if you don't want to, there are other methods that abstract and simplify the FIFO access. We will see them later.

## Accessing the FIFO

This drivers offers you several ways to access the FIFO.

### fifo_data InfoUnit (not recommended)

You can simply reading the `fifo_data` InfoUnit, like `sensor.data_read('fifo_data')`. This will return information from the FIFO.

```python
sensor.config_write(
    press_en=1,
    temp_en=1,
    osr_p=1,
    osr_t=1,
    odr_sel=5,
    fifo_mode=1,
    fifo_press_en=1,
    fifo_temp_en=1,
    fifo_time_en=0,
    fifo_subsampling=1,
    fifo_stop_on_full=0,
)

# Read fifo_data InfoUnit (not recommended)
print("\n" + "-" * 20 + "\n")
for _ in range(10):
    print(sensor.data_read("fifo_data"))
    time.sleep_ms(10)
```

[→ 10-fifo.py](./examples/10-fifo.py)

But the output is not very pleasant. It comes in a nested dictionary. The first layer is the  regular dictionary that comes from `data_read`, and the second contains all InfoUnits inside the received frame. Something like this will come out:

```output
{'fifo_data': {'frameiu_config_change': None}}
{'fifo_data': {'frameiu_press_and_temp': (91116.27, 29.47223)}}
{'fifo_data': {'frameiu_config_change': None}}
{'fifo_data': {'frameiu_press_and_temp': (91120.9, 29.47223)}}
{'fifo_data': {'frameiu_press_and_temp': (91119.59, 29.47679)}}
```

The information is there but it's not very user-friendly. Furthermore, I cannot guarantee that you will get all the frames in the FIFO reading it like this. It may work because of how the device handles partial transmissions and retransmissions of frames.

You will also generate unnecessary traffic in the serial bus, because the FIFO can (and should) be read in bursts, not one frame at a time, to be more efficient.

I wanted to show you that there's a regular InfoUnit attached to the FIFO data output, but **this is definitely not the way to access the FIFO**.

### Inspect RAW FIFO content (not recommended)

There is another way to access FIFO data which **is also not recommended**, and should be avoided unless you know what you are doing.

The driver has a fifo mirror where it dumps the contents of the device FIFO. The method `_fifo_sync()`, while not part of the public API, copies the contents of the driver FIFO to the mirror, which can be inspected to analyze the raw content.

```python
# Inspect RAW FIFO contents (not recommended)
print("\n" + "-" * 20 + "\n")
sensor.fifo_flush()  # Clear FIFO
time.sleep_ms(100)  # Wait for FIFO to fill
nb = sensor._fifo_sync()  # Sync FIFO
print("RAW FIFO contents:")
print(sensor._fifo_mirror[:nb])
```

[→ 10-fifo.py](./examples/10-fifo.py)

And you will see something as useful as this:

```output
RAW FIFO contents:
bytearray(b'\x94\x00\xa8\x84\x00\\w\x94\x00\xa9\x84\x00\\w\x94\x00\xaa\x84\x00\\w\x94\x00\xa8\x84\x00_w\x94\x00\xa9\x84\x00^w\x94\x00\xa9\x84\x00^w\x94\x00\xa8\x84\x00^w\x94\x00\xa7\x84\x00]w\x94\x00\xa8\x84\x00`w\x94\x00\xa9\x84\x00^w\x94\x00\xa9\x84\x00^w\x94\x00\xa8\x84\x00`w\x94\x00\xa9\x84\x00^w\x94\x00\xa8\x84\x00^w\x94\x00\xaa\x84\x00^w\x94\x00\xaa\x84\x00`w\x94\x00\xa9\x84\x00\\w\x94\x00\xaa\x84\x00^w\x94\x00\xab\x84\x00_w\x94\x00\xa9\x84\x00`w\x94\x00\xa9\x84')
```

Like with the previous method, I just want to let you know is there, but don't use it unless you know what you are doing.

### fifo_debug()

While being for debugging, it can be very handy when learning how the FIFO works, especially to see how the device handles config changes, errors, partial transmissions and FIFO over reads. It shows a graphical representation of the type of frames inside the FIFO.

```python
# Use fifo_debug() to see a 'graphical' representation of the FIFO contents
print("\n" + "-" * 20 + "\n")
sensor.fifo_flush()  # Clear FIFO
# Now we make some changes in config to see how it affects the FIFO
time.sleep_ms(50)
sensor.config_write(fifo_press_en=0, print_result=False)
time.sleep_ms(50)
sensor.config_write(fifo_press_en=1, fifo_temp_en=0, print_result=False)
time.sleep_ms(50)
sensor.config_write(fifo_subsampling=4, print_result=False)
time.sleep_ms(50)
sensor.config_write(fifo_press_en=1, fifo_temp_en=1, press_en=0, print_result=False)
time.sleep_ms(50)
# You will usually simply use `fifo_debug()`, but here we explicitly tell how many
# bytes we want to read to overshoot a little bit and get some empty frames at the end
sensor.fifo_debug(sensor.fifo_length() + 16)
```

[→ 10-fifo.py](./examples/10-fifo.py)

You will get something like this:

```output
FIFO frames representation (see legend below):
BBBBBBBBBBBTTTTTTTTTTTTPPPPPPPPPPPPPCPPBCTTTS00000000

PARAMETER                LEGEND    FIFO_STATS 
FRAME_CONFIG_CHANGE        C           2      
FRAME_EMPTY                0           8      
FRAME_ERROR                X           0      
FRAME_PRESS                P           15     
FRAME_PRESS_AND_TEMP       B           12     
FRAME_SENSORTIME           S           1      
FRAME_TEMP                 T           15     
INVALID                    -           0      
TOTAL BYTES                -          228     
TOTAL ERRORS               -           0      
TOTAL FRAMES               -           53
```

This view offer you the FIFO content at a glance (first row of letters) and some stats about the FIFO contents.

While this is a useful method if you are trying to use the FIFO on your own, you still won't probably need it if you stick to the last two access methods I'm going to show you, which corresponds to more high level ways to access the FIFO.

### fifo_read()

This is the first proper way to access the FIFO. It reads the FIFO frames, decodes them and offer them to the user as a generator. Each frame is yielded as a namedtuple with two fields: `type`, with the type of frame and `payload`, which contains the information available.

This generator comes handy when you want to process all available frames in the FIFO every time you read it.

The information available depends on the type of frame and the driver does not discard any frame, not even special frames, like empty frames or config change frames, so caller must check the type to interpret the information correctly. This method offers the user almost complete control of the frame processing while sparing him from the actual decoding, but the user must also actively manage the FIFO and decide what to do with each frame and periodically read the FIFO to avoid overflows.

```python
sensor.fifo_flush()  # Clear FIFO
time.sleep_ms(50)
for frame in sensor.fifo_read():
    print(frame)
```

[→ 10-fifo.py](./examples/10-fifo.py)

This just print all frames available in the fifo already decoded:

```output
Frame(type='FRAME_TEMP', payload=28.95177)
Frame(type='FRAME_TEMP', payload=28.93351)
Frame(type='FRAME_SENSORTIME', payload=18274)
Frame(type='FRAME_EMPTY', payload=None)
Frame(type='FRAME_EMPTY', payload=None)
```

We can add some processing to make a simple frame counter as an example:

```python
data_frames = sensortime_frames = other_frames = 0
sensor.fifo_flush()  # Clear FIFO
time.sleep_ms(50)
sensor.config_write(fifo_subsampling=1, press_en=1, print_result=False)
time.sleep_ms(100)
print("Frame counter")
for frame in sensor.fifo_read():
    if frame.type in ("FRAME_TEMP", "FRAME_PRESS", "FRAME_PRESS_TEMP"):
        data_frames += 1
    elif frame.type == "FRAME_SENSORTIME":
        sensortime_frames += 1
    else:
        other_frames += 1
print(f"Data frames: {data_frames}")
print(f"Sensortime frames: {sensortime_frames}")
print(f"Other frames: {other_frames}")
```

[→ 10-fifo.py](./examples/10-fifo.py)

```output
Frame counter
Data frames: 25
Sensortime frames: 1
Other frames: 2
```

This is a very simple example, but you can see how you can process the frames as they come and do whatever you want with them. Depending on your application, this frame by frame processing may be necessary or not. For example, if you plan to dynamically change the FIFO configuration, you will need to process the config change frames to know what has changed and act accordingly.

This method is simple yet allows the user full control over what to do with every frame. Just remember that you must periodically read the FIFO to avoid overflows.

### Use fifo_auto_queue() to automatically process the FIFO

The `fifo_auto_queue()` method offers the highest level of abstraction, making it ultra simple for the user to use the device FIFO. It returns a `BMP3XXFIFO` object that handles the FIFO for the user.

This `BMP3XXFIFO` class is intended to allow the user to use the device FIFO from a high level, hiding all the details of frame decoding and queue management. The user should be able to simply gather continuous data from the device FIFO using the `get` method, knowing that, unless some major thing happens, you will not be losing samples.

It builds on top of the lower level `fifo_read` method from the BMP3XX class and performs automatic pulls from the device FIFO when needed. **It also discards all special frames, leaving only valid and decoded data frames in the queue**

Note that it abstracts out some details from the user. If the user needs a more precise control of what frames are being received and what to do with them, then the `fifo_read` method should be directly used instead and frames processed one by one.

The `get()` method returns a `SensorData` named tuple that contains pressure, temperature and altitude information when applicable or `None`.

```python
sensor.fifo_flush()  # Clear FIFO
queue = sensor.fifo_auto_queue()
for _ in range(10):
    print(queue.get())
```

```output
SensorData(press=91225.8, temp=28.89242, alt=876.437)
SensorData(press=91227.83, temp=28.90155, alt=876.2521)
SensorData(press=91227.83, temp=28.90155, alt=876.2521)
SensorData(press=91227.83, temp=28.90155, alt=876.2521)
None
SensorData(press=91229.88, temp=28.91068, alt=876.0672)
SensorData(press=91225.25, temp=28.91068, alt=876.4871)
SensorData(press=91221.91, temp=28.90611, alt=876.7882)
None
None
```

Individual fields of the SensorData namedtuple can be accessed with the standard dot notation:

```python
data = queue.get()
data.press  # Pressure
data.temp  # Temperature
data.alt  # Altitude
```

In the output above, you can notice that `get()` returns `None` when there is no new data available in the queue. The `BMP3XXFIFO` object will automatically pull new data from the device FIFO when needed, so the user does not need to worry about it. For example, if the local queue is empty it will always try to fetch additional data from the device FIFO until the local queue is full again, but if the device FIFO is also empty, then `get()` will return `None` until new data is available.

The `BMP3XXFIFO` will also fetch new data from the device FIFO when the local queue is not empty but the falls below a certain threshold and enough time has passed since last pull. You can take a look at the implementation of the `BMP3XXFIFO` class in the [bmp3xx.py](./bmp3xx.py) file if you want to know more about the details.

If the user takes care of the `None` values returned by `get()` and does not try to process them, then the user can be sure that he will not lose any data from the device FIFO, and doesn't need to worry much about the details of the FIFO management or polling frequency.

This example can handle the queue indefinitely, printing the data as it comes:

```python

TODO more details about fifo_auto_queue
TODO Interrupts
TODO Complete example using interrupts and queue

