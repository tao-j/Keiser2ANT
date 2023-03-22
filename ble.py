import asyncio
import struct
import time
import usb

from bleak import BleakScanner
from ant.core import driver, node, message, constants


class PowerData:
    def __init__(self):
        self.eventCount = 0
        self.eventTime = 0
        self.cumulativePower = 0
        self.instantaneousPower = 0
        self.cadence = 0

    def update(self, power, cadence):
        self.eventCount = (self.eventCount + 1) & 0xFF
        self.cumulativePower = (self.cumulativePower + int(power)) & 0xFFFF
        self.instantaneousPower = int(power)
        self.cadence = int(cadence) & 0xFF


class KeiserListener:
    def __init__(self, bike_id, scan_request) -> None:
        self.bike_id = bike_id & 0xFF
        self.scan_request = scan_request

    def callback(self, device, advertisement_data):
        if device.name == "M3":
            # print(advertisement_data)
            if hasattr(advertisement_data, "manufacturer_data"):
                msd = advertisement_data.manufacturer_data
                if self.parse_keiser_msd(msd):
                    self.scan_request.set()

    def parse_keiser_msd(self, msd: dict):
        for k, v in msd.items():
            if k == 0x0102 and 17 == len(v) and v[3] == self.bike_id:
                (
                    self.version_major,
                    self.version_minor,
                    self.data_type,
                    self.bike_id,
                    self.cadence,
                    self.heart_rate,
                    self.power,
                    self.calories,
                    self.minutes,
                    self.seconds,
                    self.distance,
                    self.gear,
                ) = struct.unpack("<BBB" + "BHHH" + "HBBHB", v)

                # print(f"Version Major: {version_major}")
                # print(f"Version Minor: {version_minor}")
                # print(f"Data Type: {data_type}")
                # print(f"Equipment ID: {bike_id}")
                # print(f"Cadence: {cadence}")
                # print(f"Heart Rate: {heart_rate}")
                # print(f"Power: {power}")
                # print(f"Caloric Burn: {calories}")
                # print(f"Duration Minutes: {minutes}")
                # print(f"Duration Seconds: {seconds}")
                # print(f"Distance: {distance}")
                # print(f"Gear: {gear}")
                if self.data_type == 0:
                    return True
        return False


class AntPlusTx:
    def __init__(self):
        devs = usb.core.find(find_all=True, idVendor=0x0FCF)
        for dev in devs:
            if dev.idProduct in [0x1008, 0x1009]:
                stick = driver.USB2Driver(
                    log=None,
                    debug=False,
                    idProduct=dev.idProduct,
                    bus=dev.bus,
                    address=dev.address,
                )
                try:
                    print("found stick, opening...")
                    stick.open()
                except:
                    print("failed to open stick, trying next")
                    continue
                stick.close()
                break
        else:
            print("No ANT devices available")
        antnode = node.Node(stick)
        print("Starting ANT node")
        antnode.start()

        SPEED_DEVICE_TYPE = 0x7B
        CADENCE_DEVICE_TYPE = 0x7A
        SPEED_CADENCE_DEVICE_TYPE = 0x79
        POWER_DEVICE_TYPE = 0x0B
        CHANNEL_PERIOD = 8182
        POWER_SENSOR_ID = 3862

        print("Starting power meter with ANT+ ID " + repr(POWER_SENSOR_ID))
        net_id = node.Network(constants.NETWORK_KEY_ANT_PLUS, "ZZ:ANT+")
        antnode.setNetworkKey(constants.NETWORK_NUMBER_PUBLIC, net_id)

        p_chan = antnode.getFreeChannel()
        p_chan.assign(net_id, constants.CHANNEL_TYPE_TWOWAY_TRANSMIT)
        p_chan.setID(POWER_DEVICE_TYPE, POWER_SENSOR_ID, 0)
        p_chan.period = 8182
        p_chan.frequency = 57
        p_chan.open()

        c_chan = antnode.getFreeChannel()
        c_chan.assign(net_id, constants.CHANNEL_TYPE_TWOWAY_TRANSMIT)
        c_chan.setID(SPEED_CADENCE_DEVICE_TYPE, POWER_SENSOR_ID, 0)
        c_chan.period = 8102
        c_chan.frequency = 57
        c_chan.open()

        self.p_chan = p_chan
        self.c_chan = c_chan
        self.node = antnode

    def send_p(self, payload):
        ant_msg = message.ChannelBroadcastDataMessage(self.p_chan.number, data=payload)
        self.node.send(ant_msg)

    def send_c(self, payload):
        ant_msg = message.ChannelBroadcastDataMessage(self.c_chan.number, data=payload)
        self.node.send(ant_msg)


class WatchDog:
    def __init__(self, timeout, signal):
        self.timeout = timeout
        self.last_update = time.time()
        self.signal = signal

    def feed(self):
        self.last_update = time.time()

    def run(self):
        while True:
            time.sleep(self.timeout)
            if time.time() - self.last_update > self.timeout:
                self.signal.set()


async def main():
    scan_reqeust = asyncio.Event()
    scan_reqeust.clear()
    kl = KeiserListener(4, scan_reqeust)
    scanner = BleakScanner(kl.callback)

    pd = PowerData()
    ant_tx = AntPlusTx()

    while True:
        scan_reqeust.clear()
        await scanner.start()
        await scan_reqeust.wait()
        pd.update(kl.power, kl.cadence / 10)
        await scanner.stop()

        # https://www.thisisant.com/my-ant/join-adopter/
        payload = bytearray(b"\x10")  # standard power-only message
        payload.append(pd.eventCount & 0xFF)
        payload.append(0xFF)  # Pedal power not used
        payload.append(int(pd.cadence) & 0xFF)  # Cadence
        payload.append(pd.cumulativePower & 0xFF)
        payload.append(pd.cumulativePower >> 8)
        payload.append(pd.instantaneousPower & 0xFF)
        payload.append(pd.instantaneousPower >> 8)
        # ant_msg = message.ChannelBroadcastDataMessage(p_chan.number, data=payload)
        print(
            f"Ver.{kl.version_minor}: {int(kl.power)} W {kl.cadence} RPM\r", end=""
        )
        # if VPOWER_DEBUG: print('Write message to ANT stick on channel ' + repr(self.channel.number))
        ant_tx.send_p(payload)

        # payload = bytearray(b'\x00ffffff')
        # tt = int(time.time() * 1024) & 0xffff
        # payload.append(tt & 0xff)
        # payload.append(tt >> 8)
        # payload.append(pd.cumulativePower & 0xff)
        # payload.append(pd.cumulativePower >> 8)
        # payload.append(pd.instantaneousPower & 0xff)
        # payload.append(pd.instantaneousPower >> 8)


if __name__ == "__main__":
    asyncio.run(main())
