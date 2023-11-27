import time
from bmp3xx import BMP3XX
from machine import Pin, I2C

# I2C, use correct pins for your board and wiring
i2c = I2C(0, scl=Pin(9), sda=Pin(8))
sensor = BMP3XX(i2c)

print("\n" + "-" * 20 + "\n")
print(f"Altitude before calibration {sensor.alt} m")
print("\n" + "-" * 20 + "\n")
print("Now let's calibrate the altimeter using the local altitude")
# Use your real local altitude here
sensor.calibrate_altimeter(local_alt=900)
print(f"Altitude after calibration {sensor.alt} m")
print("\n" + "-" * 20 + "\n")
print("Now let's calibrate the altimeter using the local sea level pressure")
# Use your real local sea level pressure here
sensor.calibrate_altimeter(local_press=90750)
print(f"Altitude after calibration {sensor.alt} m")

# Relative altitude calibrating at 0m
print("\n" + "-" * 20 + "\n")
print("Calibrating to 0m")
sensor.calibrate_altimeter(local_alt=0)
for _ in range(5):
    print(f"Relative altitude {sensor.alt} m")
    time.sleep(3)
