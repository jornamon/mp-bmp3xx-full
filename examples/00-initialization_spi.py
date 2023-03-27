"""
Initializing the device is easy, you just have to import the BMP3XX class
and instantiate the sensor providing a valid BUS object, which can be a I2C
object or an SPI object.
"""
"""
In the case of SPI you must supply the Chips Select (CS) pin as the 
spi_cs keyword argument, which must be a machine.Pin object.
"""
from bmp3xx import BMP3XX
from machine import Pin, SPI

# SPI, chose correct pins for your board and wiring
SCK = Pin(36)
MOSI = Pin(35)
MISO = Pin(37)
CS = Pin(12)
SPI_N = 2
spi = SPI(SPI_N, sck=SCK, mosi=MOSI, miso=MISO)

sensor = BMP3XX(spi, debug_print=False, spi_cs=CS)

print(sensor.all)
