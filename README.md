# Keiser BLE GAP to ANT+

This project listens to Keiser M series BLE broadcast (GAP) and retransmit them in ANT+ compatible profiles.

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

