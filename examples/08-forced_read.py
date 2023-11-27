import time
from bmp3xx import BMP3XX
from machine import Pin, I2C

# I2C, use correct pins for your board and wiring
i2c = I2C(0, scl=Pin(9), sda=Pin(8))
sensor = BMP3XX(i2c)

# Normal read
print("\n" + "-" * 20 + "\n")
print("Taking several fast consecutive measurements in normal mode")
sensor.config_write(odr_sel=160, osr_p=16, osr_t=2, print_result=False)
start = time.ticks_ms()
for _ in range(10):
    print(sensor.press)
stop = time.ticks_ms()
elapsed = time.ticks_diff(stop, start)
print(f"Elapsed time: {elapsed} ms")

# Forced read
print("\n" + "-" * 20 + "\n")
print("Now we will repeat the same measurements but using forced_read")
start = time.ticks_ms()
for _ in range(10):
    print(sensor.forced_read().press)
stop = time.ticks_ms()
elapsed = time.ticks_diff(stop, start)
print(f"Elapsed time: {elapsed} ms")
