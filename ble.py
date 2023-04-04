import asyncio
from keiser import KeiserBLEListener
import time
import usb


from ant.core import driver, node, message, constants, resetUSB


class PowerData:
    def __init__(self):
        self.eventCount = 0
        self.eventTime = 0
        self.cumulativePower = 0
        self.instantaneousPower = 0
        self.cadence = 0
        self.lastEventTime = time.time()
        self.cumulativeRevs = 0
        self.int_cum_rev = 0
        self.int_time = 0

    def update(self, power, cadence):
        now = time.time()
        dt = now - self.lastEventTime
        # set wheel to 100mm
        # TODO: use power to estimate the rev count
        self.cumulativeRevs += dt * (cadence + self.cadence) / 2.
        self.lastEventTime = now

        self.eventCount = (self.eventCount + 1) & 0xFF
        self.cumulativePower = (self.cumulativePower + int(power)) & 0xFFFF
        self.instantaneousPower = int(power)
        self.cadence = int(cadence) & 0xFF

        self.int_cum_rev = int(self.cumulativeRevs) % 0xFFFF
        self.int_time = int(self.lastEventTime * 1024) % 0xFFFF


class AntPlusTx:
    def __init__(self):
        devs = usb.core.find(find_all=True, idVendor=0x0FCF)
        for dev in devs:
            if dev.idProduct in [0x1008, 0x1009]:
                resetUSB.reset_USB_Device()
                time.sleep(1)
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

        # SPEED_DEVICE_TYPE = 0x7B
        # CADENCE_DEVICE_TYPE = 0x7A
        SPEED_CADENCE_DEVICE_TYPE = 0x79
        FITNESS_EQUIPMENT_DEVICE_TYPE = 0x11
        POWER_DEVICE_TYPE = 0x0B
        SENSOR_ID = 3862

        print("Starting power meter with ANT+ ID " + repr(SENSOR_ID))
        net_id = node.Network(constants.NETWORK_KEY_ANT_PLUS, "ZZ:ANT+")
        antnode.setNetworkKey(constants.NETWORK_NUMBER_PUBLIC, net_id)

        p_chan = antnode.getFreeChannel()
        p_chan.assign(net_id, constants.CHANNEL_TYPE_TWOWAY_TRANSMIT)
        p_chan.setID(POWER_DEVICE_TYPE, SENSOR_ID, 0)
        p_chan.period = 8182
        p_chan.frequency = 57
        p_chan.open()

        c_chan = antnode.getFreeChannel()
        c_chan.assign(net_id, constants.CHANNEL_TYPE_TWOWAY_TRANSMIT)
        c_chan.setID(SPEED_CADENCE_DEVICE_TYPE, SENSOR_ID, 0)
        c_chan.period = 8102
        c_chan.frequency = 57
        c_chan.open()

        # f_chan = antnode.getFreeChannel()
        # f_chan.assign(net_id, constants.CHANNEL_TYPE_TWOWAY_TRANSMIT)
        # f_chan.setID(FITNESS_EQUIPMENT_DEVICE_TYPE, SENSOR_ID, 0)
        # f_chan.period = 8192
        # f_chan.frequency = 57
        # f_chan.open()

        self.p_chan = p_chan
        self.c_chan = c_chan
        # self.f_chan = f_chan
        self.node = antnode

    def send_p(self, payload):
        ant_msg = message.ChannelBroadcastDataMessage(self.p_chan.number, data=payload)
        self.node.send(ant_msg)

    def send_c(self, payload):
        ant_msg = message.ChannelBroadcastDataMessage(self.c_chan.number, data=payload)
        self.node.send(ant_msg)

    def send_f(self, payload):
        ant_msg = message.ChannelBroadcastDataMessage(self.f_chan.number, data=payload)
        self.node.send(ant_msg)

    async def loop(self, kl, pd):
        try:
            i = 0
            while True:
                i = (i + 1) % 4
                await kl.new_data.wait()
                # await asyncio.sleep(0.5)
                pd.update(kl.power, kl.cadence)
                kl.new_data.clear()
                print(
                    f"Ver.{kl.version_minor}: {int(kl.power):5d} W {int(kl.cadence)} RPM {pd.int_cum_rev} REVs {pd.int_time}s /1024 \r",
                    end="",
                )

                # https://www.thisisant.com/my-ant/join-adopter/
                payload = bytearray(b"\x10")  # PWR
                payload.append(pd.eventCount & 0xFF)
                payload.append(0xFF)  # Pedal power not used
                payload.append(int(pd.cadence) & 0xFF)  # Cadence
                payload.append(pd.cumulativePower & 0xFF)
                payload.append(pd.cumulativePower >> 8)
                payload.append(pd.instantaneousPower & 0xFF)
                payload.append(pd.instantaneousPower >> 8)
                ant_tx.send_p(payload)

                if i == 0:
                    payload = bytearray(b"\x05")  # Motion and Speed Page
                else:
                    payload = bytearray(b"\x86")  # Motion and Speed Page
                payload.append(0x00)
                payload.append(0xFF)
                payload.append(0xFF)
                payload.append(pd.int_time & 0xFF)  # Event Time LSB 1/1024
                payload.append(pd.int_time >> 8)  # Event Time MSB
                payload.append(pd.int_cum_rev & 0xFF)  # Rev Count LSB
                payload.append(pd.int_cum_rev >> 8)  # Rev Count MSB
                ant_tx.send_c(payload)

                # payload = bytearray(b"\x11")  # General Settings Page
                # payload.append(0xFF)
                # payload.append(0xFF)  # Cadence
                # payload.append(int(5 / 0.01) & 0xFF)
                # payload.append(0xFF)
                # payload.append(0x7F)
                # payload.append(int(kl.resistence * 2) & 0xFF)
                # payload.append(0x00)  # flags not used
                # ant_tx.send_f(payload)

                # payload = bytearray(b"\x19")  # FE power
                # payload.append(pd.eventCount & 0xFF)
                # payload.append(int(pd.cadence) & 0xFF)  # Cadence
                # payload.append(pd.cumulativePower & 0xFF)
                # payload.append(pd.cumulativePower >> 8)
                # payload.append(pd.instantaneousPower & 0xFF)
                # payload.append((pd.instantaneousPower >> 8) & 0x0F)
                # payload.append(0x00)  # flags not used
                # ant_tx.send_f(payload)

        except asyncio.CancelledError:
            print("Exitingdfasdafasdf")
            ant_tx.p_chan.close()
            ant_tx.c_chan.close()
            # ant_tx.f_chan.close()
            ant_tx.node.stop()


async def main(ant_tx: AntPlusTx, kl: KeiserBLEListener):
    kl_task = asyncio.create_task(kl.loop())
    at_task = asyncio.create_task(ant_tx.loop(kl, PowerData()))

    await kl_task
    await at_task


if __name__ == "__main__":
    ant_tx = AntPlusTx()
    kl = KeiserBLEListener(bike_id=4)

    try:
        asyncio.run(main(ant_tx, kl))
    except KeyboardInterrupt:
        print("Exiting--------------------------------------")
        # ant_tx.c_chan.close()
        # ant_tx.p_chan.close()
        # ant_tx.node.stop()
