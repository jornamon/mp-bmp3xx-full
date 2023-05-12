import time
from bmp3xx import BMP3XX
from machine import Pin, I2C

# I2C, use correct pins for your board and wiring
i2c = I2C(0, scl=Pin(9), sda=Pin(8))
sensor = BMP3XX(i2c)

"""
This driver allows you to read and write every piece of meaningful 
information on the device.

There are lots of information you can read and write from/to
the device. The absolute best place to know want can you read and
write from/to the device is the datasheet, which I recommend you 
to read if you want to go beyond the basics.

Nonetheless, you can check from the REPL (or from your script) for
basic info about what pieces of information (InfoUnits) are available
on the device.

`sensor.info()` or `sensor.info('sensor')` give you general
information about the Sensor, providing the names of available config
and data registers and config and data InfoUnits.

InfoUnits are what you read or write to get readings, current config
or change the configuration of the device. We will see how to do that 
in the next example. In general, config InfoUnits can be read or written,
data InfoUnits can be read.
"""
print()
print("-" * 50)
sensor.info()
print("-" * 50)
print()
"""
You can get a little bit more detailed information about Registers,
Frames and InfoUnits by executing `sensor.info('registers')`, 
`sensor.info('frames')` or `sensor.info('infounits')` respectively.
"""
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
