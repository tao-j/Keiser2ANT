This project attempts to implement a translator from Keiser BLE GAP message to a BLE GATT peripheral.

Currently, progress has been made from last time:
+ CSC connects to Garmin when wheel revolution is enabled, and the wheel diameter can be set. If crank revolution data bit is set then it is unable to set wheel diameter regardless of the presence of wheel data. CP is believed not compatible with Garmin.
+ CSC/CP somehow works for watchOS 10. But even a 10Hz signal with 60RPM wheel does not guarantee a smooth data display on workout app.
+ CSC/CP can be picked up by Zwift, but displays no data.

Related info
+ Linux uses `dbus` to manage `bluez`. [`bluez-peripheral`](https://github.com/spacecheese/bluez_peripheral) is a wrapper abstracts peripheral role devices. Quick concept overview of dbus [by bootlin](https://bootlin.com/pub/conferences/2016/meetup/dbus/josserand-dbus-meetup.pdf)
+ Bluetooth specs are useless and the Bluetooth SIG hides the actual bits definition xml files. Fortunately there is some accessible [backup on Github](
https://github.com/oesmith/gatt-xml/blob/master/org.bluetooth.characteristic.cycling_power_measurement.xml). 
+ [1](https://ihaque.org/posts/2021/01/04/pelomon-part-iv-software/) [2](https://github.com/olympum/ble-cycling-power) [3](https://teaandtechtime.com/arduino-ble-cycling-power-service). [4](https://github.com/PunchThrough/espresso-ble/blob/master/ble.py) [5](https://github.com/Jumperr-labs/python-gatt-server/blob/master/gatt_server.py)

Other related info:
+ There is some issue in `bless` that prevents advertising several GATT profiles. If two profiles are defined, only one profile can be read by `nRF connect` app on a phone during testing.
+ To do it another way, actually in Circuit Python can be used, which does not support generic Linux host at the moment. `ESP32-S3` or old `ESP32` or others can be used.



