# Keiser BLE GAP to ANT+

This is a proof of concept work for receiving Keiser M series bike BLE broadcast signal and retransmit them in ANT+ compatible profiles.

## Hardware requirement
+ A BLE compatible receiver
+ An ANT+ transceiver like
    + `ANT-USB`
    + `ANT-USBm` (based on NRF 24L01P)
    + Or other ones supports Ant+ Tx

It is believed that CYCPLUS one does not work.

## Dependencies
```
python-ant
bleak
```

