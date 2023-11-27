from bmp3xx import BMP3XX
from machine import Pin, SPI

# SPI, chose correct pins for your board and wiring
SCK = Pin(36)
MOSI = Pin(35)
MISO = Pin(37)
CS = Pin(12)
SPI_N = 2
spi = SPI(SPI_N, sck=SCK, mosi=MOSI, miso=MISO)

sensor = BMP3XX(spi, spi_cs=CS)

print("\n" + "-" * 20 + "\n")
print(sensor.all)
