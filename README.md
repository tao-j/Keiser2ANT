# OpenFitness Data Adapter

A bridge to connect fitness equipment with sports watches and apps, providing advanced workout metrics beyond basic heart rate data.

For example, you can:
- Get cadence and power data from spinning bikes
- Get speed and incline data from treadmills
- And more!

## Features
- Small formfactor device with internal chargable battery lasting long. 128x64 dots OLED display, buttons for operation.
- Connect to various fitness equipment (spinning bikes, treadmills, steppers, etc.)
- Receive proprietary BLE messages from equipment using non-standard protocols
- Receive data from ANT+ protocol devices
- Transmit data in standardized BLE formats supported by modern sports watches (Apple Watch, Garmin, etc.) and apps
- Transmit data in ANT+ protocol to support Garmin and other ANT+ devices

# Current Implementation and Similar Solutions (Linux required)

[ptx2/gymnasticon](https://github.com/ptx2/gymnasticon) was an earlier project implementing similar functionality, which appears to have been adapted by [k2pi](https://k2pi.company.site/) for their $80-100 commercial product. However, their solution has limited features and is relatively bulky with higher power consumption.

Due to the original JavaScript project's large codebase and unmaintained BLE stack, we've developed this Python-based implementation for better maintainability and extensibility. Our solution adds Keiser bike ID selection and ANT+ speed data transmission.

The current implementation runs on Linux systems using a USB dongle for ANT+ signal transmission, successfully interfacing with both Garmin devices (via ANT+) and Apple Watch (via BLE).

# Hardware Implementation Options
## MCU Selection Analysis

### Option 1: nRF52840
The nRF52840 offers integrated ANT+ and BLE capabilities, making it a strong candidate for this project. Key considerations:
- Requires $1600 one-time license fee and regulatory approval for ANT+ stack
- Development-friendly options available through Adafruit:
  - [nRF52840 board](https://www.adafruit.com/product/4062)
  - [OLED display](https://www.adafruit.com/product/4650)
  - [Battery management](https://www.adafruit.com/product/3898)

Potential licensing workaround:
- Distribute base firmware with BLE only
- Provide optional ANT+ stack firmware update for evaluation purposes
- Note: This approach may have legal implications

### Option 2: nRF52832 (ANT D52 Module)
A cost-effective solution with pre-certified components:
- D52 BOM cost: ~$10
- No license fees
- Pre-approved regulatory certification
- Requires Garmin distribution agreement (free)
- Reference: [D52 Module](https://www.arrow.com/en/products/d52md2m8ia-tray/dynastream-innovations)

Limitations:
- No pre-made breakout boards available
- Manual assembly required
- SoftDevice S332 required for combined BLE/ANT+ functionality, and using Nordic nRF52 SDK is very painful.

### Option 3: nRF24AP2 + ESP32-S3
A modular approach combining separate chips:
- nRF24AP2 (~$5): ANT+ capabilities
  - No license fees
  - NRND status may affect availability
  - Serial interface simplifies integration
- ESP32-S3 (~$5): Main processor
  - Provides BLE and WiFi connectivity
  - Handles core processing tasks

Considerations:
- Requires careful antenna design
- Total solution cost competitive with other options
- More complex PCB design but simpler software stack

# Design notes for the proof of concept

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
    + `ANT-USBm` (based on nRF24L01P?)
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
