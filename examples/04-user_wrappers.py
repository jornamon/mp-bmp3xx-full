from bmp3xx import BMP3XX
from machine import Pin, I2C

# I2C, use correct pins for your board and wiring
i2c = I2C(0, scl=Pin(9), sda=Pin(8))
sensor = BMP3XX(i2c)

# Wraping data_read
def press_data_ready(sensor: BMP3XX):
    return sensor.data_read("drdy_press", print_result=False)["drdy_press"]


# Wraping config_read
def get_press_oversampling(sensor: BMP3XX):
    return sensor.config_read("osr_p", print_result=False)["osr_p"]


# Wraping config_write
def set_press_oversampling(sensor: BMP3XX, value: int):
    sensor.config_write(osr_p=value, print_result=False)


print("Press data ready:", press_data_ready(sensor))
sensor.press # Read pressure to clean data ready flag
print("Press data ready:", press_data_ready(sensor))
print("Press oversampling:", get_press_oversampling(sensor))
print("Setting press oversampling to 4")
set_press_oversampling(sensor, 4)
print("Press oversampling after new config:", get_press_oversampling(sensor))
