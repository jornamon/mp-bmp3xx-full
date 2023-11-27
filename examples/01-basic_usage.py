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
