import time
from bmp3xx import BMP3XX
from machine import Pin, I2C

from sensor import SensorError

# I2C, use correct pins for your board and wiring
i2c = I2C(0, scl=Pin(9), sda=Pin(8))
sensor = BMP3XX(i2c)

# Check current ODR
print("\n" + "-" * 20 + "\n")
print("Getting current ODR info")
sensor.calc_odr()

# Estimate ODR from values
print("\n" + "-" * 20 + "\n")
print("Estimate ODR from values")
sensor.calc_odr(
    press_en=1,
    temp_en=1,
    osr_p=32,
    osr_t=2,
)

# Effect of osr_p on ODR an conversion time
print("\n" + "-" * 20 + "\n")
print("Effect of osr_p on ODR an conversion time")
print("OSR_P       Conv. Time       min ODR")
for osr_p in (1, 2, 4, 8, 16, 32):
    res = sensor.calc_odr(press_en=1, temp_en=1, osr_t=2, osr_p=osr_p, explain=False)
    print(f"{osr_p:5d}    {res[0]:10.2f} ms    {res[2]:7d} ms")


# ODR incompatible with current configuration
print("\n" + "-" * 20 + "\n")
print("Setting a ODR too fast should throw an exception")
sensor.softreset()
time.sleep_ms(5)
sensor.config_write(odr_sel=5, osr_p=32, osr_t=2, mode="normal")
time.sleep_ms(10)
sensor.press
