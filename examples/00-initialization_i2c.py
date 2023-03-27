"""
Initializing the device is easy, you just have to import the BMP3XX class
and instantiate the sensor providing a valid BUS object, which can be a I2C
object or an SPI object.
"""

from bmp3xx import BMP3XX
from machine import Pin, I2C

# I2C
i2c = I2C(0, scl=Pin(9), sda=Pin(8))  # Depends on your board
sensor = BMP3XX(i2c)

"""
This uses the default BMP3XX I2C address 0x77.
If you need to provide a different one, you must pass it
as a keyword argument, like so:
`sensor = BMP3XX(i2c, i2c_addr=0x76)`
"""

print(sensor.all)
