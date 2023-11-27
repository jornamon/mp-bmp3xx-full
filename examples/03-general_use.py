import time
from bmp3xx import BMP3XX
from machine import Pin, I2C

# I2C, use correct pins for your board and wiring
i2c = I2C(0, scl=Pin(9), sda=Pin(8))
sensor = BMP3XX(i2c)

# Read some arbitrary data from the device
print("\n" + "-" * 20 + "\n")
for i in range(5):
    data = sensor.data_read("press", "por_detected", "mode")
    print()
    print(f"Current pressure = {data['press']}")
    print(f"Device restarted since last checked = {bool(data['por_detected'])}")
    time.sleep_ms(100)
    if i == 2:
        # Reset the device to notice the change in por_detected
        sensor.softreset()

# Read some configuration parameters from the device
print("\n" + "-" * 20 + "\n")
print("\nRead some config parameters")
config = sensor.config_read("osr_p", "osr_t", "mode", "iir_filter", print_result=True)

# Writing configuration parameters
print("\n" + "-" * 20 + "\n")
print("\nSet iir and press oversampling with update=True (default)")
sensor.config_write(iir_filter=32, osr_p=4, osr_t=2)

# update = True vs update = False
print("\n" + "-" * 20 + "\n")
print("\nComplete config")
sensor.config_read(print_result=True)
print("\nSet iir and press oversampling again but with update=False")
sensor.config_write(iir_filter=32, osr_p=4, update=False)
print("\nComplete config")
sensor.config_read(print_result=True)

