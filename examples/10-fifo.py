import time
from bmp3xx import BMP3XX
from machine import Pin, I2C

# I2C, use correct pins for your board and wiring
i2c = I2C(0, scl=Pin(9), sda=Pin(8))
sensor = BMP3XX(i2c)


sensor.config_write(
    press_en=1,
    temp_en=1,
    osr_p=1,
    osr_t=1,
    odr_sel=5,
    fifo_mode=1,
    fifo_press_en=1,
    fifo_temp_en=1,
    fifo_time_en=1,
    fifo_subsampling=1,
    fifo_stop_on_full=0,
)

# Read fifo_data InfoUnit (not recommended)
print("\n" + "-" * 20 + "\n")
for _ in range(10):
    print(sensor.data_read("fifo_data"))
    time.sleep_ms(10)

# Inspect RAW FIFO contents (not recommended)
print("\n" + "-" * 20 + "\n")
sensor.fifo_flush()  # Clear FIFO
time.sleep_ms(100)  # Wait for FIFO to fill
nb = sensor._fifo_sync()  # Sync FIFO
print("RAW FIFO contents:")
print(sensor._fifo_mirror[:nb])

# Use fifo_debug() to see a 'graphical' representation of the FIFO contents
print("\n" + "-" * 20 + "\n")
sensor.fifo_flush()  # Clear FIFO
# Now we make some changes in config to see how it affects the FIFO
time.sleep_ms(50)
sensor.config_write(fifo_press_en=0, print_result=False)
time.sleep_ms(50)
sensor.config_write(fifo_press_en=1, fifo_temp_en=0, print_result=False)
time.sleep_ms(50)
sensor.config_write(fifo_subsampling=4, print_result=False)
time.sleep_ms(50)
sensor.config_write(fifo_press_en=1, fifo_temp_en=1, press_en=0, print_result=False)
time.sleep_ms(50)
# You will usually simply use `fifo_debug()`, but here we explicitly tell how many
# bytes we want to read to overshoot a little bit and get some empty frames at the end
sensor.fifo_debug(sensor.fifo_length() + 16)

# Use fifo_read() to get a list of frames
print("\n" + "-" * 20 + "\n")
sensor.fifo_flush()  # Clear FIFO
time.sleep_ms(50)
for frame in sensor.fifo_read():
    print(frame)

# Add a little bit of frame processing to fifo_read()
print("\n" + "-" * 20 + "\n")
data_frames = sensortime_frames = other_frames = 0
sensor.fifo_flush()  # Clear FIFO
time.sleep_ms(50)
sensor.config_write(fifo_subsampling=1, press_en=1, print_result=False)
time.sleep_ms(100)
print("Frame counter")
for frame in sensor.fifo_read():
    if frame.type in ("FRAME_TEMP", "FRAME_PRESS", "FRAME_PRESS_AND_TEMP"):
        data_frames += 1
    elif frame.type == "FRAME_SENSORTIME":
        sensortime_frames += 1
    else:
        other_frames += 1
print(f"Data frames: {data_frames}")
print(f"Sensortime frames: {sensortime_frames}")
print(f"Other frames: {other_frames}")

# FIFO automation with fifo_auto_queue()
print("\n" + "-" * 20 + "\n")
sensor.fifo_flush()  # Clear FIFO
queue = sensor.fifo_auto_queue()
for _ in range(10):
    print(queue.get())

# fifo_auto_queue() event loop
print("\n" + "-" * 20 + "\n")
print("BMP3XXFIFO event loop")
sensor.fifo_flush()  # Clear FIFO
queue = sensor.fifo_auto_queue()
for _ in range(30):
    data = queue.get()
    if data:
        print(f" Altitude: {data.alt:7.2f}m", end="\r")
    time.sleep_ms(500)
print(f"Altitude: {data.alt:7.2f}")
