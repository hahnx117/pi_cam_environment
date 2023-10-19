# pi_cam_environment

First activate the I2C port in `raspi-config`

## Equipment
+ Raspberry Pi 4 2GB
+ Qwiic Hat
+ BMP 390 Temp and Pressure Sensor
    + `python3 -m pip install adafruit-circuitpython-bmp3xx`
        + NOTE: must have `python3-dev` installed first.
+ LTR-329 Light Sensor
    + `python3 -m pip install install adafruit-circuitpython-ltr329-ltr303`
+ LSM303AGR Accelerometer and Magnetometer
    + `python3 -m pip install install adafruit-circuitpython-lis2mdl`
+ Raspberry Pi Cam 3 Wide

NOTE: The `pip` packages should be in the Docker container anyway.

