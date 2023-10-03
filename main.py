from typing import Union
from bluez_peripheral.gatt.service import Service, ServiceCollection
from bluez_peripheral.gatt.characteristic import (
    characteristic,
    CharacteristicFlags as CharFlags,
)
from bluez_peripheral.util import *
from bluez_peripheral.advert import Advertisement
from bluez_peripheral.agent import NoIoAgent
import asyncio

import struct

from bluez_peripheral.util import Collection
from bluez_peripheral.uuid import BTUUID as UUID

# cycling speed and cadence
CSC_UUID = "1816"
CSC_MEASUREMENT_UUID = "2A5B"
CSC_FEATURE_UUID = "2A5C"

# cycling power
CP_UUID = "1818"
CP_MEASUREMENT_UUID = "2A63"
CP_FEATURE_UUID = "2A65"

SENSOR_LOCATION_UUID = "2A5D"

# device information
DI_UUID = "180A"
DI_SYSTEM_ID_UUID = "2A23"
DI_MODEL_NUMBER_UUID = "2A24"
DI_SERIAL_NUMBER_UUID = "2A25"
DI_FIRMWARE_REVISION_UUID = "2A26"
DI_HARDWARE_REVISION_UUID = "2A27"
DI_SOFTWARE_REVISION_UUID = "2A28"
DI_MANUFACTURER_NAME_UUID = "2A29"


CSC_F_BIT_WHEEL_REVOLUTION_DATA_PRESENT = 0b0000_0001
CSC_F_BIT_CRANK_REVOLUTION_DATA_PRESENT = 0b0000_0010

# feature flags
CP_F_BIT_WHEEL_REVOLUTION_DATA_PRESENT = 0b0001_0000
CP_F_BIT_CRANK_REVOLUTION_DATA_PRESENT = 0b0010_0000
# measurement flags
CP_M_BIT_WHEEL_REVOLUTION_DATA_PRESENT = 0b0000_0100
CP_M_BIT_CRANK_REVOLUTION_DATA_PRESENT = 0b0000_1000


class DeviceInformationService(Service):
    def __init__(self):
        super().__init__(DI_UUID)

    @characteristic(DI_SYSTEM_ID_UUID, CharFlags.READ)
    def system_id(self, options):
        return struct.pack("<Q", *[0x0000022001100000])

    @characteristic(DI_MODEL_NUMBER_UUID, CharFlags.READ)
    def model_number(self, options):
        return bytearray(b"Keiser M to GATT")

    @characteristic(DI_SERIAL_NUMBER_UUID, CharFlags.READ)
    def serial_number(self, options):
        return bytearray(b"12345678")

    @characteristic(DI_FIRMWARE_REVISION_UUID, CharFlags.READ)
    def firmware_revision(self, options):
        return bytearray(b"0.0.1")

    @characteristic(DI_HARDWARE_REVISION_UUID, CharFlags.READ)
    def hardware_revision(self, options):
        return bytearray(b"0.1.1")

    @characteristic(DI_SOFTWARE_REVISION_UUID, CharFlags.READ)
    def software_revision(self, options):
        return bytearray(b"1.0beta")

    @characteristic(DI_MANUFACTURER_NAME_UUID, CharFlags.READ)
    def manufacturer_name(self, options):
        return bytearray(b"t-j")


class CPService(Service):
    def __init__(self):
        self.measure_flags = (
            0x0
            # | CP_M_BIT_CRANK_REVOLUTION_DATA_PRESENT
            | CP_M_BIT_WHEEL_REVOLUTION_DATA_PRESENT
        )
        self.feature_flags = (
            0x0 
            # | CP_F_BIT_CRANK_REVOLUTION_DATA_PRESENT
            | CP_F_BIT_WHEEL_REVOLUTION_DATA_PRESENT
        )
        super().__init__(CP_UUID, primary=True)

    @characteristic(CP_MEASUREMENT_UUID, CharFlags.NOTIFY | CharFlags.READ)
    def cp_measurement(self, options):
        pass

    def notify_new_rate(self, power, time_in_ms, wheel_rev, crank_rev):
        rate = struct.pack(
            "<HhIH",
            *[
                self.measure_flags,
                power & 0x7FFF,
                wheel_rev & 0xFFFFFFFF,
                (2 * time_in_ms) & 0xFFFF,
                # crank_rev & 0xFFFF,
                # time_in_ms & 0xFFFF,
            ],
        )
        self.cp_measurement.changed(rate)

    @characteristic(CP_FEATURE_UUID, CharFlags.READ)
    def cp_feature(self, options):
        return struct.pack("<I", *[self.feature_flags])

    @characteristic(SENSOR_LOCATION_UUID, CharFlags.READ)
    def sensor_location(self, options):
        return bytearray(b"\x0d")


class CSCService(Service):
    def __init__(self):
        super().__init__(CSC_UUID, True)
        self.feature = (
            CSC_F_BIT_WHEEL_REVOLUTION_DATA_PRESENT
            # |  CSC_F_BIT_CRANK_REVOLUTION_DATA_PRESENT
        )

    @characteristic(CSC_MEASUREMENT_UUID, CharFlags.NOTIFY | CharFlags.READ)
    def csc_measurement(self, options):
        pass

    def notify_new_rate(self, wheel_rev, crank_rev, time_in_ms):
        rate = struct.pack(
            "<BIH",
            # "<BHH",
            self.feature,
            wheel_rev & 0xFFFFFFFF,
            time_in_ms & 0xFFFF,
            # crank_rev & 0xFFFF,
            # time_in_ms & 0xFFFF,
        )
        self.csc_measurement.changed(rate)

    @characteristic(CSC_FEATURE_UUID, CharFlags.READ)
    def csc_feature(self, options):
        return struct.pack("<H", *[self.feature])

    @characteristic(SENSOR_LOCATION_UUID, CharFlags.READ)
    def sensor_location(self, options):
        return bytearray(b"\x0d")


import time


async def main():
    # system busmfrom dbus_next.
    bus = await get_message_bus()

    csc_service = CSCService()
    cp_service = CPService()
    di_service = DeviceInformationService()
    svcs = ServiceCollection([cp_service])
    await svcs.register(bus)
    # await csc_service.register(bus)

    # An agent is required to handle pairing
    agent = NoIoAgent()
    # This script needs superuser for this to work.
    await agent.register(bus)

    adapter = await Adapter.get_first(bus)
    print(await adapter.get_address())

    # Start an advert that will last for 60 seconds.
    advert = Advertisement("KeiserGAP2GATT CSC CP", [CP_UUID], 0x0480, 0)
    await advert.register(bus, adapter)

    import random

    last_t = time.time()
    wheel_rev = 1
    crank_rev = 1
    rev = 0
    interval = 0.1
    while True:
        await asyncio.sleep(interval)
        this_t = time.time() - last_t
        time_in_ms = int(this_t * 1024)
        power = random.randint(120, 130)

        # rev += (60. + int(this_t) % 20) / 60 * interval
        rev += interval
        wheel_rev = int(rev)
        crank_rev = int(rev)
        print(rev, this_t, wheel_rev, crank_rev, time_in_ms)
        csc_service.notify_new_rate(
            wheel_rev=wheel_rev, crank_rev=crank_rev, time_in_ms=time_in_ms
        )
        cp_service.notify_new_rate(
            power=power, wheel_rev=wheel_rev, crank_rev=crank_rev, time_in_ms=time_in_ms
        )
        # print("updated", rev, end="\r")
        # Handle dbus requests.

    await bus.wait_for_disconnect()


if __name__ == "__main__":
    asyncio.run(main())
