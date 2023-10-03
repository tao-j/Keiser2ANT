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

