# Keiser BLE GAP to ANT+

This project listens to Keiser M series BLE broadcast ([GAP spec](https://dev.keiser.com/mseries/direct/)) and retransmit them in ANT+ compatible profiles. ANT+ specs can be obtained but not distributed at [here](https://www.thisisant.com/my-ant/join-adopter/).

## Hardware requirement
+ A BLE compatible receiver
+ An ANT+ transceiver like
    + `ANT-USB`
    + `ANT-USBm` (based on NRF 24L01P)
    + Or other ones supports Ant+ Tx

It is believed that CYCPLUS branded ones do not work.

## Dependencies
```
python-ant
bleak
```

## System Design

There are two modules works asynchronously:
+ Keiser Data Listener: `kl`, scans BLE advertisements and filter the data to find `bike_id` of interest.
+ ANT+ Data Transmitter: `ant_tx`, transmits data pages ~~~in 4Hz.~~~ whenever there is a fresh data fed from `kl`.

And there is a converter `kl2ant` that transform from `kl` into `ant_tx` that conforms the ANT+ specs.

For BLE(GATT) Tx, there is a separate `ble_tx` and `kl2ble` for use with shared `kl`.