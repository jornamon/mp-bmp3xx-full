import time
from bmp3xx import BMP3XX
from machine import Pin, I2C

# I2C, use correct pins for your board and wiring
i2c = I2C(0, scl=Pin(9), sda=Pin(8))
sensor = BMP3XX(i2c)

"""
Besides basic use, you can use three powerful method to read/write
any InfoUnit you wish from the device.

This tools are:
- data_read('InfoUnit1', 'InfoUnit2',...) returns a dictionary with the 
values of all requested data InfoUnits.
- config_read('InfoUnit1', 'InfoUnit2',...) returns a dictionary with the 
values of all requested config info units.
- config_write(InfoUnit1=value1, InfoUnit2=value2,...) returns a dictionary with the 
values of all requested config info units.

Let's see some examples

Read `pressure` and `power-on-or-reset` flag, which informs 
you if the device has been rebooted since the last time you checked this flag. 
Try turning off and on to the *sensor*, not the board, to see the effect.
`por_detected` can be a useful InfoUnit to detect device reboots.
"""
for i in range(3):
    data = sensor.data_read("press", "por_detected", "mode")
    print()
    print(f"Current pressure = {data['press']}")
    print(f"Device restarted since last checked = {bool(data['por_detected'])}")
    time.sleep_ms(100)

"""
Now let's do it with some configuration options. Let's read the following device
config parameters:
- Pressure Oversampling
- Temperature Oversampling 
- Power mode
- IIR filter

You can enable or disable printing the results in a nice tabulated way with the 
argument `print_result=True`
"""
print("\nRead some config parameters")
config = sensor.config_read("osr_p", "osr_t", "mode", "iir_filter", print_result=True)

"""
You can alter the device confituration with `config_write`.
It takes parameters (InfoUnits name strings) as kwargs and update config accordingly.
update = True  -> Updates only the provided parameters, using current config as base.
update = False -> Takes parameters defaults, updates it with provided parameters and applies it.
Returns the applied config.

For example, we can update current configuration to set IIR filter order to 32 and 
pressure oversampling to 4:
"""

print("\nSet iir and press oversampling with update=True (default)")
sensor.config_write(iir_filter=32, osr_p=4, osr_t=2)

"""
Unless you suppress printing with print_result=False, `config_write` will show you the 
previous configuration (config on the device before this change), the base configuration
(which can be the current config or the InfoUnit defaults depending ont the `update` parameter,
which defaults to True), the requested config and the new config.

This allows you to easily spot if the command is having the effects you want.
"""
"""
`config_read` without parameters returns complete current sensor config. Lets run it,
apply the same config change with the `update` parameter set to False (takes InfoUnit
defaults instead of current config), run `config_read` again and compare the results.
`config_write` only changes the configuration of the affected Registers (those that
contain the InfoUnits you are changing), so the rest of the config remains the same.

The default value for the InfoUnits is in the `bmp3xx_data_structure.py` file.
"""

print("\nComplete config")
sensor.config_read(print_result=True)
print("\nSet iir and press oversampling again but with update=False")
sensor.config_write(iir_filter=32, osr_p=4, update=False)
print("\nComplete config")
sensor.config_read(print_result=True)

"""Check how `osr_t` has changed from 2 to 1, as it is the default value,
even if we didn't change it. This InfoUnit is in the same Register as `osr_p`,
so it is affected by the change.

update=True works for incremental changes from your current configuration.
update=False works for setting a new configuration from scratch without having to 
take care of the values for InfoUnits you are not changing."""
