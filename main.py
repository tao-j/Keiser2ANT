import asyncio
from keiser import KeiserBLEListener
import time
import usb
import struct

from ant.core import driver, node, message, constants, resetUSB


def uint8(val):
    return int(val) & 0xFF


def uint16(val):
    return int(val) & 0xFFFF


class BikeDataByIntegration:
    def __init__(self):
        # last feed readings to be sent
        self.power = 0
        self.cadence = 0
        self.speed = 0

        # power events
        self.power_event_counts = 0
        self.cum_power = 0

        # speed
        self.init_time = time.time()
        self.last_feed_time = self.init_time
        self.cum_rev = 0
        self.cum_rev_count = 0
        self.event_time_ms = 0

    def get_event_count(self):
        return uint8(self.power_event_counts)

    def get_cadence(self):
        return uint8(self.cadence)

    def get_power(self):
        return uint16(self.power)

    def get_cum_power(self):
        return uint16(self.cum_power)

    def get_event_time_ms(self):
        return uint16(self.event_time_ms)

    def get_cum_rev_count(self):
        return uint16(self.cum_rev_count)

    def power_to_speed(self, power):
        """
        power in watts
        speed in m/s
        """
        Cd = 0.9
        A = 0.5
        rho = 1.225
        Crr = 0.0045
        F_gravity = 75 * 9.81

        # Define the power equations
        coeff_P_drag = 0.5 * Cd * A * rho  # * v**3
        coeff_P_roll = Crr * F_gravity  # * v

        # P_drag v^3 + P_roll v + (-power) = 0
        p = coeff_P_roll / coeff_P_drag
        q = -power / coeff_P_drag

        delta = p**3 / 27 + q**2 / 4
        cubic_root = lambda x: x ** (1.0 / 3) if x > 0 else -((-x) ** (1.0 / 3))
        u = cubic_root(-q / 2 + delta ** (1.0 / 2))
        v = cubic_root(-q / 2 - delta ** (1.0 / 2))

        return u + v

    def feed(self, power, cadence):
        """
        feed instantaneous power/cadence readings and infer bike speed
        also update the cumulative power and cadence
        """
        speed = self.power_to_speed(power)
        # print(f"speed: {self.speed} m/s")

        now = time.time()
        dt = now - self.last_feed_time
        self.last_feed_time = now

        # speed events
        # set wheel to 700c*25 or ~2096mm
        WHEEL_CIRCUMFERENCE = 2.096
        self.cum_rev += (speed + self.speed) / 2 * dt / WHEEL_CIRCUMFERENCE
        diff = self.cum_rev - self.cum_rev_count
        if diff >= 1:
            self.event_time_ms = now * 1024 - (
                now * 1024 - self.event_time_ms
            ) / diff * (diff - int(diff))
            self.cum_rev_count = int(self.cum_rev)

        # power events
        self.power_event_counts += 1
        self.cum_power += power

        self.cadence = cadence
        self.power = power
        self.speed = speed


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
            exit(1)
        antnode = node.Node(stick)
        print("Starting ANT node")
        antnode.start()

        SPEED_DEVICE_TYPE = 0x7B  # 8118
        # CADENCE_DEVICE_TYPE = 0x7A # 8102
        # SPEED_CADENCE_DEVICE_TYPE = 0x79  # 8086
        # FITNESS_EQUIPMENT_DEVICE_TYPE = 0x11
        POWER_DEVICE_TYPE = 0x0B
        SENSOR_ID = 3862

        print("Starting CSC/CP with ANT+ ID " + repr(SENSOR_ID))
        net_id = node.Network(constants.NETWORK_KEY_ANT_PLUS, "ZZ:ANT+")
        antnode.setNetworkKey(constants.NETWORK_NUMBER_PUBLIC, net_id)

        self.chans = []

        p_chan = antnode.getFreeChannel()
        p_chan.assign(net_id, constants.CHANNEL_TYPE_TWOWAY_TRANSMIT)
        p_chan.setID(POWER_DEVICE_TYPE, SENSOR_ID, 0)
        p_chan.period = 8182
        p_chan.frequency = 57
        p_chan.open()
        self.p_chan = p_chan
        self.chans.append(p_chan)

        c_chan = antnode.getFreeChannel()
        c_chan.assign(net_id, constants.CHANNEL_TYPE_TWOWAY_TRANSMIT)
        c_chan.setID(SPEED_DEVICE_TYPE, SENSOR_ID, 0)
        c_chan.period = 8118
        c_chan.frequency = 57
        c_chan.open()
        self.c_chan = c_chan
        self.chans.append(c_chan)

        # f_chan = antnode.getFreeChannel()
        # f_chan.assign(net_id, constants.CHANNEL_TYPE_TWOWAY_TRANSMIT)
        # f_chan.setID(FITNESS_EQUIPMENT_DEVICE_TYPE, SENSOR_ID, 0)
        # f_chan.period = 8192
        # f_chan.frequency = 57
        # f_chan.open()
        # self.f_chan = f_chan
        # self.chans.append(f_chan)

        self.node = antnode

    def send_msg(self, chan, payload):
        ant_msg = message.ChannelBroadcastDataMessage(chan.number, data=payload)
        self.node.send(ant_msg)

    async def loop(self, kl, pd):
        try:
            while True:
                await kl.new_data.wait()
                # await asyncio.sleep(0.25)
                # kl.power = 11
                # kl.cadence = 222
                pd.feed(kl.power, kl.cadence)
                kl.new_data.clear()
                print(
                    f"Ver.{kl.version_minor}:"
                    f"{int(pd.power):5d} W {int(pd.cadence)} RPM {pd.cum_rev_count} REV "
                    f"{pd.get_event_time_ms()} ms {pd.speed * 3.6 / 1.67:.1f} mph\r",
                    end="\n",
                )

                PWR_PAGE_ID = 0x10
                payload = struct.pack(
                    "<BB" + "BB" + "HH",
                    *[
                        PWR_PAGE_ID,
                        pd.get_event_count(),
                        0xFF,  # Pedal power not used
                        pd.get_cadence(),
                        pd.get_cum_power(),
                        pd.get_power(),
                    ],
                )
                ant_tx.send_msg(ant_tx.p_chan, payload)

                DEFAULT_PAGE_ID = 0x00
                payload = struct.pack(
                    "<B" + "BH" + "HH",
                    DEFAULT_PAGE_ID,
                    0xFF,
                    0xFFFF,
                    pd.get_event_time_ms(),
                    pd.get_cum_rev_count(),
                )
                ant_tx.send_msg(ant_tx.c_chan, payload)

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
                # payload.append(pd.power_event_counts & 0xFF)
                # payload.append(int(pd.cadence) & 0xFF)  # Cadence
                # payload.append(pd.cum_power & 0xFF)
                # payload.append(pd.cum_power >> 8)
                # payload.append(pd.power & 0xFF)
                # payload.append((pd.power >> 8) & 0x0F)
                # payload.append(0x00)  # flags not used
                # ant_tx.send_f(payload)

        except asyncio.CancelledError:
            print("Exiting: cancelled")
            for chan in ant_tx.chans:
                chan.close()
            ant_tx.node.stop()


async def main(ant_tx: AntPlusTx, kl: KeiserBLEListener):
    kl_task = asyncio.create_task(kl.loop())
    at_task = asyncio.create_task(ant_tx.loop(kl, BikeDataByIntegration()))

    await kl_task
    await at_task


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 2:
        bike_id = int(sys.argv[1])
    else:
        bike_id = 1

    ant_tx = AntPlusTx()
    kl = KeiserBLEListener(bike_id=bike_id)

    try:
        asyncio.run(main(ant_tx, kl))
    except KeyboardInterrupt:
        print("Exiting--------------------------------------")
        for chan in ant_tx.chans:
            chan.close()
        ant_tx.node.stop()
