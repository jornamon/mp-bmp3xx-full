import time
from bmp3xx import BMP3XX
from machine import Pin, I2C

# I2C, use correct pins for your board and wiring
i2c = I2C(0, scl=Pin(9), sda=Pin(8))
sensor = BMP3XX(i2c)

print("\n" + "-" * 20 + "\n")
print("Applying indoor_navigation preset")
sensor.apply_config_preset("indoor_navigation")
sensor.config_read()

# This throws an exception, but offers a list of available presets
print("Available templates:")
sensor.apply_config_preset()
