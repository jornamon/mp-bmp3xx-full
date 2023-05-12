import time
from bmp3xx import BMP3XX
from machine import Pin, I2C

# I2C, use correct pins for your board and wiring
i2c = I2C(0, scl=Pin(9), sda=Pin(8))
sensor = BMP3XX(i2c)

"""
The driver offers four properties that can be directly read from the sensor:
- press: atmospheric pressure in Pascals (Pa)
- temp: temperature in degrees Celsius (C)
- alt: altitude in meters (m)
- all: all of the above inside a named tuple with fields: press, temp and alt
"""

print(f"The pressure is {sensor.press} Pascals")
print(f"The temperature is {sensor.temp} Degrees Celsius")
print(f"The altitude is {sensor.alt} meters")
print()

time.sleep_ms(100)
sd = sensor.all  # Get all available readings
print(f"All data can be pulled together as a SensorData namedtuple:\n{sd}")
print(f"Access each field: press: {sd.press}, temp: {sd.temp}, alt: {sd.alt}")
