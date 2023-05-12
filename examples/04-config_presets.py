import time
from bmp3xx import BMP3XX
from machine import Pin, I2C

# I2C, use correct pins for your board and wiring
i2c = I2C(0, scl=Pin(9), sda=Pin(8))
sensor = BMP3XX(i2c)


"""
If you don't want to decide each relevant parameter, you can use the
available config presents (templates).

Config templates are defined in `bmp3xx_data_structure.py module`. 
Most are recommended configs by the manufacturer, but you can also define your own.

To apply one, you just use the `apply_config_preset` method.
To see the available presets, you can inspect the `bmp3xx_data_structure` module,
If you call the method without arguments, it will print the available presets.
"""

print("Available templates:")
sensor.apply_config_preset()

"""
We can apply for example the `indoor_navigation` preset and check the resulting config.
Now the parameters are set to the recommended values for indoor navigation.
"""

sensor.apply_config_preset("indoor_navigation")
sensor.config_read()
