# Bike Data Hub

This project is very similar to [ptx2/gymnasticon](https://github.com/ptx2/gymnasticon). Instead of JavaScript, it is written in Python. 
It adds BikeID selection for Keiser and adds speed page for ANT transmission.
In addition, the developer strives to deliver a well-thought design for logically sensible modules and developer friendly concepts as a thought exercise.

Originally this project is hosted under two separately projects [Keiser2GATT](https://github.com/tao-j/Keiser2GATT) and [Keiser2ANT](https://github.com/tao-j/Keiser2ANT) that are in succession of [Keiser2Garmin](https://github.com/tao-j/Keiser2Garmin).

## System Design

There are two modules works asynchronously: 
+ `bike`: Receives sensor data or generates simulated data.
  + Emits a signal when new readings are available
  + Data truncating and conversion should not be done here
+ `tx`: Sends the data in BLE or ANT protocol defined format.
  + Value truncation is performed here
  + Either sends the data in 4Hz or whenever a condition is triggered.
   + TODO: if there is no data received in 2 seconds, they should stop transmitting.

The converter `tx.conv` transforms from various `bike` raw data into values `tx` uses. It should work in floating numbers and leave the truncation and rouding to the last stage. Here, the conversion may include algorithms that infer the required values defined by specs but not available directly in readings. Examples are:
+ CounterGenerator: see its docstring
+ Estimate speed from power
+ Estimate wheel revolution from speed


## Bikes
TODO: each bike class could be derived from base classes indicating the type of raw data they provide, such as Power, Cadence, Speed, Rev Event, etc.

### Simulation

### Keiser
Keiser M series BLE broadcast has a public ([spec](https://dev.keiser.com/mseries/direct/)). Those bikes transmit readings in GAP messages. The BikeID of interest can be set.

Other bikes can be added as later.


## Data Transmission

### ANT+

Implemented Profiles:
+ Bicycle Power
  + Sends Power and Cadence
+ Bicycle Speed and Cadence
  + Speed only device is implemented, whilee Speed and Cadence or Cadence only device are availble.
+ TODO: Fitness Machine

ANT+ specs can be obtained by simply register [here](https://www.thisisant.com/my-ant/join-adopter/).

#### Hardware requirement
+ An ANT+ transceiver
    + `ANT-USB`
    + `ANT-USBm` (based on NRF 24L01P)
    + Or other ones supports Ant+ Tx (needs simple code change to add raw serial)

It is believed that CYCPLUS branded ones do not work.

Be sure to close and clean up the channels opened before exiting, otherwise next time opening the device it will throw an exception: `usb.core.USBError: [Errno 75] Overflow`.

### Bluetooth (BLE GATT)

Implemented Profiles:
+ CP: Cycling Power
  + Only Power is sent
+ CSC: Cycling Speed and Cadence
+ FTMS: Fitness Machine
  + TODO

The Bluetooth SIG pdf specs are not that helpful. But xml files circulating over the internet are useful.

#### Compatibility Test
+ watchOS 10: CSC/CP works. But sometimes it is unable to setup the wheel dimension, sensor name is not showing correctly.
+ Garmin: Can only connect to one service either CSC or CP. When CSC is connected, and the wheel feature bit is set, then the wheel diameter can be set. If crank revolution data bit is set then it is unable to set wheel diameter regardless of the presence of wheel data. The trick is to add an empty SC control point. CP works if only sending power data.
+ Zwift: CSC/CP can be picked up, but displays no data on iOS, but works on Android.
+ nRF Toolbox: CSC is supported. However, it seems that this program ignores the timestamp and if there is a duplicate message with the same reading, it will estimate the speed/cadence as 0. Also, it requires a Battery Service implemented to connect.

#### Related info
+ Linux uses `dbus` to manage `bluez`. [`bluez-peripheral`](https://github.com/spacecheese/bluez_peripheral) is a wrapper abstracts peripheral role devices. Quick concept overview of dbus [by bootlin](https://bootlin.com/pub/conferences/2016/meetup/dbus/josserand-dbus-meetup.pdf)
+ Bluetooth specs are useless and the Bluetooth SIG hides the actual bits definition xml files. Fortunately there is some accessible [backup on Github](
https://github.com/oesmith/gatt-xml/blob/master/org.bluetooth.characteristic.cycling_power_measurement.xml). 
+ The cross-platform solution `bless` has trouble advertising several GATT profiles on Linux. If two profiles are defined, only one profile can be read by nRF connect. In light of this, `bluez-peripheral` is used.
+ [1](https://ihaque.org/posts/2021/01/04/pelomon-part-iv-software/) [2](https://github.com/olympum/ble-cycling-power) [3](https://teaandtechtime.com/arduino-ble-cycling-power-service). [4](https://github.com/PunchThrough/espresso-ble/blob/master/ble.py) [5](https://github.com/Jumperr-labs/python-gatt-server/blob/master/gatt_server.py)



## Alternate Solutions on MCU
To do it another way, BLE only, actually in Circuit Python can be used, which does not support generic Linux host at the moment. `ESP32-S3` or old `ESP32` or others can be used.

In order to transmit the ANT+ signals other than a fully fledged system, `nRF52840` might be a good choice, but its soft device licensing can be troublesome.
