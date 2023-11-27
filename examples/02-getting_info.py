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
