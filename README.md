This tries to implement a translator from Keiser BLE GAP message to a BLE GATT fitness sensor.

Currently it does not work since:

+ There is some issue in `bless` that prevents advertising several GATT profiles. In `main.py` defined two profiles, but only one profile can be read by `nRF connect` app on phone during testing.
+ Has to reimplement the GAPP fitness profile while `bless` does not ship them but `bleak` has parsing library, which makes it a process of reinvent the wheel. In addition, most Garmin device does not take those profiles, even if for the simple power sensor(not sure though).
+ To do it fast, actually in Circuit Python can be used `ada.py`, which does not support generic Linux host at the moment. `ESP32-S3` or old `ESP32` or others can be used.