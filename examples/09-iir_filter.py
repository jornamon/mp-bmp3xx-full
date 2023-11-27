from bmp3xx import BMP3XX
from machine import Pin, I2C

# I2C, use correct pins for your board and wiring
i2c = I2C(0, scl=Pin(9), sda=Pin(8))
sensor = BMP3XX(i2c)


def calculate_noise(samples):
    n = len(samples)
    mean = sum(samples) / n
    variance = sum((xi - mean) ** 2 for xi in samples) / n
    noise = variance**0.5
    return noise


iir_values = (0, 2, 4, 8, 16, 32, 64, 128)
samples = []
N = 256

sensor.config_write(
    osr_p=1,
    osr_t=1,
    odr_sel=5,
    iir_filter=0,
)

print("IIR      noise")
for iir in iir_values:
    sensor.config_write(iir_filter=iir, print_result=False)
    samples.clear()
    # Stabilize filter output
    for i in range(iir + 10):
        sensor.forced_read().press
    # Actual measures to be analyzed
    for i in range(N):
        samples.append(sensor.forced_read().press)
    print(f"{iir:3d} {calculate_noise(samples):10.2f}")
